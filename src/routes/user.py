from flask import Blueprint, jsonify, request
from src.services.user_service import user_service
from src.services.jwt_service import jwt_required

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
@jwt_required
def get_users(current_user):
    """Get all users (admin functionality)"""
    try:
        limit = request.args.get('limit', 100, type=int)
        users = user_service.get_all_users(limit)
        print(f"✅ [USER DEBUG] Admin user {current_user.email} requested users list")
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        print(f"❌ [USER DEBUG] Error getting users: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users', methods=['POST'])
@jwt_required
def create_user(current_user):
    """Create a new user (admin functionality)"""
    try:
        data = request.json
        
        if not data or not data.get('email') or not data.get('name'):
            return jsonify({'error': 'Email and name are required'}), 400
        
        user = user_service.create_user(
            email=data['email'],
            name=data['name'],
            password=data.get('password'),
            interests=data.get('interests', []),
            newsletter_format=data.get('newsletter_format', 'single'),
            delivery_schedule=data.get('delivery_schedule')
        )
        
        if not user:
            return jsonify({'error': 'Failed to create user or user already exists'}), 409
        
        print(f"✅ [USER DEBUG] Admin user {current_user.email} created new user: {user.email}")
        return jsonify(user.to_dict()), 201
        
    except Exception as e:
        print(f"❌ [USER DEBUG] Error creating user: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required
def get_user(current_user, user_id):
    """Get user by ID"""
    try:
        user = user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        print(f"✅ [USER DEBUG] User {current_user.email} requested user info for: {user_id}")
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        print(f"❌ [USER DEBUG] Error getting user: {e}")
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required
def update_user(current_user, user_id):
    """Update user by ID"""
    try:
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Only allow users to update their own profile, or admin functionality
        if current_user.id != user_id:
            # Here you could add admin check logic
            return jsonify({'error': 'Unauthorized'}), 403
        
        updates = {}
        if 'name' in data:
            updates['name'] = data['name']
        if 'interests' in data:
            updates['interests'] = data['interests']
        if 'newsletter_format' in data:
            updates['newsletter_format'] = data['newsletter_format']
        if 'delivery_schedule' in data:
            updates['delivery_schedule'] = data['delivery_schedule']
        
        updated_user = user_service.update_user(user_id, **updates)
        
        if not updated_user:
            return jsonify({'error': 'User not found or update failed'}), 404
        
        return jsonify(updated_user.to_dict()), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@user_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required
def delete_user(current_user, user_id):
    """Delete user by ID"""
    try:
        # Only allow users to delete their own profile, or admin functionality
        if current_user.id != user_id:
            # Here you could add admin check logic
            return jsonify({'error': 'Unauthorized'}), 403
        
        success = user_service.delete_user(user_id)
        
        if not success:
            return jsonify({'error': 'User not found or deletion failed'}), 404
        
        print(f"✅ [USER DEBUG] User {current_user.email} deleted their profile")
        return '', 204
        
    except Exception as e:
        print(f"❌ [USER DEBUG] Error deleting user: {e}")
        return jsonify({'error': str(e)}), 500
