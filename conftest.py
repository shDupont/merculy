"""
Merculy Backend - Test Configuration
"""
import pytest
from unittest.mock import Mock
from app import create_app

@pytest.fixture
def app():
    """Create application for testing"""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SECRET_KEY': 'test-key',
        'AZURE_CLIENT_ID': 'test-client-id',
        'COSMOS_URI': 'https://test-cosmos.documents.azure.com:443/',
        'COSMOS_KEY': 'test-key',
        'GEMINI_API_KEY': 'test-gemini-key',
        'SENDGRID_API_KEY': 'test-sendgrid-key'
    })

    return app

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def mock_cosmos_service():
    """Mock Cosmos DB service"""
    mock = Mock()
    mock.get_user.return_value = None
    mock.create_user.return_value = Mock()
    mock.update_user.return_value = Mock()
    mock.list_active_users.return_value = []
    return mock

@pytest.fixture
def valid_jwt_token():
    """Mock valid JWT token"""
    return "eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIsImtpZCI6InRlc3Qta2V5In0.eyJzdWIiOiJ0ZXN0LXVzZXItaWQiLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJuYW1lIjoiVGVzdCBVc2VyIiwiZXhwIjoxOTk5OTk5OTk5fQ.signature"

@pytest.fixture
def auth_headers(valid_jwt_token):
    """Authorization headers with valid token"""
    return {
        'Authorization': f'Bearer {valid_jwt_token}',
        'Content-Type': 'application/json'
    }
