"""
Merculy Backend - Configuration Settings
"""
import os
from typing import List
from pydantic import BaseSettings

class Config(BaseSettings):
    # Flask Settings
    SECRET_KEY: str = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
    FLASK_ENV: str = os.getenv('FLASK_ENV', 'development')

    # Azure AD B2C
    AZURE_TENANT_ID: str = os.getenv('AZURE_TENANT_ID', '')
    AZURE_B2C_POLICY: str = os.getenv('AZURE_B2C_POLICY', '')
    AZURE_CLIENT_ID: str = os.getenv('AZURE_CLIENT_ID', '')
    AZURE_OPENID_CONFIG: str = os.getenv('AZURE_OPENID_CONFIG', '')

    # Azure Cosmos DB
    COSMOS_URI: str = os.getenv('COSMOS_URI', '')
    COSMOS_KEY: str = os.getenv('COSMOS_KEY', '')
    COSMOS_DB_NAME: str = os.getenv('COSMOS_DB_NAME', 'merculy')

    # Google Gemini
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')

    # SendGrid
    SENDGRID_API_KEY: str = os.getenv('SENDGRID_API_KEY', '')
    SENDGRID_FROM_EMAIL: str = os.getenv('SENDGRID_FROM_EMAIL', 'noreply@merculy.com')

    # News APIs
    NEWSAPI_KEY: str = os.getenv('NEWSAPI_KEY', '')
    GUARDIAN_API_KEY: str = os.getenv('GUARDIAN_API_KEY', '')
    BING_NEWS_KEY: str = os.getenv('BING_NEWS_KEY', '')

    # Redis
    REDIS_URL: str = os.getenv('REDIS_URL', 'redis://localhost:6379')

    # CORS
    ALLOWED_ORIGINS: List[str] = ['http://localhost:3000', 'https://merculy.app']

    class Config:
        env_file = '.env'
