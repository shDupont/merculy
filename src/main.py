import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, request, send_from_directory, session
from flask_login import LoginManager, current_user
from flask_cors import CORS
from dotenv import load_dotenv

from src.services.user_service import user_service
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.news import news_bp
from src.config import Config

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
    
    # Configuration
    app.config.from_object(Config)
    
    # Enable CORS for all routes
    CORS(app, supports_credentials=True)
    
    # Initialize Flask-Login
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_email):
        """Load user from Cosmos DB for Flask-Login"""
        print(f"[DEBUG] user_email: {user_email}")
        return user_service.get_user_by_email(user_email)
    
    # Configure for API usage (no redirects)
    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({'error': 'Authentication required'}), 401
    
    # Register blueprints
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(news_bp, url_prefix='/api')
    
    # Initialize Cosmos DB connection (replaces SQLAlchemy table creation)
    with app.app_context():
        try:
            # Test Cosmos DB connection
            if user_service.cosmos_service.is_available():
                print("✅ Cosmos DB connection successful")
            else:
                print("❌ Cosmos DB connection failed - check your configuration")
        except Exception as e:
            print(f"❌ Error connecting to Cosmos DB: {e}")
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'message': 'Merculy Backend API is running',
            'version': '1.0.0'
        }

    # API info endpoint
    @app.route('/api')
    def api_info():
        return {
            'name': 'Merculy Backend API',
            'version': '1.0.0',
            'description': 'Backend API for Merculy newsletter application',
            'endpoints': {
                'auth': {
                    'POST /api/auth/register': 'Register new user',
                    'POST /api/auth/login': 'Login with email/password',
                    'POST /api/auth/google-login': 'Login with Google',
                    'POST /api/auth/facebook-login': 'Login with Facebook',
                    'POST /api/auth/logout': 'Logout current user',
                    'GET /api/auth/me': 'Get current user info',
                    'PUT /api/auth/update-profile': 'Update user profile',
                    'PUT /api/auth/change-password': 'Change user password'
                },
                'news': {
                    'GET /api/topics': 'Get available topics',
                    'GET /api/news/<topic>': 'Get news by topic',
                    'GET /api/trending': 'Get trending news',
                    'GET /api/search': 'Search news articles',
                    'POST /api/newsletter/generate': 'Generate personalized newsletter',
                    'GET /api/newsletters': 'Get user newsletters',
                    'POST /api/newsletters/<id>/save': 'Save/unsave newsletter',
                    'GET /api/newsletters/saved': 'Get saved newsletters',
                    'GET /api/preferences/topics': 'Get topic suggestions',
                    'POST /api/articles/<id>/analyze': 'Analyze article for fake news'
                },
                'users': {
                    'GET /api/users': 'Get all users (admin)',
                    'GET /api/users/<id>': 'Get user by ID',
                    'PUT /api/users/<id>': 'Update user',
                    'DELETE /api/users/<id>': 'Delete user'
                }
            }
        }

     # Serve frontend files
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve(path):
        static_folder_path = app.static_folder
        if static_folder_path is None:
            return "Static folder not configured", 404

        if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
            return send_from_directory(static_folder_path, path)
        else:
            index_path = os.path.join(static_folder_path, 'index.html')
            if os.path.exists(index_path):
                return send_from_directory(static_folder_path, 'index.html')
            else:
                return "Frontend not available. This is a backend API.", 200
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

