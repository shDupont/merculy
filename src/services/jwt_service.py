"""
JWT Authentication Service for Merculy API
Handles token generation, validation, and user authentication
"""
import jwt
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, current_app
from src.config import Config
from src.services.user_service import CosmosUser
from src.services.cosmos_service import CosmosService

class JWTService:
    def __init__(self):
        self.secret_key = Config.JWT_SECRET_KEY
        self.algorithm = Config.JWT_ALGORITHM
        self.expires_in = Config.JWT_ACCESS_TOKEN_EXPIRES
        self.cosmos_service = CosmosService()
    
    def generate_token(self, user_id, email):
        """Generate JWT token for authenticated user"""
        try:
            payload = {
                'user_id': str(user_id),
                'email': email,
                'iat': datetime.utcnow(),
                'exp': datetime.utcnow() + timedelta(seconds=self.expires_in)
            }
            
            token = jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
            
            print(f"🔑 [JWT DEBUG] Token generated successfully for user {user_id}")
            print(f"    Email: {email}")
            print(f"    Expires in: {self.expires_in} seconds")
            print(f"    Token: {token[:50]}...")
            
            return token
            
        except Exception as e:
            print(f"❌ [JWT DEBUG] Error generating token: {e}")
            return None
    
    def decode_token(self, token):
        """Decode and validate JWT token"""
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            print(f"✅ [JWT DEBUG] Token decoded successfully")
            print(f"    User ID: {payload.get('user_id')}")
            print(f"    Email: {payload.get('email')}")
            print(f"    Expires: {datetime.fromtimestamp(payload.get('exp'))}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            print(f"⚠️ [JWT DEBUG] Token expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"❌ [JWT DEBUG] Invalid token: {e}")
            return None
        except Exception as e:
            print(f"❌ [JWT DEBUG] Error decoding token: {e}")
            return None
    
    def get_user_from_token(self, token):
        """Get user object from JWT token"""
        try:
            payload = self.decode_token(token)
            if not payload:
                return None
            
            user_id = payload.get('user_id')
            if not user_id:
                print(f"❌ [JWT DEBUG] No user_id in token payload")
                return None
            
            # Get user from database
            user_data = self.cosmos_service.get_user_by_id(user_id)
            if not user_data:
                print(f"❌ [JWT DEBUG] User {user_id} not found in database")
                return None
            
            print(f"✅ [JWT DEBUG] User retrieved from token: {user_data.get('email')}")
            return CosmosUser(user_data)
            
        except Exception as e:
            print(f"❌ [JWT DEBUG] Error getting user from token: {e}")
            return None

# Global JWT service instance
jwt_service = JWTService()

def jwt_required(f):
    """Decorator to require JWT authentication for routes"""
    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from Authorization header
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            print(f"⚠️ [JWT DEBUG] No Authorization header in request")
            print(f"    Endpoint: {request.endpoint}")
            print(f"    Method: {request.method}")
            print(f"    Headers: {dict(request.headers)}")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Authorization header missing'
            }), 401
        
        # Validate token format
        if not auth_header.startswith('Bearer '):
            print(f"⚠️ [JWT DEBUG] Invalid Authorization header format")
            print(f"    Header: {auth_header[:50]}...")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Invalid authorization header format. Use: Bearer <token>'
            }), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        if not token:
            print(f"⚠️ [JWT DEBUG] Empty token in Authorization header")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Token missing'
            }), 401
        
        # Get user from token
        current_user = jwt_service.get_user_from_token(token)
        
        if not current_user:
            print(f"⚠️ [JWT DEBUG] Token validation failed")
            print(f"    Token: {token[:50]}...")
            return jsonify({
                'error': 'Authentication required',
                'message': 'Invalid or expired token'
            }), 401
        
        print(f"✅ [JWT DEBUG] Authentication successful for {current_user.email}")
        print(f"    Endpoint: {request.endpoint}")
        print(f"    User ID: {current_user.id}")
        
        # Pass current_user as first argument to the route function
        return f(current_user, *args, **kwargs)
    
    return decorated

def get_current_user_from_token():
    """Utility function to get current user from token in request"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]
    return jwt_service.get_user_from_token(token)
