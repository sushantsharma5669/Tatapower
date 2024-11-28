import os
import logging
from error_handler import AuthenticationError
import requests
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
        try:
            headers = {
                'accept': 'application/json',
                'Api-Version': '2.0',
                'x-api-key': self.api_key
            }

            data = {
                'api_secret': self.api_secret
            }

            response = requests.post(
                f"{self.base_url}/login/authorization/token",
                headers=headers,
                json=data
            )

            if response.status_code != 200:
                raise AuthenticationError(f"Authentication failed: {response.text}")

            self.access_token = response.json().get('access_token')
            if not self.access_token:
                raise AuthenticationError("No access token received")

            self.logger.info("Successfully authenticated with Upstox")

        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")