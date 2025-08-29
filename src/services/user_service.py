"""
User service for managing user data in Azure Cosmos DB.
Replaces the SQLAlchemy User model with Cosmos DB operations.
"""
from datetime import datetime
import hashlib
import json
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from src.services.cosmos_service import CosmosService


class CosmosUser(UserMixin):
    """
    User class compatible with Flask-Login that uses Cosmos DB as backend.
    Replaces the SQLAlchemy User model.
    """
    
    def __init__(self, user_data=None):
        if user_data:
            self.id = user_data.get('id')
            self.email = user_data.get('email')
            self.name = user_data.get('name')
            self.password_hash = user_data.get('password_hash')
            self.google_id = user_data.get('google_id')
            self.facebook_id = user_data.get('facebook_id')
            self.interests = user_data.get('interests', [])
            self.newsletter_format = user_data.get('newsletter_format', 'single')
            self.delivery_schedule = user_data.get('delivery_schedule', {
                'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                'time': '08:00'
            })
            self.created_at = user_data.get('created_at')
            self.last_login = user_data.get('last_login')
        else:
            # Initialize empty user
            self.id = None
            self.email = None
            self.name = None
            self.password_hash = None
            self.google_id = None
            self.facebook_id = None
            self.interests = []
            self.newsletter_format = 'single'
            self.delivery_schedule = {
                'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                'time': '08:00'
            }
            self.created_at = None
            self.last_login = None

    def get_id(self):
        """Return user ID for Flask-Login"""
        return str(self.email) if self.email else None

    def get_interests(self):
        """Get user interests as a list"""
        return self.interests if isinstance(self.interests, list) else []
    
    def set_interests(self, interests_list):
        """Set user interests from a list"""
        self.interests = interests_list if isinstance(interests_list, list) else []
    
    def get_delivery_schedule(self):
        """Get delivery schedule as dict"""
        if isinstance(self.delivery_schedule, dict):
            return self.delivery_schedule
        return {'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'], 'time': '08:00'}
    
    def set_delivery_schedule(self, schedule_dict):
        """Set delivery schedule from dict"""
        if isinstance(schedule_dict, dict):
            self.delivery_schedule = schedule_dict
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'interests': self.get_interests(),
            'newsletter_format': self.newsletter_format,
            'delivery_schedule': self.get_delivery_schedule(),
            'created_at': self.created_at,
            'password_hash': self.password_hash
        }

    def to_cosmos_dict(self):
        """Convert user to dictionary for Cosmos DB storage"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'password_hash': self.password_hash,
            'google_id': self.google_id,
            'facebook_id': self.facebook_id,
            'interests': self.get_interests(),
            'newsletter_format': self.newsletter_format,
            'delivery_schedule': self.get_delivery_schedule(),
            'created_at': self.created_at,
            'last_login': self.last_login,
            'type': 'user'
        }


class UserService:
    """
    Service class for managing users in Cosmos DB.
    Replaces direct SQLAlchemy operations.
    """
    
    def __init__(self):
        self.cosmos_service = CosmosService()
    
    def _generate_user_id(self, email):
        """Generate a consistent user ID from email"""
        return hashlib.md5(email.encode()).hexdigest()
    
    def create_user(self, email, name, password=None, google_id=None, facebook_id=None, **kwargs):
        """
        Create a new user in Cosmos DB
        
        Args:
            email (str): User email
            name (str): User name
            password (str, optional): User password (will be hashed)
            google_id (str, optional): Google OAuth ID
            facebook_id (str, optional): Facebook OAuth ID
            **kwargs: Additional user attributes
        
        Returns:
            CosmosUser: Created user object or None if failed
        """
        try:
            # Check if user already exists
            existing_user = self.get_user_by_email(email)
            if existing_user:
                print(f'[DEBUG] User already exists: {email}')
                return None
            
            # Generate user ID
            user_id = self._generate_user_id(email)
            print(f'[DEBUG] Generated user ID: {user_id} for email: {email}')
            
            # Create user data
            user_data = {
                'id': user_id,
                'email': email,
                'name': name,
                'google_id': google_id,
                'facebook_id': facebook_id,
                'interests': kwargs.get('interests', []),
                'newsletter_format': kwargs.get('newsletter_format', 'single'),
                'delivery_schedule': kwargs.get('delivery_schedule', {
                    'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
                    'time': '08:00'
                }),
                'followed_channels': kwargs.get('followed_channels', []),
                'created_at': datetime.utcnow().isoformat(),
                'update_at': datetime.utcnow().isoformat(),
                'last_login': None,
                'password_hash': generate_password_hash(password) if password else None
            }
            
            print(f'[DEBUG] User data created: {user_data}')
            print(f'[DEBUG] Cosmos service available: {self.cosmos_service.is_available()}')
            
            # Save to Cosmos DB
            cosmos_user = self.cosmos_service.create_user(user_data)
            print(f'[DEBUG] Cosmos user creation result: {cosmos_user is not None}')
            if cosmos_user:
                return CosmosUser(cosmos_user)
            
            return None
            
        except Exception as e:
            print(f"[ERROR] Error creating user: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def get_user_by_email(self, email):
        """
        Get user by email from Cosmos DB
        
        Args:
            email (str): User email
            
        Returns:
            CosmosUser: User object or None if not found
        """
        try:
            print('[GET EMAIL]')
            print(email)
            cosmos_user = self.cosmos_service.get_user_by_email(email)
            if cosmos_user:
                return CosmosUser(cosmos_user)
            return None
        except Exception as e:
            print(f"Error getting user by email: {e}")
            return None
    
    def get_user_by_id(self, user_id):
        """
        Get user by ID from Cosmos DB
        
        Args:
            user_id (str): User ID
            
        Returns:
            CosmosUser: User object or None if not found
        """
        try:
            if not self.cosmos_service.is_available():
                return None
            
            container = self.cosmos_service.database.get_container_client('users')
            user_doc = container.read_item(item=user_id, partition_key=None)
            
            if user_doc and user_doc.get('type') == 'user':
                return CosmosUser(user_doc)
            return None
            
        except Exception as e:
            print(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_oauth_id(self, oauth_id, provider):
        """
        Get user by OAuth ID from Cosmos DB
        
        Args:
            oauth_id (str): OAuth ID
            provider (str): OAuth provider ('google' or 'facebook')
            
        Returns:
            CosmosUser: User object or None if not found
        """
        try:
            cosmos_user = self.cosmos_service.get_user_by_oauth_id(oauth_id, provider)
            if cosmos_user:
                return CosmosUser(cosmos_user)
            return None
        except Exception as e:
            print(f"Error getting user by OAuth ID: {e}")
            return None
    
    def update_user(self, user_email, **updates):
        """
        Update user in Cosmos DB
        
        Args:
            user_email (str): User ID
            **updates: Fields to update
            
        Returns:
            CosmosUser: Updated user object or None if failed
        """
        try:
            # Get current user
            user = self.get_user_by_email(user_email)
            if not user:
                return None
            
            # Update fields
            for key, value in updates.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            
            # Update in Cosmos DB
            updated_user = self.cosmos_service.update_user(user.email, updates)
            if updated_user:
                return CosmosUser(updated_user)
            
            return None
            
        except Exception as e:
            print(f"Error updating user: {e}")
            return None
    
    def update_last_login(self, user_email):
        """
        Update user's last login timestamp
        
        Args:
            user_email (str): User ID
            
        Returns:
            CosmosUser: Updated user object or None if failed
        """
        return self.update_user(user_email, last_login=datetime.utcnow().isoformat())
    
    def authenticate_user(self, email, password):
        """
        Authenticate user with email and password
        
        Args:
            email (str): User email
            password (str): User password
            
        Returns:
            CosmosUser: Authenticated user object or None if authentication failed
        """
        try:
            user = self.get_user_by_email(email)
            print('[AUTH]')
            print(user.to_dict.__str__)
            if not user or not user.password_hash:
                return None
            
            if check_password_hash(user.password_hash, password):
                return user
            
            return None
            
        except Exception as e:
            print(f"Error authenticating user: {e}")
            return None
    
    def change_password(self, user_id, new_password):
        """
        Change user password
        
        Args:
            user_id (str): User ID
            new_password (str): New password
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            password_hash = generate_password_hash(new_password)
            updated_user = self.update_user(user_id, password_hash=password_hash)
            return updated_user is not None
        except Exception as e:
            print(f"Error changing password: {e}")
            return False
    
    def get_all_users(self, limit=100):
        """
        Get all users (admin function)
        
        Args:
            limit (int): Maximum number of users to return
            
        Returns:
            list: List of CosmosUser objects
        """
        try:
            if not self.cosmos_service.is_available():
                return []
            
            container = self.cosmos_service.database.get_container_client('users')
            query = "SELECT * FROM c WHERE c.type = 'user' ORDER BY c.created_at DESC"
            items = list(container.query_items(
                query=query,
                enable_cross_partition_query=True,
                max_item_count=limit
            ))
            
            return [CosmosUser(item) for item in items]
            
        except Exception as e:
            print(f"Error getting all users: {e}")
            return []
    
    def delete_user(self, user_id):
        """
        Delete user from Cosmos DB
        
        Args:
            user_id (str): User ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not self.cosmos_service.is_available():
                return False
            
            container = self.cosmos_service.database.get_container_client('users')
            container.delete_item(item=user_id, partition_key=None)
            return True
            
        except Exception as e:
            print(f"Error deleting user: {e}")
            return False


# Global instance
user_service = UserService()
