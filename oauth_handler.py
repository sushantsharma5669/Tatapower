import os
import logging
from error_handler import AuthenticationError

class UPStoxAuth:
    def __init__(self):
        self.api_key = self.get_api_key()
        self.api_secret = self.get_api_secret()
        self.redirect_uri = self.get_redirect_uri()
        self.logger = logging.getLogger(__name__)

    def get_api_key(self):
        """Retrieve API key from environment variables"""
        api_key = os.getenv('UPSTOX_API_KEY')
        if not api_key:
            raise AuthenticationError("UPSTOX_API_KEY not found in environment variables")
        return api_key

    def get_api_secret(self):
        """Retrieve API secret from environment variables"""
        api_secret = os.getenv('UPSTOX_API_SECRET')
        if not api_secret:
            raise AuthenticationError("UPSTOX_API_SECRET not found in environment variables")
        return api_secret

    def get_redirect_uri(self):
        """Retrieve redirect URI from environment variables"""
        redirect_uri = os.getenv('UPSTOX_REDIRECT_URI')
        if not redirect_uri:
            raise AuthenticationError("UPSTOX_REDIRECT_URI not found in environment variables")
        return redirect_uri

    def get_pushbullet_key(self):
        """Retrieve Pushbullet API key from environment variables"""
        key = os.getenv('PUSHBULLET_API_KEY')
        if not key:
            raise AuthenticationError("PUSHBULLET_API_KEY not found in environment variables")
        return key