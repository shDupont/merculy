"""
Merculy Backend - Health Check Routes
"""
from flask import Blueprint, jsonify
from datetime import datetime

health_bp = Blueprint('health', __name__)

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@health_bp.route('/health/detailed', methods=['GET'])
def detailed_health_check():
    """Detailed health check with service status"""
    services = {
        'database': 'unknown',
        'sendgrid': 'unknown',
        'gemini': 'unknown'
    }

    overall_status = 'healthy'

    # Check Cosmos DB
    try:
        from ..services.cosmos import cosmos_service
        if cosmos_service.client:
            services['database'] = 'healthy'
        else:
            services['database'] = 'unhealthy'
            overall_status = 'degraded'
    except Exception:
        services['database'] = 'unhealthy'
        overall_status = 'degraded'

    # Check SendGrid (basic config check)
    try:
        from ..core.config import Config
        config = Config()
        if config.SENDGRID_API_KEY:
            services['sendgrid'] = 'configured'
        else:
            services['sendgrid'] = 'not_configured'
    except Exception:
        services['sendgrid'] = 'error'

    # Check Gemini (basic config check)
    try:
        from ..core.config import Config
        config = Config()
        if config.GEMINI_API_KEY:
            services['gemini'] = 'configured'
        else:
            services['gemini'] = 'not_configured'
    except Exception:
        services['gemini'] = 'error'

    return jsonify({
        'status': overall_status,
        'timestamp': datetime.utcnow().isoformat(),
        'services': services
    })
