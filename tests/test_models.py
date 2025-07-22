"""
Merculy Backend - Models Tests
"""
import pytest
from datetime import datetime
from pydantic import ValidationError
from app.models.user import User, UserPreferences, Article, BiasType, NewsletterFormat

class TestUserModels:
    def test_user_preferences_defaults(self):
        prefs = UserPreferences()

        assert prefs.newsletter_format == NewsletterFormat.UNICA
        assert prefs.frequency_days == ["monday", "wednesday", "friday"]
        assert prefs.delivery_hour == 8
        assert prefs.delivery_timezone == "America/Sao_Paulo"
        assert prefs.topics == []
        assert prefs.custom_topics == []

    def test_user_creation_valid(self):
        user = User(
            user_id="test-user-123",
            email="test@example.com",
            name="Test User"
        )

        assert user.user_id == "test-user-123"
        assert user.email == "test@example.com"
        assert user.name == "Test User"
        assert user.is_active is True
        assert user.roles == ["user"]

    def test_user_invalid_email(self):
        with pytest.raises(ValidationError):
            User(
                user_id="test-user-123",
                email="invalid-email",
                name="Test User"
            )

    def test_article_creation(self):
        article = Article(
            title="Test Article",
            url="https://example.com/article",
            excerpt="Test excerpt",
            source="Test Source",
            published_at=datetime.now(),
            topic="Technology"
        )

        assert article.title == "Test Article"
        assert article.topic == "Technology"
        assert article.bias is None
        assert article.confidence_score == 0.0

    def test_article_with_bias(self):
        article = Article(
            title="Political Article",
            url="https://example.com/politics",
            excerpt="Political news",
            source="News Source",
            published_at=datetime.now(),
            topic="Politics",
            bias=BiasType.CENTRO,
            confidence_score=0.85
        )

        assert article.bias == BiasType.CENTRO
        assert article.confidence_score == 0.85
