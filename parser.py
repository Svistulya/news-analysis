import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import re

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
            print(f"Ошибка с форматом времени {timestamp_str}: {e}")
            return ''

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
                created_utc = self._parse_timestamp(timestamp_str)
                
                news_item = {
                    'title': post.get('post-title', ''),
                    'url': self._fix_url(post.get('content-href', '')),
                    'score': self._parse_number(post.get('score', '0')),
                    'num_comments': self._parse_number(post.get('comment-count', '0')),
                    'created_utc': created_utc,
                    'author': post.get('author', ''),
                    'permalink': f"{self.base_url}{post.get('permalink', '')}",
                    'subreddit': subreddit
                }
                news_items.append(news_item)
            
            return news_items
        
        except Exception as e:
            print(f"Ошибка в {subreddit}: {e}")
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
            print(f"Сохранено в  {filename}")
        except Exception as e:
            print(f"Ошибка сохранения {e}")

if __name__ == "__main__":
    scraper = RedditScraper()
    subreddits = ['news', 'worldnews', 'technology']
    all_news = []
    
    for subreddit in subreddits:
        print(f"Scraping r/{subreddit}...")
        news = scraper.get_news_from_subreddit(subreddit)
        all_news.extend(news)
    
    scraper.save_to_json(all_news, "reddit_news_scraped.json")
    
    for i, news_item in enumerate(all_news, 1):
        print(f"\nNews #{i}:")
        print(f"Title: {news_item['title']}")
        print(f"URL: {news_item['url']}")
        print(f"Score: {news_item['score']} points")
        print(f"Comments: {news_item['num_comments']}")
        print(f"Posted: {news_item['created_utc']}")