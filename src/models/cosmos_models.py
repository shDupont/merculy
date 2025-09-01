"""
Cosmos DB based models for the Merculy application.
Replaces SQLAlchemy models with Cosmos DB compatible classes.
"""
from datetime import datetime
from src.services.cosmos_service import CosmosService


class CosmosNewsletter:
    """Newsletter model for Cosmos DB - Article Reference Collection"""
    
    def __init__(self, newsletter_data=None):
        if newsletter_data:
            self.id = newsletter_data.get('id')
            self.user_id = newsletter_data.get('user_id')
            self.title = newsletter_data.get('title')
            self.topic = newsletter_data.get('topic')
            self.created_at = newsletter_data.get('created_at')
            self.articles = newsletter_data.get('articles', [])  # List of article IDs
        else:
            self.id = None
            self.user_id = None
            self.title = None
            self.topic = None
            self.created_at = None
            self.articles = []
    
    def to_dict(self):
        """Convert newsletter to dictionary for API responses"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'topic': self.topic,
            'created_at': self.created_at,
            'articles': self.articles,
            'article_count': len(self.articles) if self.articles else 0
        }
    
    def to_cosmos_dict(self):
        """Convert newsletter to dictionary for Cosmos DB storage"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'topic': self.topic,
            'created_at': self.created_at,
            'articles': self.articles,
            'type': 'newsletter'
        }


class CosmosNewsArticle:
    """News Article model for Cosmos DB"""
    
    def __init__(self, article_data=None):
        if article_data:
            self.id = article_data.get('id')
            self.title = article_data.get('title')
            self.content = article_data.get('content')
            self.summary = article_data.get('summary')
            self.bullet_point_highlights = article_data.get('bullet_point_highlights')
            self.source = article_data.get('source')
            self.url = article_data.get('url')
            self.topic = article_data.get('topic')
            self.image_url = article_data.get('image_url')
            self.political_bias = article_data.get('political_bias')
            self.published_at = article_data.get('published_at')
            self.created_at = article_data.get('created_at')
        else:
            self.id = None
            self.title = None
            self.content = None
            self.summary = None
            self.bullet_point_highlights = None
            self.source = None
            self.url = None
            self.topic = None
            self.image_url = None
            self.political_bias = None
            self.published_at = None
            self.created_at = None
    
    def to_dict(self):
        """Convert news article to dictionary for API responses"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'bullet_point_highlights': self.bullet_point_highlights,
            'source': self.source,
            'url': self.url,
            'topic': self.topic,
            'image_url': self.image_url,
            'political_bias': self.political_bias,
            'published_at': self.published_at,
            'created_at': self.created_at
        }
    
    def to_cosmos_dict(self):
        """Convert news article to dictionary for Cosmos DB storage"""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'bullet_point_highlights': self.bullet_point_highlights,
            'source': self.source,
            'url': self.url,
            'topic': self.topic,
            'image_url': self.image_url,
            'political_bias': self.political_bias,
            'published_at': self.published_at,
            'created_at': self.created_at,
            'type': 'news_article'
        }


class NewsletterService:
    """Service class for managing newsletters in Cosmos DB"""
    
    def __init__(self):
        self.cosmos_service = CosmosService()
    
    def create_newsletter(self, user_id, title, topic, articles):
        """Create a new newsletter with article references"""
        try:
            newsletter_data = {
                'user_id': str(user_id),
                'title': title,
                'topic': topic,
                'articles': articles,  # List of article IDs
                'created_at': datetime.utcnow().isoformat()
            }
            
            cosmos_newsletter = self.cosmos_service.create_newsletter(newsletter_data)
            if cosmos_newsletter:
                return CosmosNewsletter(cosmos_newsletter)
            return None
            
        except Exception as e:
            print(f"Error creating newsletter: {e}")
            return None
    
    def get_user_newsletters(self, user_id, limit=50):
        """Get newsletters for a user"""
        try:
            cosmos_newsletters = self.cosmos_service.get_user_newsletters(str(user_id), limit)
            return [CosmosNewsletter(newsletter) for newsletter in cosmos_newsletters]
        except Exception as e:
            print(f"Error getting user newsletters: {e}")
            return []
    
    def get_newsletter_with_articles(self, newsletter_id, user_id):
        """Get newsletter with populated article data"""
        try:
            # Get the newsletter
            newsletter = self.cosmos_service.get_newsletter_by_id(newsletter_id, str(user_id))
            if not newsletter:
                return None
            
            newsletter_obj = CosmosNewsletter(newsletter)
            
            # Get the articles data
            articles_data = []
            for article_id in newsletter_obj.articles:
                article = self.cosmos_service.get_news_article_by_id(article_id)
                if article:
                    articles_data.append(CosmosNewsArticle(article))
            
            # Return newsletter with articles data
            return {
                'newsletter': newsletter_obj,
                'articles': articles_data
            }
            
        except Exception as e:
            print(f"Error getting newsletter with articles: {e}")
            return None
    
    def delete_newsletter(self, newsletter_id, user_id):
        """Delete a newsletter"""
        try:
            result = self.cosmos_service.delete_newsletter(newsletter_id, str(user_id))
            return result is not None
        except Exception as e:
            print(f"Error deleting newsletter: {e}")
            return False


class NewsArticleService:
    """Service class for managing news articles in Cosmos DB"""
    
    def __init__(self):
        self.cosmos_service = CosmosService()
    
    def create_article(self, title, content, source, url, topic, image_url=None,
                      summary=None, bullet_point_highlights=None, political_bias=None, published_at=None):
        """Create a new news article"""
        try:
            article_data = {
                'title': title,
                'content': content,
                'summary': summary,
                'bullet_point_highlights': bullet_point_highlights,
                'source': source,
                'url': url,
                'topic': topic,
                'image_url': image_url,
                'political_bias': political_bias,
                'published_at': published_at or datetime.utcnow().isoformat(),
                'created_at': datetime.utcnow().isoformat()
            }
            
            cosmos_article = self.cosmos_service.create_news_article(article_data)
            if cosmos_article:
                return CosmosNewsArticle(cosmos_article)
            return None
            
        except Exception as e:
            print(f"Error creating news article: {e}")
            return None
    
    def get_articles_by_topic(self, topic, limit=20):
        """Get news articles by topic"""
        try:
            cosmos_articles = self.cosmos_service.get_news_articles_by_topic(topic, limit)
            return [CosmosNewsArticle(article) for article in cosmos_articles]
        except Exception as e:
            print(f"Error getting articles by topic: {e}")
            return []


# Global instances
newsletter_service = NewsletterService()
news_article_service = NewsArticleService()
