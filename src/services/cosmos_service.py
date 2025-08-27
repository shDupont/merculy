from azure.cosmos import CosmosClient, PartitionKey, exceptions
import json
from datetime import datetime
from src.config import Config

class CosmosService:
    def __init__(self):
        self.client = None
        self.database = None
        self.container = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Cosmos DB client and containers"""
        try:
            if not Config.COSMOS_ENDPOINT or not Config.COSMOS_KEY:
                print("Warning: Cosmos DB credentials not configured. Using SQLite fallback.")
                return
            
            self.client = CosmosClient(Config.COSMOS_ENDPOINT, Config.COSMOS_KEY)
            
            # Create database if it doesn't exist
            try:
                self.database = self.client.create_database_if_not_exists(
                    id=Config.COSMOS_DATABASE_NAME
                )
            except exceptions.CosmosResourceExistsError:
                self.database = self.client.get_database_client(Config.COSMOS_DATABASE_NAME)
            
            # Create containers if they don't exist
            self._create_containers()
            
        except Exception as e:
            print(f"Error initializing Cosmos DB: {e}")
            self.client = None
    
    def _create_containers(self):
        """Create necessary containers"""
        containers = [
            {
                'id': 'users',
                'partition_key': PartitionKey(path="/email"),
            },
            {
                'id': 'newsletters',
                'partition_key': PartitionKey(path="/user_id"),
            },
            {
                'id': 'news_articles',
                'partition_key': PartitionKey(path="/topic"),
            },
            {
                'id': 'user_preferences',
                'partition_key': PartitionKey(path="/user_id"),
            }
        ]
        
        for container_config in containers:
            try:
                self.database.create_container_if_not_exists(
                    id=container_config['id'],
                    partition_key=container_config['partition_key'],
                )
            except exceptions.CosmosResourceExistsError:
                pass
    
    def is_available(self):
        """Check if Cosmos DB is available"""
        return self.client is not None
    
    # User operations
    def create_user(self, user_data):
        """Create a new user in Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('users')
            user_doc = {
                'id': str(user_data.get('id', user_data['email'])),
                'email': user_data['email'],
                'name': user_data['name'],
                'google_id': user_data.get('google_id'),
                'facebook_id': user_data.get('facebook_id'),
                'interests': user_data.get('interests', []),
                'newsletter_format': user_data.get('newsletter_format', 'single'),
                'delivery_schedule': user_data.get('delivery_schedule', {
                    'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                    'time': '08:00'
                }),
                'created_at': datetime.utcnow().isoformat(),
                'last_login': user_data.get('last_login'),
                'is_active': user_data.get('is_active', True),
                'type': 'user'
            }
            
            return container.create_item(body=user_doc)
        except Exception as e:
            print(f"Error creating user in Cosmos DB: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email from Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('users')
            query = "SELECT * FROM c WHERE c.email = @email AND c.type = 'user'"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@email", "value": email}],
                partition_key=email
            ))
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting user from Cosmos DB: {e}")
            return None
    
    def get_user_by_oauth_id(self, oauth_id, provider):
        """Get user by OAuth ID from Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('users')
            field = f"{provider}_id"
            query = f"SELECT * FROM c WHERE c.{field} = @oauth_id AND c.type = 'user'"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@oauth_id", "value": oauth_id}],
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting user by OAuth ID from Cosmos DB: {e}")
            return None
    
    def update_user(self, email, updates):
        """Update user in Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('users')
            user = self.get_user_by_email(email)
            if not user:
                return None
            
            user.update(updates)
            user['updated_at'] = datetime.utcnow().isoformat()
            
            return container.replace_item(item=user['id'], body=user)
        except Exception as e:
            print(f"Error updating user in Cosmos DB: {e}")
            return None
    
    # Newsletter operations
    def create_newsletter(self, newsletter_data):
        """Create a newsletter in Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('newsletters')
            newsletter_doc = {
                'id': f"{newsletter_data['user_id']}_{datetime.utcnow().timestamp()}",
                'user_id': newsletter_data['user_id'],
                'title': newsletter_data['title'],
                'content': newsletter_data['content'],
                'topic': newsletter_data.get('topic'),
                'created_at': datetime.utcnow().isoformat(),
                'sent_at': newsletter_data.get('sent_at'),
                'is_saved': newsletter_data.get('is_saved', False),
                'type': 'newsletter'
            }
            
            return container.create_item(body=newsletter_doc)
        except Exception as e:
            print(f"Error creating newsletter in Cosmos DB: {e}")
            return None
    
    def get_user_newsletters(self, user_id, limit=50):
        """Get newsletters for a user from Cosmos DB"""
        if not self.is_available():
            return []
        
        try:
            container = self.database.get_container_client('newsletters')
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.type = 'newsletter' ORDER BY c.created_at DESC"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@user_id", "value": str(user_id)}],
                partition_key=str(user_id),
                max_item_count=limit
            ))
            return items
        except Exception as e:
            print(f"Error getting newsletters from Cosmos DB: {e}")
            return []
    
    def save_newsletter(self, newsletter_id, user_id):
        """Save/unsave a newsletter"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('newsletters')
            query = "SELECT * FROM c WHERE c.id = @id AND c.user_id = @user_id"
            items = list(container.query_items(
                query=query,
                parameters=[
                    {"name": "@id", "value": newsletter_id},
                    {"name": "@user_id", "value": str(user_id)}
                ],
                partition_key=str(user_id)
            ))
            
            if items:
                newsletter = items[0]
                newsletter['is_saved'] = not newsletter.get('is_saved', False)
                return container.replace_item(item=newsletter['id'], body=newsletter)
            
            return None
        except Exception as e:
            print(f"Error saving newsletter in Cosmos DB: {e}")
            return None
    
    # News articles operations
    def create_news_article(self, article_data):
        """Create a news article in Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('news_articles')
            article_doc = {
                'id': f"{article_data['topic']}_{datetime.utcnow().timestamp()}",
                'title': article_data['title'],
                'content': article_data['content'],
                'summary': article_data.get('summary'),
                'source': article_data['source'],
                'url': article_data['url'],
                'topic': article_data['topic'],
                'political_bias': article_data.get('political_bias'),
                'published_at': article_data['published_at'],
                'created_at': datetime.utcnow().isoformat(),
                'type': 'news_article'
            }
            
            return container.create_item(body=article_doc)
        except Exception as e:
            print(f"Error creating news article in Cosmos DB: {e}")
            return None
    
    def get_news_articles_by_topic(self, topic, limit=20):
        """Get news articles by topic from Cosmos DB"""
        if not self.is_available():
            return []
        
        try:
            container = self.database.get_container_client('news_articles')
            query = "SELECT * FROM c WHERE c.topic = @topic AND c.type = 'news_article' ORDER BY c.published_at DESC"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@topic", "value": topic}],
                partition_key=topic,
                max_item_count=limit
            ))
            return items
        except Exception as e:
            print(f"Error getting news articles from Cosmos DB: {e}")
            return []
    
    # User preferences operations
    def save_user_preferences(self, user_id, preferences):
        """Save user preferences in Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('user_preferences')
            pref_doc = {
                'id': f"pref_{user_id}",
                'user_id': str(user_id),
                'preferences': preferences,
                'updated_at': datetime.utcnow().isoformat(),
                'type': 'user_preferences'
            }
            
            # Try to replace if exists, otherwise create
            try:
                return container.replace_item(item=pref_doc['id'], body=pref_doc)
            except exceptions.CosmosResourceNotFoundError:
                return container.create_item(body=pref_doc)
                
        except Exception as e:
            print(f"Error saving user preferences in Cosmos DB: {e}")
            return None
    
    def get_user_preferences(self, user_id):
        """Get user preferences from Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('user_preferences')
            query = "SELECT * FROM c WHERE c.user_id = @user_id AND c.type = 'user_preferences'"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@user_id", "value": str(user_id)}],
                partition_key=str(user_id)
            ))
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting user preferences from Cosmos DB: {e}")
            return None

# Global instance
cosmos_service = CosmosService()

