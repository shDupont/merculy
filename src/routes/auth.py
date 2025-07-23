from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests
import json
from datetime import datetime

from src.models.user import db, User
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
        existing_user = User.query.filter_by(email=data['email']).first()
        if existing_user:
            return jsonify({'error': 'User already exists'}), 409
        
        # Create new user
        user = User(
            email=data['email'],
            name=data['name'],
            password_hash=generate_password_hash(data['password'])
        )
        
        # Set initial preferences if provided
        if data.get('interests'):
            user.set_interests(data['interests'])
        if data.get('newsletter_format'):
            user.newsletter_format = data['newsletter_format']
        if data.get('delivery_schedule'):
            user.set_delivery_schedule(data['delivery_schedule'])
        
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        
        return jsonify({
            'message': 'User registered successfully',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login with email and password"""
    try:
        data = request.get_json()
        
        if not data or not data.get('email') or not data.get('password'):
            return jsonify({'error': 'Email and password are required'}), 400
        
        user = User.query.filter_by(email=data['email']).first()
        
        if not user or not user.password_hash or not check_password_hash(user.password_hash, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user)
        
        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict()
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
        
        # Check if user exists
        user = User.query.filter_by(google_id=google_id).first()
        
        if not user:
            # Check if user exists with same email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link Google account to existing user
                user.google_id = google_id
            else:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    google_id=google_id
                )
                db.session.add(user)
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user)
        
        return jsonify({
            'message': 'Google login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
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
        
        # Check if user exists
        user = User.query.filter_by(facebook_id=facebook_id).first()
        
        if not user:
            # Check if user exists with same email
            user = User.query.filter_by(email=email).first()
            if user:
                # Link Facebook account to existing user
                user.facebook_id = facebook_id
            else:
                # Create new user
                user = User(
                    email=email,
                    name=name,
                    facebook_id=facebook_id
                )
                db.session.add(user)
        
        if not user.is_active:
            return jsonify({'error': 'Account is deactivated'}), 401
        
        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        login_user(user)
        
        return jsonify({
            'message': 'Facebook login successful',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
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
        
        if data.get('name'):
            current_user.name = data['name']
        
        if data.get('interests'):
            current_user.set_interests(data['interests'])
        
        if data.get('newsletter_format'):
            current_user.newsletter_format = data['newsletter_format']
        
        if data.get('delivery_schedule'):
            current_user.set_delivery_schedule(data['delivery_schedule'])
        
        db.session.commit()
        
        return jsonify({
            'message': 'Profile updated successfully',
            'user': current_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@auth_bp.route('/change-password', methods=['PUT'])
@login_required
def change_password():
    """Change user password"""
    try:
        data = request.get_json()
        
        if not data.get('current_password') or not data.get('new_password'):
            return jsonify({'error': 'Current password and new password are required'}), 400
        
        if not current_user.password_hash:
            return jsonify({'error': 'Cannot change password for OAuth-only accounts'}), 400
        
        if not check_password_hash(current_user.password_hash, data['current_password']):
            return jsonify({'error': 'Current password is incorrect'}), 401
        
        current_user.password_hash = generate_password_hash(data['new_password'])
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

