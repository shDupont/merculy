import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Cookies
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE= True
    SESSION_COOKIE_HTTPONLY = True   # Prevent XSS attacks
    SESSION_COOKIE_DOMAIN = None 

    # Session configuration
    PERMANENT_SESSION_LIFETIME = 86400  # 24 hours in seconds
    SESSION_REFRESH_EACH_REQUEST = True  # Extend session on each request

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

