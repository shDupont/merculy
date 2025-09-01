import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, jsonify, request, send_from_directory
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
    
    # Enable CORS for all routes with JWT token support
    CORS(
        app, 
        supports_credentials=True, 
        origins="*",
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
        methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        expose_headers=["Authorization"]
    )
    
    # Additional CORS headers for complex requests
    @app.after_request
    def after_request(response):
        origin = request.headers.get('Origin')
        if origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
        response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response

    # Handle preflight OPTIONS requests
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({'status': 'OK'})
            response.headers['Access-Control-Allow-Origin'] = request.headers.get('Origin', '*')
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization,X-Requested-With'
            response.headers['Access-Control-Allow-Credentials'] = 'true'
            return response

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
                print("⚠️  App will continue but database operations may fail")
        except Exception as e:
            print(f"❌ Error connecting to Cosmos DB: {e}")
            print("⚠️  App will continue but database operations may fail")
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return {
            'status': 'healthy',
            'message': 'Merculy Backend API is running',
            'version': '1.0.0'
        }
    
    # CORS test endpoint
    @app.route('/cors-test')
    def cors_test():
        return {
            'message': 'CORS is working!',
            'headers': dict(request.headers),
            'origin': request.headers.get('Origin', 'Not provided')
        }
    
    # @app.route('/debug/jwt-info')
    # def jwt_info():
    #     """Debug endpoint to check JWT authentication info"""
    #     from src.services.jwt_service import get_current_user_from_token
        
    #     auth_header = request.headers.get('Authorization', 'None')
    #     current_user = get_current_user_from_token()
        
    #     return jsonify({
    #         'auth_header': auth_header[:50] + '...' if len(auth_header) > 50 else auth_header,
    #         'user_authenticated': current_user is not None,
    #         'user_id': getattr(current_user, 'id', None) if current_user else None,
    #         'user_email': getattr(current_user, 'email', None) if current_user else None,
    #         'headers': dict(request.headers),
    #         'environment': {
    #             'jwt_secret_configured': bool(app.config.get('JWT_SECRET_KEY')),
    #             'jwt_expires_in': app.config.get('JWT_ACCESS_TOKEN_EXPIRES'),
    #             'jwt_algorithm': app.config.get('JWT_ALGORITHM'),
    #         }
    #     })

    
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
    return app

app = create_app()

if __name__ == '__main__':
    # Use Azure's PORT environment variable or default to 8000
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)

