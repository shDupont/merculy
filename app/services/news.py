"""
Merculy Backend - News Curation Service
"""
import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from flask import current_app
from ..models.user import Article
from ..core.config import Config
import json

class NewsService:
    def __init__(self):
        self.config = Config()

    def fetch_news_api(self, topics: List[str], days_back: int = 1) -> List[Dict]:
        """Fetch news from NewsAPI"""
        try:
            url = "https://newsapi.org/v2/everything"

            # Convert topics to query string
            query = " OR ".join(topics)

            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

            params = {
                'q': query,
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'pt',
                'pageSize': 50,
                'apiKey': self.config.NEWSAPI_KEY
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            articles = []

            for article in data.get('articles', []):
                if article.get('title') and article.get('url'):
                    articles.append({
                        'title': article['title'],
                        'url': article['url'],
                        'excerpt': article.get('description', ''),
                        'content': article.get('content', ''),
                        'source': article.get('source', {}).get('name', 'Unknown'),
                        'published_at': article.get('publishedAt'),
                        'topic': self._categorize_article(article['title'], topics)
                    })

            return articles

        except Exception as e:
            current_app.logger.error(f"NewsAPI error: {str(e)}")
            return []

    def fetch_guardian_api(self, topics: List[str], days_back: int = 1) -> List[Dict]:
        """Fetch news from The Guardian API"""
        try:
            url = "https://content.guardianapis.com/search"

            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

            params = {
                'q': " OR ".join(topics),
                'from-date': from_date,
                'show-fields': 'headline,standfirst,body',
                'page-size': 50,
                'api-key': self.config.GUARDIAN_API_KEY
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            data = response.json()
            articles = []

            for article in data.get('response', {}).get('results', []):
                fields = article.get('fields', {})
                articles.append({
                    'title': fields.get('headline', article.get('webTitle', '')),
                    'url': article.get('webUrl', ''),
                    'excerpt': fields.get('standfirst', ''),
                    'content': fields.get('body', ''),
                    'source': 'The Guardian',
                    'published_at': article.get('webPublicationDate'),
                    'topic': self._categorize_article(article.get('webTitle', ''), topics)
                })

            return articles

        except Exception as e:
            current_app.logger.error(f"Guardian API error: {str(e)}")
            return []

    def fetch_bing_news(self, topics: List[str], days_back: int = 1) -> List[Dict]:
        """Fetch news from Bing News API"""
        try:
            url = "https://api.bing.microsoft.com/v7.0/news/search"

            query = " OR ".join(topics)

            headers = {
                'Ocp-Apim-Subscription-Key': self.config.BING_NEWS_KEY
            }

            params = {
                'q': query,
                'mkt': 'pt-BR',
                'count': 50,
                'freshness': 'Day' if days_back <= 1 else 'Week'
            }

            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()

            data = response.json()
            articles = []

            for article in data.get('value', []):
                articles.append({
                    'title': article.get('name', ''),
                    'url': article.get('url', ''),
                    'excerpt': article.get('description', ''),
                    'content': article.get('description', ''),
                    'source': article.get('provider', [{}])[0].get('name', 'Unknown'),
                    'published_at': article.get('datePublished'),
                    'topic': self._categorize_article(article.get('name', ''), topics)
                })

            return articles

        except Exception as e:
            current_app.logger.error(f"Bing News API error: {str(e)}")
            return []

    def _categorize_article(self, title: str, topics: List[str]) -> str:
        """Simple categorization based on title keywords"""
        title_lower = title.lower()

        for topic in topics:
            if topic.lower() in title_lower:
                return topic

        # Default categorization
        if any(word in title_lower for word in ['política', 'governo', 'eleição']):
            return 'Política'
        elif any(word in title_lower for word in ['economia', 'mercado', 'dinheiro']):
            return 'Economia'
        elif any(word in title_lower for word in ['tecnologia', 'ia', 'artificial', 'tech']):
            return 'Tecnologia'
        elif any(word in title_lower for word in ['esporte', 'futebol', 'copa']):
            return 'Esportes'
        else:
            return 'Geral'

    def deduplicate_articles(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles based on URL"""
        seen_urls = set()
        unique_articles = []

        for article in articles:
            if article['url'] not in seen_urls:
                seen_urls.add(article['url'])
                unique_articles.append(article)

        return unique_articles

    def fetch_curated_news(self, user_topics: List[str], days_back: int = 1) -> List[Article]:
        """Fetch and curate news from all sources"""
        all_articles = []

        # Fetch from all APIs
        all_articles.extend(self.fetch_news_api(user_topics, days_back))
        all_articles.extend(self.fetch_guardian_api(user_topics, days_back))
        all_articles.extend(self.fetch_bing_news(user_topics, days_back))

        # Deduplicate
        unique_articles = self.deduplicate_articles(all_articles)

        # Convert to Article objects
        articles = []
        for article_data in unique_articles:
            try:
                # Parse date
                published_at = datetime.fromisoformat(
                    article_data['published_at'].replace('Z', '+00:00')
                )

                article = Article(
                    title=article_data['title'],
                    url=article_data['url'],
                    excerpt=article_data['excerpt'],
                    content=article_data.get('content', ''),
                    source=article_data['source'],
                    published_at=published_at,
                    topic=article_data['topic']
                )
                articles.append(article)

            except Exception as e:
                current_app.logger.warning(f"Error parsing article: {str(e)}")
                continue

        # Sort by published date (most recent first)
        articles.sort(key=lambda x: x.published_at, reverse=True)

        return articles[:20]  # Limit to top 20 articles

# Global service instance
news_service = NewsService()
