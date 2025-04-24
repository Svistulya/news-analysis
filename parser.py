import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone

class RedditScraper:
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
            print(f"Timestamp error {timestamp_str}: {e}")
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
            
            return images if images else None
        except Exception as e:
            print(f"Image parsing error: {e}")
            return None

    def get_news_from_subreddit(self, subreddit, limit=10):
        try:
            url = f"{self.base_url}/r/{subreddit}/top/?t=day"
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            posts = soup.find_all('shreddit-post')[:limit]
            
            news_items = []
            for post in posts:
                timestamp_str = post.get('created-timestamp', '')
                post_url = f"{self.base_url}{post.get('permalink', '')}"
                
                news_item = {
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
                news_items.append(news_item)
            
            return news_items
        
        except Exception as e:
            print(f"Error parsing {subreddit}: {e}")
            return []

    def _fix_url(self, url):
        if url.startswith('/'):
            return f"{self.base_url}{url}"
        return url

    def _parse_number(self, num_str):
        try:
            return int(num_str.replace(',', ''))
        except:
            return 0

    def save_to_json(self, data, filename):
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"Saved to {filename}")
        except Exception as e:
            print(f"Save error: {e}")

if __name__ == "__main__":
    scraper = RedditScraper()
    subreddits = ['pics', 'aww', 'nature', 'technology']
    all_news = []
    
    for subreddit in subreddits:
        print(f"Scraping r/{subreddit}...")
        news = scraper.get_news_from_subreddit(subreddit)
        all_news.extend(news)
    
    scraper.save_to_json(all_news, "reddit_posts_with_images.json")
    
    for i, news_item in enumerate(all_news[:5], 1):
        print(f"\nPost #{i}:")
        print(f"Title: {news_item['title']}")
        print(f"Subreddit: r/{news_item['subreddit']}")
        if news_item['images']:
            print(f"Images found: {len(news_item['images'])}")
            print("Sample image URLs:")
            for img in news_item['images'][:2]:
                print(f"  - {img}")
