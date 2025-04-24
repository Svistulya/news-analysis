from textblob import TextBlob
import json
from collections import defaultdict

class RedditTitleAnalyzer:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path
        self.posts = self._load_posts()
        
    def _load_posts(self):
        try:
            with open(self.json_file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Ошибка загрузки файла: {e}")
            return []
    
    def analyze_sentiment(self, text):
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
    
    def analyze_titles(self):
        if not self.posts:
            print("Нет данных для анализа")
            return None
            
        results = []
        sentiment_counts = defaultdict(int)
        
        for post in self.posts:
            title = post.get('title', '')
            if not title:
                continue
                
            analysis = self.analyze_sentiment(title)
            results.append({
                'title': title,
                'analysis': analysis,
                'images': post.get('images', []),  
                'url': post.get('url', ''),
                'permalink': post.get('permalink', ''),
                'subreddit': post.get('subreddit', '')
            })
            sentiment_counts[analysis['sentiment']] += 1
            
        return {
            'posts_analyzed': len(results),
            'sentiment_distribution': dict(sentiment_counts),
            'detailed_results': results
        }
    
if __name__ == "__main__":
    analyzer = RedditTitleAnalyzer("reddit_posts_with_images.json")
    
    print("Анализируем...")
    results = analyzer.analyze_titles()
    
    if results:
        
        
        with open("reddit_sentiment_analysis_with_images.json", "w", encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print("\nРезультаты сохранены")
