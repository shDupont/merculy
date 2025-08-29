from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
import json
from datetime import datetime

from src.services.user_service import user_service
from src.config import Config

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register a new user with email and password"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password') or not data.get('name'):
            return jsonify({'error': 'Email, password and name are required'}), 400
        
        # Check if user already exists
        existing_user = user_service.get_user_by_email(data['email'])
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        user = user_service.create_user(
            email=data['email'],
            name=data['name'],
            password=data['password'],
            interests=data.get('interests', []),
            newsletter_format=data.get('newsletter_format', 'single'),
            delivery_schedule=data.get('delivery_schedule')
        )
        
        if not user:
            return jsonify({'error': 'Failed to create user'}), 500
        
        login_user(user, force=True)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = user_service.authenticate_user(data['email'], data['password'])
        
        if not user:
            return jsonify({'error': 'Invalid credentials'}), 401
        
        # Update last login
        user_service.update_last_login(user.id)
        
        is_logged = login_user(user, force=True)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'isLogged': is_logged
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/google-login', methods=['POST'])
def google_login():
    """Login with Google OAuth"""
    try:
        data = request.get_json()
        token = data.get('token')
        
        if not token:
            return jsonify({'error': 'Google token is required'}), 400
        
        # Verify the token with Google
        try:
            idinfo = id_token.verify_oauth2_token(
                token, 
                google_requests.Request(), 
                Config.GOOGLE_CLIENT_ID
            )
            
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Wrong issuer.')
                
        except ValueError as e:
            return jsonify({'error': 'Invalid Google token'}), 401
        
        google_id = idinfo['sub']
        email = idinfo['email']
        name = idinfo['name']
        
        print(f'[DEBUG] Google OAuth - ID: {google_id}, Email: {email}, Name: {name}')

        # Check if user exists by Google ID
        user = user_service.get_user_by_oauth_id(google_id, 'google')
        print(f'[DEBUG] User found by Google ID: {user is not None}')
        
        if not user:
            # Check if user exists with same email
            user = user_service.get_user_by_email(email)
            print(f'[DEBUG] User found by email: {user is not None}')
            if user:
                # Link Google account to existing user
                print('[DEBUG] Linking Google account to existing user')
                user_service.update_user(user.id, google_id=google_id)
                user.google_id = google_id
            else:
                # Create new user
                print('[DEBUG] Creating new user with Google OAuth')
                user = user_service.create_user(
                    email=email,
                    name=name,
                    google_id=google_id
                )
                print(f'[DEBUG] User created: {user is not None}')
        
        if not user:
            print('[DEBUG] FAILED: User is None after all attempts')
            return jsonify({
                'error': 'Failed to create or retrieve user',
                'debug': {
                    'google_id': google_id,
                    'email': email,
                    'cosmos_available': user_service.cosmos_service.is_available()
                }
            }), 500
        
        # Update last login
        user_service.update_last_login(user.id)
        
        login_user(user, force=True)
        
        return jsonify({
            'message': 'Google login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/facebook-login', methods=['POST'])
def facebook_login():
    """Login with Facebook OAuth"""
    try:
        data = request.get_json()
        access_token = data.get('access_token')
        
        if not access_token:
            return jsonify({'error': 'Facebook access token is required'}), 400
        
        # Verify token with Facebook
        fb_response = requests.get(
            f'https://graph.facebook.com/me?fields=id,name,email&access_token={access_token}'
        )
        
        if fb_response.status_code != 200:
            return jsonify({'error': 'Invalid Facebook token'}), 401
        
        fb_data = fb_response.json()
        facebook_id = fb_data['id']
        email = fb_data.get('email')
        name = fb_data['name']
        
        if not email:
            return jsonify({'error': 'Email permission required from Facebook'}), 400
        
        # Check if user exists by Facebook ID
        user = user_service.get_user_by_oauth_id(facebook_id, 'facebook')
        
        if not user:
            # Check if user exists with same email
            user = user_service.get_user_by_email(email)
            if user:
                # Link Facebook account to existing user
                user_service.update_user(user.id, facebook_id=facebook_id)
                user.facebook_id = facebook_id
            else:
                # Create new user
                user = user_service.create_user(
                    email=email,
                    name=name,
                    facebook_id=facebook_id
                )
        
        if not user:
            return jsonify({'error': 'Failed to create or retrieve user'}), 500
        
        # Update last login
        user_service.update_last_login(user.id)
        
        login_user(user, force=True)
        
        return jsonify({
            'message': 'Facebook login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """Logout current user"""
    logout_user()
    return jsonify({'message': 'Logout successful'}), 200

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_current_user():
    """Get current user information"""
    return jsonify({'user': current_user.to_dict()}), 200

@auth_bp.route('/update-profile', methods=['PUT'])
@login_required
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()
        
        updates = {}
        
        if data.get('name'):
            updates['name'] = data['name']
        
        if data.get('interests'):
            updates['interests'] = data['interests']
        
        if data.get('newsletter_format'):
            updates['newsletter_format'] = data['newsletter_format']
        
        if data.get('delivery_schedule'):
            updates['delivery_schedule'] = data['delivery_schedule']
        
        updated_user = user_service.update_user(current_user.id, **updates)
        
        if not updated_user:
            return jsonify({'error': 'Failed to update profile'}), 500
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': updated_user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['PUT'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        if not current_user.passwordHash:
            return jsonify({'error': 'Cannot change password for OAuth-only accounts'}), 400
        
        if not check_password_hash(current_user.passwordHash, data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        success = user_service.change_password(current_user.id, data['new_password'])
        
        if not success:
            return jsonify({'error': 'Failed to change password'}), 500
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

