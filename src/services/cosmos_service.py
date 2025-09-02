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
                'partition_key': PartitionKey(path="/id"),
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
            },
            {
                'id': 'newsConf',
                'partition_key': PartitionKey(path="/id"),
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
            
            return container.create_item(body=user_data)
        except Exception as e:
            print(f"Error creating user in Cosmos DB: {e}")
            return None
    
    def get_user_by_email(self, email):
        """Get user by email from Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('users')
            query = "SELECT * FROM c WHERE c.email = @email"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@email", "value": email}],
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting user from Cosmos DB: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """Get user by ID from Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('users')
            query = "SELECT * FROM c WHERE c.id = @user_id"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@user_id", "value": str(user_id)}],
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting user by ID from Cosmos DB: {e}")
            return None
    
    def get_user_by_oauth_id(self, oauth_id, provider):
        """Get user by OAuth ID from Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('users')
            field = f"{provider}_id"
            query = f"SELECT * FROM c WHERE c.{field} = @oauth_id"
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
                'topic': newsletter_data.get('topic'),
                'articles': newsletter_data.get('articles', []),  # List of article IDs
                'created_at': datetime.utcnow().isoformat(),
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
    
    def get_newsletter_by_id(self, newsletter_id, user_id):
        """Get newsletter by ID"""
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
            
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting newsletter by ID from Cosmos DB: {e}")
            return None
    
    def delete_newsletter(self, newsletter_id, user_id):
        """Delete a newsletter"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('newsletters')
            container.delete_item(item=newsletter_id, partition_key=str(user_id))
            return True
        except Exception as e:
            print(f"Error deleting newsletter in Cosmos DB: {e}")
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
                'bullet_point_highlights': article_data.get('bullet_point_highlights'),
                'source': article_data['source'],
                'url': article_data['url'],
                'topic': article_data['topic'],
                'image_url': article_data.get('image_url'),
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
    
    def get_news_article_by_id(self, article_id):
        """Get news article by ID from Cosmos DB"""
        if not self.is_available():
            return None
        
        try:
            container = self.database.get_container_client('news_articles')
            query = "SELECT * FROM c WHERE c.id = @article_id AND c.type = 'news_article'"
            items = list(container.query_items(
                query=query,
                parameters=[{"name": "@article_id", "value": article_id}],
                enable_cross_partition_query=True
            ))
            return items[0] if items else None
        except Exception as e:
            print(f"Error getting news article by ID from Cosmos DB: {e}")
            return None
    
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

    # News configuration operations
    def get_available_topics(self):
        """Get available topics from Cosmos DB newsConf container"""
        if not self.is_available():
            return []
        
        try:
            container = self.database.get_container_client('newsConf')
            item = container.read_item(
                item='available-topics',
                partition_key='available-topics'
            )
            
            if item and 'items' in item:
                # Return only active topics
                active_topics = [topic for topic in item['items'] if topic.get('isActive', True)]
                return active_topics
            return []
        except Exception as e:
            print(f"Error getting topics from Cosmos DB: {e}")
            return []
    
    def get_available_channels(self):
        """Get available channels from Cosmos DB newsConf container"""
        if not self.is_available():
            return []
        
        try:
            container = self.database.get_container_client('newsConf')
            item = container.read_item(
                item='available-channels',
                partition_key='available-channels'
            )
            
            if item and 'items' in item:
                # Return only active channels
                active_channels = [channel for channel in item['items'] if channel.get('isActive', True)]
                return active_channels
            return []
        except Exception as e:
            print(f"Error getting channels from Cosmos DB: {e}")
            return []

    def get_domain_from_channels(self, channels: list[str]):
        """ Convert channel IDs to domains """
        channel_domains = []
        if channels:
            # Get all available channels from Cosmos DB
            all_channels = self.get_available_channels()
            
            for channel_id in channels:
                # Find the corresponding domain for each channel ID
                for channel in all_channels:
                    if channel.get('id') == channel_id and channel.get('isActive', True):
                        channel_domains.append(channel.get('domain'))
                        break
                    
        return channel_domains if channel_domains else None
        
# Global instance
cosmos_service = CosmosService()

