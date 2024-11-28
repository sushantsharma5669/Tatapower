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

    def authenticate(self) -> None:
        """Authenticate using API credentials"""
        try:
            headers = {
                'accept': 'application/json',
                'Api-Version': '2.0',
                'x-api-key': self.api_key
            }

            response = requests.post(
                f"{self.base_url}/login/authorization/token",
                headers=headers,
                json={'api_secret': self.api_secret}
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