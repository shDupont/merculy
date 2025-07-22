"""
Merculy Backend - Authentication Tests
"""
import pytest
from unittest.mock import patch, MagicMock
from app.auth.azure_b2c import AzureB2CAuth
import jwt

class TestAzureB2CAuth:
    def setup_method(self):
        self.auth = AzureB2CAuth()

    @patch('app.auth.azure_b2c.requests.get')
    def test_get_jwks_success(self, mock_get):
        # Mock OIDC config response
        oidc_mock = MagicMock()
        oidc_mock.json.return_value = {
            'jwks_uri': 'https://test.com/jwks'
        }
        oidc_mock.raise_for_status.return_value = None

        # Mock JWKS response
        jwks_mock = MagicMock()
        jwks_mock.json.return_value = {
            'keys': [
                {
                    'kid': 'test-key-id',
                    'kty': 'RSA',
                    'n': 'test-modulus',
                    'e': 'AQAB'
                }
            ]
        }
        jwks_mock.raise_for_status.return_value = None

        mock_get.side_effect = [oidc_mock, jwks_mock]

        result = self.auth.get_jwks()

        assert 'keys' in result
        assert len(result['keys']) == 1
        assert result['keys'][0]['kid'] == 'test-key-id'

    def test_validate_token_invalid_format(self):
        result = self.auth.validate_token('invalid-token')
        assert result is None

    @patch.object(AzureB2CAuth, 'get_signing_key')
    @patch('jwt.decode')
    def test_validate_token_success(self, mock_jwt_decode, mock_get_key):
        mock_get_key.return_value = 'mock-key'
        mock_jwt_decode.return_value = {
            'sub': 'test-user-id',
            'email': 'test@example.com',
            'name': 'Test User'
        }

        # Create a mock token with proper header
        with patch('jwt.get_unverified_header') as mock_header:
            mock_header.return_value = {'kid': 'test-key-id'}

            result = self.auth.validate_token('valid.jwt.token')

            assert result is not None
            assert result['sub'] == 'test-user-id'
            assert result['email'] == 'test@example.com'
