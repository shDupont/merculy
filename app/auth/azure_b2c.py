"""
Merculy Backend - Azure AD B2C Authentication
"""
import jwt
import requests
from functools import wraps
from flask import request, jsonify, current_app
from typing import Dict, Optional
import time
from ..core.config import Config

class AzureB2CAuth:
    def __init__(self):
        self.config = Config()
        self._jwks_cache = None
        self._jwks_cache_expires = 0

    def get_jwks(self) -> Dict:
        """Get JWKS from Azure B2C with caching"""
        current_time = time.time()

        if self._jwks_cache and current_time < self._jwks_cache_expires:
            return self._jwks_cache

        try:
            # Get OpenID configuration
            oidc_response = requests.get(self.config.AZURE_OPENID_CONFIG)
            oidc_response.raise_for_status()
            oidc_config = oidc_response.json()

            # Get JWKS
            jwks_response = requests.get(oidc_config['jwks_uri'])
            jwks_response.raise_for_status()
            jwks = jwks_response.json()

            # Cache for 1 hour
            self._jwks_cache = jwks
            self._jwks_cache_expires = current_time + 3600

            return jwks
        except Exception as e:
            current_app.logger.error(f"Error fetching JWKS: {str(e)}")
            raise

    def get_signing_key(self, kid: str):
        """Get signing key from JWKS"""
        jwks = self.get_jwks()

        for key in jwks.get('keys', []):
            if key.get('kid') == kid:
                return jwt.algorithms.RSAAlgorithm.from_jwk(key)

        raise ValueError(f"Unable to find key with kid: {kid}")

    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate JWT token from Azure B2C"""
        try:
            # Decode header to get kid
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get('kid')

            if not kid:
                return None

            # Get signing key
            signing_key = self.get_signing_key(kid)

            # Validate token
            payload = jwt.decode(
                token,
                signing_key,
                algorithms=['RS256'],
                audience=self.config.AZURE_CLIENT_ID,
                options={"verify_exp": True, "verify_aud": True}
            )

            return payload

        except jwt.ExpiredSignatureError:
            current_app.logger.warning("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            current_app.logger.warning(f"Invalid token: {str(e)}")
            return None
        except Exception as e:
            current_app.logger.error(f"Token validation error: {str(e)}")
            return None

# Global auth instance
azure_auth = AzureB2CAuth()
