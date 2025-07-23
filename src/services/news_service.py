import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from src.config import Config

class NewsService:
    def __init__(self):
        self.news_api_key = Config.NEWS_API_KEY
        self.news_api_url = Config.NEWS_API_URL
        
        # Brazilian news sources
        self.brazilian_sources = [
            'globo.com',
            'folha.uol.com.br',
            'estadao.com.br',
            'g1.globo.com',
            'uol.com.br',
            'veja.abril.com.br',
            'exame.com',
            'valor.com.br',
            'bbc.com/portuguese',
            'cnn.com.br'
        ]
        
        # Topic mapping for Portuguese keywords
        self.topic_keywords = {
            'tecnologia': ['tecnologia', 'tech', 'inovação', 'startup', 'digital', 'internet', 'software', 'hardware'],
            'política': ['política', 'governo', 'eleições', 'congresso', 'senado', 'deputado', 'presidente'],
            'economia': ['economia', 'mercado', 'bolsa', 'dólar', 'inflação', 'PIB', 'juros', 'banco'],
            'esportes': ['futebol', 'esporte', 'copa', 'olimpíadas', 'jogos', 'atleta', 'campeonato'],
            'saúde': ['saúde', 'medicina', 'hospital', 'doença', 'vacina', 'tratamento', 'médico'],
            'ciência': ['ciência', 'pesquisa', 'estudo', 'descoberta', 'universidade', 'científico'],
            'entretenimento': ['cinema', 'música', 'teatro', 'celebridade', 'filme', 'show', 'artista'],
            'negócios': ['negócios', 'empresa', 'corporação', 'CEO', 'investimento', 'lucro', 'receita'],
            'educação': ['educação', 'escola', 'universidade', 'ensino', 'professor', 'estudante', 'MEC'],
            'meio ambiente': ['meio ambiente', 'sustentabilidade', 'clima', 'aquecimento global', 'poluição', 'natureza']
        }
    
    def is_available(self):
        """Check if News API is available"""
        return self.news_api_key is not None
    
    def _make_news_api_request(self, params: Dict) -> Optional[Dict]:
        """Make request to News API"""
        if not self.is_available():
            return None
        
        try:
            params['apiKey'] = self.news_api_key
            params['language'] = 'pt'  # Portuguese
            params['sortBy'] = 'publishedAt'
            
            response = requests.get(self.news_api_url, params=params, timeout=30)
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"News API error: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error calling News API: {e}")
            return None
    
    def get_news_by_topic(self, topic: str, limit: int = 20) -> List[Dict]:
        """Get news articles by topic"""
        keywords = self.topic_keywords.get(topic.lower(), [topic])
        query = ' OR '.join(keywords)
        
        params = {
            'q': query,
            'domains': ','.join(self.brazilian_sources),
            'pageSize': min(limit, 100),
            'from': (datetime.now() - timedelta(days=7)).isoformat()  # Last 7 days
        }
        
        result = self._make_news_api_request(params)
        
        if result and 'articles' in result:
            articles = []
            for article in result['articles']:
                if article.get('title') and article.get('description'):
                    processed_article = {
                        'title': article['title'],
                        'content': article.get('description', '') + ' ' + article.get('content', ''),
                        'summary': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'url': article.get('url', ''),
                        'topic': topic,
                        'published_at': article.get('publishedAt', datetime.now().isoformat()),
                        'image_url': article.get('urlToImage')
                    }
                    articles.append(processed_article)
            
            return articles[:limit]
        
        return []
    
    def get_news_by_interests(self, interests: List[str], limit_per_topic: int = 10) -> Dict[str, List[Dict]]:
        """Get news articles based on user interests"""
        news_by_topic = {}
        
        for interest in interests:
            articles = self.get_news_by_topic(interest, limit_per_topic)
            if articles:
                news_by_topic[interest] = articles
        
        return news_by_topic
    
    def get_trending_news(self, limit: int = 20) -> List[Dict]:
        """Get trending news from Brazil"""
        params = {
            'country': 'br',
            'pageSize': min(limit, 100)
        }
        
        # Use top headlines endpoint for trending news
        trending_url = 'https://newsapi.org/v2/top-headlines'
        
        try:
            params['apiKey'] = self.news_api_key
            response = requests.get(trending_url, params=params, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                if 'articles' in result:
                    articles = []
                    for article in result['articles']:
                        if article.get('title') and article.get('description'):
                            processed_article = {
                                'title': article['title'],
                                'content': article.get('description', '') + ' ' + article.get('content', ''),
                                'summary': article.get('description', ''),
                                'source': article.get('source', {}).get('name', 'Unknown'),
                                'url': article.get('url', ''),
                                'topic': 'trending',
                                'published_at': article.get('publishedAt', datetime.now().isoformat()),
                                'image_url': article.get('urlToImage')
                            }
                            articles.append(processed_article)
                    
                    return articles[:limit]
            
        except Exception as e:
            print(f"Error getting trending news: {e}")
        
        return []
    
    def search_news(self, query: str, limit: int = 20) -> List[Dict]:
        """Search for news articles with a specific query"""
        params = {
            'q': query,
            'domains': ','.join(self.brazilian_sources),
            'pageSize': min(limit, 100),
            'from': (datetime.now() - timedelta(days=30)).isoformat()  # Last 30 days
        }
        
        result = self._make_news_api_request(params)
        
        if result and 'articles' in result:
            articles = []
            for article in result['articles']:
                if article.get('title') and article.get('description'):
                    processed_article = {
                        'title': article['title'],
                        'content': article.get('description', '') + ' ' + article.get('content', ''),
                        'summary': article.get('description', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'url': article.get('url', ''),
                        'topic': 'search',
                        'published_at': article.get('publishedAt', datetime.now().isoformat()),
                        'image_url': article.get('urlToImage')
                    }
                    articles.append(processed_article)
            
            return articles[:limit]
        
        return []
    
    def get_news_by_source(self, source: str, limit: int = 20) -> List[Dict]:
        """Get news articles from a specific source"""
        params = {
            'domains': source,
            'pageSize': min(limit, 100),
            'from': (datetime.now() - timedelta(days=7)).isoformat()
        }
        
        result = self._make_news_api_request(params)
        
        if result and 'articles' in result:
            articles = []
            for article in result['articles']:
                if article.get('title') and article.get('description'):
                    processed_article = {
                        'title': article['title'],
                        'content': article.get('description', '') + ' ' + article.get('content', ''),
                        'summary': article.get('description', ''),
                        'source': article.get('source', {}).get('name', source),
                        'url': article.get('url', ''),
                        'topic': 'source',
                        'published_at': article.get('publishedAt', datetime.now().isoformat()),
                        'image_url': article.get('urlToImage')
                    }
                    articles.append(processed_article)
            
            return articles[:limit]
        
        return []
    
    def get_available_sources(self) -> List[Dict]:
        """Get list of available Brazilian news sources"""
        sources = []
        for domain in self.brazilian_sources:
            sources.append({
                'domain': domain,
                'name': domain.replace('.com.br', '').replace('.com', '').replace('www.', '').title(),
                'country': 'br',
                'language': 'pt'
            })
        
        return sources
    
    def categorize_article(self, title: str, content: str) -> str:
        """Categorize an article based on its content"""
        title_content = (title + ' ' + content).lower()
        
        topic_scores = {}
        for topic, keywords in self.topic_keywords.items():
            score = sum(1 for keyword in keywords if keyword.lower() in title_content)
            if score > 0:
                topic_scores[topic] = score
        
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        
        return 'geral'  # Default category

# Global instance
news_service = NewsService()

