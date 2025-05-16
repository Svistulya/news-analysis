import requests
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from textblob import TextBlob
from collections import defaultdict

class RedditParser:
    def __init__(self):
        self.base_url = "https://www.reddit.com"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def _parse_timestamp(self, timestamp_str):
        try:
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.rstrip('Z')).isoformat()
            if timestamp_str.isdigit():
                return datetime.fromtimestamp(int(timestamp_str)/1000, timezone.utc).isoformat()
            return ''
        except Exception as e:
            print(f"Ошибка времени {timestamp_str}: {e}")
            return ''

    def _get_post_images(self, post_url):
        try:
            response = self.session.get(post_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            images = []
            img_tags = soup.find_all('img', {
                'class': 'i18n-post-media-img preview-img media-lightbox-img max-h-[100vw] h-full w-full object-contain relative'
            })
            
            for img in img_tags:
                src = img.get('src')
                if src and src.startswith('https://'):
                    images.append(src)
            
            return images if images else []
        except Exception as e:
            print(f"Ошибка полкчения изображения: {e}")
            return []

    def _analyze_sentiment(self, text):
        analysis = TextBlob(text)
        polarity = analysis.sentiment.polarity
        subjectivity = analysis.sentiment.subjectivity
        
        if polarity > 0.1:
            sentiment = "positive"
        elif polarity < -0.1:
            sentiment = "negative"
        else:
            sentiment = "neutral"
            
        return {
            'polarity': polarity,
            'subjectivity': subjectivity,
            'sentiment': sentiment
        }

    def get_analyzed_posts(self, subreddits=None, limit=10):
        if subreddits is None:
            subreddits = ['pics', 'aww', 'nature', 'technology']
            
        all_posts = []
        sentiment_counts = defaultdict(int)
        
        for subreddit in subreddits:
            try:
                url = f"{self.base_url}/r/{subreddit}/top/?t=day"
                response = self.session.get(url, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                posts = soup.find_all('shreddit-post')[:limit]
                
                for post in posts:
                    timestamp_str = post.get('created-timestamp', '')
                    post_url = f"{self.base_url}{post.get('permalink', '')}"
                    
                    post_data = {
                        'title': post.get('post-title', ''),
                        'url': self._fix_url(post.get('content-href', '')),
                        'score': self._parse_number(post.get('score', '0')),
                        'num_comments': self._parse_number(post.get('comment-count', '0')),
                        'created_utc': self._parse_timestamp(timestamp_str),
                        'author': post.get('author', ''),
                        'permalink': post_url,
                        'subreddit': subreddit,
                        'images': self._get_post_images(post_url)
                    }
                    
                    
                    analysis = self._analyze_sentiment(post_data['title'])
                    post_data['analysis'] = analysis
                    sentiment_counts[analysis['sentiment']] += 1
                    
                    all_posts.append(post_data)
                
            except Exception as e:
                print(f"Ошибка {subreddit}: {e}")
        
        return {
            'posts_analyzed': len(all_posts),
            'sentiment_distribution': dict(sentiment_counts),
            'detailed_results': all_posts
        }

    def _fix_url(self, url):
        if url.startswith('/'):
            return f"{self.base_url}{url}"
        return url

    def _parse_number(self, num_str):
        try:
            return int(num_str.replace(',', ''))
        except:
            return 0    
