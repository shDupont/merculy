"""
Merculy Backend - Azure Cosmos DB Service
"""
from azure.cosmos import CosmosClient, exceptions
from flask import current_app
from typing import List, Dict, Optional
from ..models.user import User, Newsletter
from ..core.config import Config
import json
from datetime import datetime

class CosmosService:
    def __init__(self):
        self.config = Config()
        self.client = None
        self.database = None
        self.users_container = None
        self.newsletters_container = None
        self.sources_container = None

    def initialize(self):
        """Initialize Cosmos DB client and containers"""
        try:
            self.client = CosmosClient(
                self.config.COSMOS_URI,
                self.config.COSMOS_KEY
            )

            # Create database if not exists
            self.database = self.client.create_database_if_not_exists(
                id=self.config.COSMOS_DB_NAME
            )

            # Create containers if not exist
            self.users_container = self.database.create_container_if_not_exists(
                id="users",
                partition_key="/userId",
                offer_throughput=400
            )

            self.newsletters_container = self.database.create_container_if_not_exists(
                id="newsletters",
                partition_key="/userId",
                offer_throughput=400
            )

            self.sources_container = self.database.create_container_if_not_exists(
                id="sources",
                partition_key="/sourceId",
                offer_throughput=400
            )

        except Exception as e:
            current_app.logger.error(f"Cosmos DB initialization error: {str(e)}")
            raise

    # User operations
    def get_user(self, user_id: str) -> Optional[User]:
        """Get user by Azure AD B2C user_id"""
        try:
            query = "SELECT * FROM c WHERE c.userId = @user_id"
            parameters = [{"name": "@user_id", "value": user_id}]

            items = list(self.users_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ))

            if items:
                return User(**items[0])
            return None

        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            current_app.logger.error(f"Error getting user {user_id}: {str(e)}")
            return None

    def create_user(self, user: User) -> User:
        """Create new user"""
        try:
            user_dict = user.dict()
            user_dict['userId'] = user.user_id  # Partition key
            user_dict['id'] = user.user_id  # Cosmos DB id

            created_item = self.users_container.create_item(body=user_dict)
            return User(**created_item)

        except Exception as e:
            current_app.logger.error(f"Error creating user: {str(e)}")
            raise

    def update_user(self, user_id: str, updates: Dict) -> Optional[User]:
        """Update user"""
        try:
            # Get existing user
            existing_user = self.get_user(user_id)
            if not existing_user:
                return None

            # Update fields
            user_dict = existing_user.dict()
            user_dict.update(updates)
            user_dict['updated_at'] = datetime.utcnow().isoformat()
            user_dict['userId'] = user_id  # Ensure partition key
            user_dict['id'] = user_id

            updated_item = self.users_container.replace_item(
                item=user_id,
                body=user_dict
            )
            return User(**updated_item)

        except Exception as e:
            current_app.logger.error(f"Error updating user {user_id}: {str(e)}")
            return None

    def list_active_users(self) -> List[User]:
        """List all active users"""
        try:
            query = "SELECT * FROM c WHERE c.isActive = true"

            items = list(self.users_container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))

            return [User(**item) for item in items]

        except Exception as e:
            current_app.logger.error(f"Error listing active users: {str(e)}")
            return []

    # Newsletter operations
    def save_newsletter(self, newsletter: Newsletter) -> Newsletter:
        """Save newsletter"""
        try:
            newsletter_dict = newsletter.dict()
            newsletter_dict['userId'] = newsletter.user_id  # Partition key
            newsletter_dict['id'] = f"{newsletter.user_id}_{newsletter.date.strftime('%Y%m%d')}"

            created_item = self.newsletters_container.upsert_item(body=newsletter_dict)
            return Newsletter(**created_item)

        except Exception as e:
            current_app.logger.error(f"Error saving newsletter: {str(e)}")
            raise

    def get_user_newsletters(self, user_id: str, limit: int = 10) -> List[Newsletter]:
        """Get user's newsletters"""
        try:
            query = "SELECT * FROM c WHERE c.userId = @user_id ORDER BY c.date DESC OFFSET 0 LIMIT @limit"
            parameters = [
                {"name": "@user_id", "value": user_id},
                {"name": "@limit", "value": limit}
            ]

            items = list(self.newsletters_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=user_id
            ))

            return [Newsletter(**item) for item in items]

        except Exception as e:
            current_app.logger.error(f"Error getting newsletters for user {user_id}: {str(e)}")
            return []

# Global service instance
cosmos_service = CosmosService()
