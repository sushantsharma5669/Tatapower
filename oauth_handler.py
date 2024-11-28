# oauth_handler.py
import os
import logging
import requests
from error_handler import AuthenticationError
from typing import Dict

class UpstoxAuth:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.api_key = self.get_api_key()
        self.api_secret = self.get_api_secret()
        self.access_token = None
        self.base_url = "https://api.upstox.com/v2"

    def get_api_key(self) -> str:
        api_key = os.getenv('UPSTOX_API_KEY')
        if not api_key:
            self.logger.error("Upstox API key not found")
            raise AuthenticationError("UPSTOX_API_KEY not found in environment variables")
        return api_key

    def get_api_secret(self) -> str:
        api_secret = os.getenv('UPSTOX_API_SECRET')
        if not api_secret:
            self.logger.error("Upstox API secret not found")
            raise AuthenticationError("UPSTOX_API_SECRET not found in environment variables")
        return api_secret

    def get_pushbullet_key(self) -> str:
        key = os.getenv('PUSHBULLET_API_KEY')
        if not key:
            self.logger.error("Pushbullet API key not found")
            raise AuthenticationError("PUSHBULLET_API_KEY not found in environment variables")
        return key

    def authenticate(self) -> None:
        """Authenticate using Upstox API v2"""
        try:
            auth_url = f"{self.base_url}/login/authorization/token"
            
            headers = {
                'accept': 'application/json',
                'Api-Version': '2.0'
            }
            
            payload = {
                'api_key': self.api_key,
                'api_secret': self.api_secret
            }

            self.logger.info("Initiating authentication with Upstox")
            response = requests.post(auth_url, headers=headers, json=payload)

            if response.status_code != 200:
                self.logger.error(f"Authentication failed with status {response.status_code}")
                self.logger.error(f"Response: {response.text}")
                raise AuthenticationError(f"Authentication failed: {response.text}")

            token_data = response.json()
            self.access_token = token_data.get('access_token')

            if not self.access_token:
                raise AuthenticationError("No access token received in response")

            self.logger.info("Successfully authenticated with Upstox")

        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")

    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        if not self.access_token:
            self.authenticate()

        return {
            'accept': 'application/json',
            'Api-Version': '2.0',
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }