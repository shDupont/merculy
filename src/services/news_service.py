import requests
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import json
from src.config import Config
from src.services.cosmos_service import cosmos_service

class NewsService:
    def __init__(self):
        self.news_api_key = Config.NEWS_API_KEY
        self.news_api_url = Config.NEWS_API_URL
        
        # Topic mapping for Portuguese keywords - will be enhanced by Cosmos DB data
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
            'meio ambiente': ['meio ambiente', 'sustentabilidade', 'clima', 'aquecimento global', 'poluição', 'natureza'],
            'meio-ambiente': ['meio ambiente', 'sustentabilidade', 'clima', 'aquecimento global', 'poluição', 'natureza'],
            'arte-cultura': ['arte', 'cultura', 'música', 'teatro', 'cinema', 'literatura', 'exposição', 'festival'],
            'mercado-trabalho': ['emprego', 'trabalho', 'carreira', 'vaga', 'concurso', 'desemprego', 'RH', 'profissional']
        }
    
    def is_available(self):
        """Check if News API is available"""
        return self.news_api_key is not None
    
    def get_brazilian_sources_domains(self):
        """Get Brazilian news sources domains from Cosmos DB"""
        channels = cosmos_service.get_available_channels()
        if channels:
            return [channel['domain'] for channel in channels if channel.get('country') == 'br']
        
        # Fallback to hardcoded sources if Cosmos DB is not available
        return [
            'globo.com',
            'folha.uol.com.br',
            'estadao.com.br',
            'g1.globo.com',
            'uol.com.br',
            'veja.abril.com.br',
            'exame.com',
            'valor.com.br',
            'bbc.com/portuguese',
            'cnnbrasil.com.br'
        ]
    
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
    
    def get_news_by_topic(self, topic: str, limit: int = 20, user_channels: List[str] = None) -> List[Dict]:
        """
        Get news articles by topic with user-specific channel filtering
        
        Args:
            topic: The topic to search for
            limit: Maximum number of articles to return
            user_channels: List of channel domains that user follows (optional)
            
        Returns:
            List of news articles
        """
        keywords = self.topic_keywords.get(topic.lower(), [topic])
        query = ' OR '.join(keywords)
        
        # Use user's followed channels if provided, otherwise use all Brazilian sources
        print(user_channels)
        if user_channels and len(user_channels) > 0:
            selected_sources = user_channels
        else:
            selected_sources = self.get_brazilian_sources_domains()
        
        # Calculate news distribution across sources
        news_per_source = max(1, limit // len(selected_sources))
        remainder = limit % len(selected_sources)
        
        all_articles = []
        
        for i, source_domain in enumerate(selected_sources):
            # Calculate limit for this source (distribute remainder among first sources)
            source_limit = news_per_source + (1 if i < remainder else 0)
            
            params = {
                'q': query,
                'domains': source_domain,
                'pageSize': min(source_limit, 100),
                'from': (datetime.now() - timedelta(days=7)).isoformat()  # Last 7 days
            }
            
            result = self._make_news_api_request(params)
            
            if result and 'articles' in result:
                source_articles = []
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
                        source_articles.append(processed_article)
                        
                        if len(source_articles) >= source_limit:
                            break
                
                all_articles.extend(source_articles)
        
        # Return up to the requested limit
        return all_articles[:limit]

    def get_news_by_multiple_topics(self, topics: List[str], limit: int = 20, user_channels: List[str] = None) -> Dict[str, List[Dict]]:
        """
        Get news articles by multiple topics with equal distribution
        
        Args:
            topics: List of topics to search for
            limit: Total maximum number of articles to return across all topics
            user_channels: List of channel domains that user follows (optional)
            
        Returns:
            Dictionary with topic as key and list of articles as value
        """
        print(f"[MULTIPLE_TOPICS] Starting with topics: {topics}, limit: {limit}, user_channels: {user_channels}")
        
        if not topics:
            print("[MULTIPLE_TOPICS] No topics provided - returning empty dict")
            return {}
        
        # Simple equal division: divide total limit by number of topics
        articles_per_topic = limit // len(topics)
        print(f"[MULTIPLE_TOPICS] Articles per topic: {articles_per_topic}")
        
        news_by_topic = {}
        
        # Get articles for each topic with equal distribution
        for i, topic in enumerate(topics):
            # Calculate limit for this topic (distribute remainder to first topics)
            topic_limit = articles_per_topic

            print(f"[MULTIPLE_TOPICS] Processing topic '{topic}' with limit: {topic_limit}")
            
            # Get articles for this topic
            topic_articles = self.get_news_by_topic(
                topic=topic,
                limit=topic_limit,
                user_channels=user_channels
            )
            
            print(f"[MULTIPLE_TOPICS] Topic '{topic}' returned {len(topic_articles) if topic_articles else 0} articles")
            
            if topic_articles:
                news_by_topic[topic] = topic_articles
            else:
                print(f"[MULTIPLE_TOPICS] No articles found for topic '{topic}'")
        
        print(f"[MULTIPLE_TOPICS] Final result: {len(news_by_topic)} topics with articles")
        return news_by_topic
    
    def get_news_by_interests(self, user, limit: int = 20) -> Dict[str, List[Dict]]:
        """
        Get news articles based on current user's interests using multiple topics approach
        
        Args:
            user: Current user object with interests and followed_channels
            limit: Total maximum number of articles to return across all interests
            
        Returns:
            Dictionary with topic as key and list of articles as value
        """
        # Get user's interests
        user_interests = user.get_interests()

        print(f"[INTERESTS] User interests: {user_interests}")
        print(f"[INTERESTS] User type: {type(user)}")
        print(f"[INTERESTS] User ID: {getattr(user, 'id', 'unknown')}")
        
        if not user_interests:
            print("[INTERESTS] No user interests found - returning empty dict")
            # Return empty if user has no interests
            return {}
        
        # Get user's followed channels
        user_channels = None
        if hasattr(user, 'get_followed_channels'):
            user_channels = user.get_followed_channels()
            print(f"[INTERESTS] User channels: {user_channels}")
        else:
            print("[INTERESTS] User has no get_followed_channels method")
        
        print(f"[INTERESTS] Calling get_news_by_multiple_topics with: topics={user_interests}, limit={limit}, user_channels={user_channels}")
        
        # Use the multiple topics method for better distribution
        result = self.get_news_by_multiple_topics(
            topics=user_interests,
            limit=limit,
            user_channels=user_channels
        )
        
        print(f"[INTERESTS] get_news_by_multiple_topics returned: {type(result)}")
        print(f"[INTERESTS] Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        if isinstance(result, dict):
            for topic, articles in result.items():
                print(f"[INTERESTS] Topic '{topic}': {len(articles)} articles")
        
        return result
    
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
        brazilian_sources = self.get_brazilian_sources_domains()
        
        params = {
            'q': query,
            'domains': ','.join(brazilian_sources),
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
        """Get list of available Brazilian news sources from Cosmos DB"""
        channels = cosmos_service.get_available_channels()
        if channels:
            sources = []
            for channel in channels:
                if channel.get('isActive', True):
                    sources.append({
                        'id': channel.get('id'),
                        'name': channel.get('name'),
                        'domain': channel.get('domain'),
                        'category': channel.get('category'),
                        'language': channel.get('language', 'pt-br'),
                        'country': channel.get('country', 'br')
                    })
            return sources
        
        # Fallback to hardcoded sources if Cosmos DB is not available
        brazilian_sources = self.get_brazilian_sources_domains()
        sources = []
        for domain in brazilian_sources:
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

