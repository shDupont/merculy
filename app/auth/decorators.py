"""
Merculy Backend - Authentication Decorators
"""
from functools import wraps
from flask import request, jsonify, g
from .azure_b2c import azure_auth

def requires_auth(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return jsonify({'error': 'Authorization header required'}), 401

        try:
            # Extract token from "Bearer <token>"
            token = auth_header.split(' ')[1]
        except IndexError:
            return jsonify({'error': 'Invalid authorization header format'}), 401

        # Validate token
        payload = azure_auth.validate_token(token)
        if not payload:
            return jsonify({'error': 'Invalid or expired token'}), 401

        # Store user info in g for use in route
        g.current_user = {
            'user_id': payload.get('sub'),
            'email': payload.get('email'),
            'name': payload.get('name'),
            'roles': payload.get('extension_roles', ['user'])
        }

        return f(*args, **kwargs)

    return decorated_function

def requires_role(required_role):
    """Decorator to require specific role"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not hasattr(g, 'current_user'):
                return jsonify({'error': 'Authentication required'}), 401

            user_roles = g.current_user.get('roles', [])
            if required_role not in user_roles and 'admin' not in user_roles:
                return jsonify({'error': 'Insufficient permissions'}), 403

            return f(*args, **kwargs)

        return decorated_function
    return decorator
