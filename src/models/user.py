from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime
import json

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=True)  # Nullable for OAuth users
    
    # OAuth fields
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    facebook_id = db.Column(db.String(100), unique=True, nullable=True)
    
    # User preferences
    interests = db.Column(db.Text, nullable=True)  # JSON string of interests
    newsletter_format = db.Column(db.String(50), default='single')  # 'single' or 'by_topic'
    delivery_frequency = db.Column(db.String(100), default='daily')  # JSON string of days/times
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_interests(self):
        """Get user interests as a list"""
        if self.interests:
            return json.loads(self.interests)
        return []
    
    def set_interests(self, interests_list):
        """Set user interests from a list"""
        self.interests = json.dumps(interests_list)
    
    def get_delivery_schedule(self):
        """Get delivery schedule as dict"""
        if self.delivery_frequency:
            return json.loads(self.delivery_frequency)
        return {'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'], 'time': '08:00'}
    
    def set_delivery_schedule(self, schedule_dict):
        """Set delivery schedule from dict"""
        self.delivery_frequency = json.dumps(schedule_dict)
    
    def to_dict(self):
        """Convert user to dictionary for API responses"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'interests': self.get_interests(),
            'newsletter_format': self.newsletter_format,
            'delivery_schedule': self.get_delivery_schedule(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Newsletter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    topic = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime, nullable=True)
    is_saved = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('newsletters', lazy=True))
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'topic': self.topic,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'is_saved': self.is_saved
        }

class NewsArticle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    content = db.Column(db.Text, nullable=False)
    summary = db.Column(db.Text, nullable=True)
    source = db.Column(db.String(100), nullable=False)
    url = db.Column(db.String(500), nullable=False)
    topic = db.Column(db.String(100), nullable=False)
    political_bias = db.Column(db.String(20), nullable=True)  # 'left', 'center', 'right'
    published_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'summary': self.summary,
            'source': self.source,
            'url': self.url,
            'topic': self.topic,
            'political_bias': self.political_bias,
            'published_at': self.published_at.isoformat() if self.published_at else None
        }

