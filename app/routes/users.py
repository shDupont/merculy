"""
Merculy Backend - User Management Routes
"""
from flask import Blueprint, request, jsonify, g
from datetime import datetime
from ..auth.decorators import requires_auth, requires_role
from ..services.cosmos import cosmos_service
from ..models.user import User, UserUpdate, UserPreferences
from pydantic import ValidationError

users_bp = Blueprint('users', __name__)

@users_bp.before_app_first_request
def initialize_cosmos():
    """Initialize Cosmos DB before first request"""
    cosmos_service.initialize()

@users_bp.route('/profile', methods=['GET'])
@requires_auth
def get_profile():
    """Get current user profile"""
    try:
        user = cosmos_service.get_user(g.current_user['user_id'])

        if not user:
            # First time user - create profile
            user = User(
                user_id=g.current_user['user_id'],
                email=g.current_user['email'],
                name=g.current_user['name'],
                last_login=datetime.utcnow()
            )
            user = cosmos_service.create_user(user)
        else:
            # Update last login
            cosmos_service.update_user(
                g.current_user['user_id'],
                {'last_login': datetime.utcnow().isoformat()}
            )

        return jsonify(user.dict())

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/profile', methods=['PUT'])
@requires_auth
def update_profile():
    """Update user profile"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate data
        try:
            user_update = UserUpdate(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': e.errors()}), 400

        # Update user
        updated_user = cosmos_service.update_user(
            g.current_user['user_id'],
            user_update.dict(exclude_unset=True)
        )

        if not updated_user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(updated_user.dict())

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/profile/preferences', methods=['PUT'])
@requires_auth
def update_preferences():
    """Update user preferences"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate preferences data
        try:
            preferences = UserPreferences(**data)
        except ValidationError as e:
            return jsonify({'error': 'Validation error', 'details': e.errors()}), 400

        # Update user preferences
        updated_user = cosmos_service.update_user(
            g.current_user['user_id'],
            {'preferences': preferences.dict()}
        )

        if not updated_user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({
            'message': 'Preferences updated successfully',
            'preferences': updated_user.preferences.dict()
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/profile/preferences', methods=['GET'])
@requires_auth
def get_preferences():
    """Get user preferences"""
    try:
        user = cosmos_service.get_user(g.current_user['user_id'])

        if not user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify(user.preferences.dict())

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/profile/topics', methods=['GET'])
def get_available_topics():
    """Get list of available topics"""
    # Default topics that users can choose from
    topics = [
        'Política',
        'Economia',
        'Tecnologia',
        'Esportes',
        'Saúde',
        'Ciência',
        'Entretenimento',
        'Mundo',
        'Brasil',
        'Negócios',
        'Educação',
        'Meio Ambiente',
        'Arte e Cultura',
        'Moda e Estilo',
        'Viagem'
    ]

    return jsonify({
        'topics': topics,
        'custom_topics_allowed': True
    })

@users_bp.route('/users', methods=['GET'])
@requires_auth
@requires_role('admin')
def list_users():
    """List all users (admin only)"""
    try:
        users = cosmos_service.list_active_users()
        users_data = [
            {
                'user_id': user.user_id,
                'email': user.email,
                'name': user.name,
                'is_active': user.is_active,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None
            }
            for user in users
        ]

        return jsonify({
            'users': users_data,
            'total': len(users_data)
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.route('/users/<user_id>/deactivate', methods=['POST'])
@requires_auth
@requires_role('admin')
def deactivate_user(user_id):
    """Deactivate user (admin only)"""
    try:
        updated_user = cosmos_service.update_user(user_id, {'is_active': False})

        if not updated_user:
            return jsonify({'error': 'User not found'}), 404

        return jsonify({'message': 'User deactivated successfully'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@users_bp.errorhandler(ValidationError)
def handle_validation_error(e):
    """Handle Pydantic validation errors"""
    return jsonify({'error': 'Validation error', 'details': e.errors()}), 400
