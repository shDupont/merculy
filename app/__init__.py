"""
Merculy Backend - Flask Application Factory
"""
from flask import Flask
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_apscheduler import APScheduler
import os
from .core.config import Config

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize CORS
    CORS(app, origins=app.config.get('ALLOWED_ORIGINS', ['*']))

    # Initialize Rate Limiting
    limiter = Limiter(
        app,
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"]
    )

    # Initialize Scheduler
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    # Register Blueprints
    from .routes.users import users_bp
    from .routes.newsletters import newsletters_bp
    from .routes.health import health_bp

    app.register_blueprint(health_bp, url_prefix='/v1')
    app.register_blueprint(users_bp, url_prefix='/v1')
    app.register_blueprint(newsletters_bp, url_prefix='/v1')

    # Register scheduler jobs
    from .scheduler.jobs import register_jobs
    register_jobs(scheduler)

    return app
