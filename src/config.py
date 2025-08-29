import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session configuration for better security
    SESSION_COOKIE_SECURE = os.environ.get('FLASK_ENV') != 'development'  # Use HTTPS in production only
    SESSION_COOKIE_HTTPONLY = True  # Prevent XSS
    SESSION_COOKIE_SAMESITE = 'Lax'  # CSRF protection
    REMEMBER_COOKIE_SECURE = os.environ.get('FLASK_ENV') != 'development'
    REMEMBER_COOKIE_HTTPONLY = True
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
    GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET')
    FACEBOOK_CLIENT_ID = os.environ.get('FACEBOOK_CLIENT_ID')
    FACEBOOK_CLIENT_SECRET = os.environ.get('FACEBOOK_CLIENT_SECRET')
    
    # Azure Cosmos DB
    COSMOS_ENDPOINT = os.environ.get('COSMOS_ENDPOINT')
    COSMOS_KEY = os.environ.get('COSMOS_KEY')
    COSMOS_DATABASE_NAME = os.environ.get('COSMOS_DATABASE_NAME', 'merculy_db')
    COSMOS_CONTAINER_NAME = os.environ.get('COSMOS_CONTAINER_NAME', 'users')
    
    # Gemini API
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')
    
    # News API
    NEWS_API_KEY = os.environ.get('NEWS_API_KEY')
    NEWS_API_URL = os.environ.get('NEWS_API_URL', 'https://newsapi.org/v2/everything')
    
    # Available topics for news
    AVAILABLE_TOPICS = [
        'tecnologia',
        'política',
        'economia',
        'esportes',
        'saúde',
        'ciência',
        'entretenimento',
        'negócios',
        'educação',
        'meio ambiente'
    ]

