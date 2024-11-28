import os
import logging
import requests
import time
from error_handler import AuthenticationError
from typing import Dict, Optional

class UpstoxAuth:
    def __init__(self, test_mode: bool = False):
        self.logger = logging.getLogger(__name__)
        self.api_key = self.get_api_key()
        self.api_secret = self.get_api_secret()
        self.access_token = None
        self.base_url = "https://api.upstox.com/v2"
        self.test_mode = test_mode
        
        # Rate limiting parameters
        self.last_api_call = 0
        self.api_call_limit = 5  # calls per minute
        self.retry_count = 0
        self.max_retries = 3

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

    def _rate_limit(self):
        """Implement rate limiting for API calls"""
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call
        
        if time_since_last_call < (60 / self.api_call_limit):
            sleep_time = (60 / self.api_call_limit) - time_since_last_call
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()

    def authenticate(self) -> None:
        """Authenticate with Upstox API with proper error handling and retries"""
        if self.test_mode:
            self.logger.info("Running in test mode - skipping actual API authentication")
            self.access_token = "test_mode_token"
            return

        try:
            self._rate_limit()

            headers = {
                'accept': 'application/json',
                'Api-Version': '2.0'
            }
            
            data = {
                'api_key': self.api_key,
                'api_secret': self.api_secret
            }

            response = requests.post(
                f"{self.base_url}/login/authorization/token",
                headers=headers,
                json=data
            )

            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                
                if not self.access_token:
                    raise AuthenticationError("No access token received in response")
                    
                self.logger.info("Successfully authenticated with Upstox")
                self.retry_count = 0  # Reset retry count on success
                
            else:
                self._handle_auth_error(response)

        except Exception as e:
            self.logger.error(f"Authentication error: {str(e)}")
            raise AuthenticationError(f"Failed to authenticate: {str(e)}")

    def _handle_auth_error(self, response) -> None:
        """Handle authentication errors with exponential backoff retry"""
        self.retry_count += 1
        
        if self.retry_count >= self.max_retries:
            raise AuthenticationError(
                f"Max retries ({self.max_retries}) exceeded. Last error: {response.text}"
            )
            
        retry_delay = min(2 ** self.retry_count, 60)  # Max 60 seconds delay
        self.logger.warning(
            f"Authentication failed. Retrying in {retry_delay} seconds... "
            f"(Attempt {self.retry_count} of {self.max_retries})"
        )
        
        time.sleep(retry_delay)
        self.authenticate()

    def get_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        if not self.access_token and not self.test_mode:
            self.authenticate()

        return {
            'accept': 'application/json',
            'Api-Version': '2.0',
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }

    def check_token_validity(self) -> bool:
        """Check if the current access token is valid"""
        if self.test_mode:
            return True
            
        if not self.access_token:
            return False

        try:
            response = requests.get(
                f"{self.base_url}/user/profile",
                headers=self.get_headers()
            )
            return response.status_code == 200
        except:
            return False