# oauth_handler.py
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

    def authenticate(self) -> None:
        """Authenticate using API key and secret"""
        try:
            headers = {
                'accept': 'application/json',
                'Api-Version': '2.0',
                'x-api-key': self.api_key,
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

    def get_request_headers(self) -> Dict[str, str]:
        """Get headers for API requests"""
        if not self.access_token:
            self.authenticate()

        return {
            'accept': 'application/json',
            'Api-Version': '2.0',
            'x-api-key': self.api_key,
            'Authorization': f'Bearer {self.access_token}'
        }

    def place_order(self, order_params: Dict) -> Dict:
        """Place an order using the API"""
        try:
            headers = self.get_request_headers()
            response = requests.post(
                f"{self.base_url}/order/place",
                headers=headers,
                json=order_params
            )

            if response.status_code != 200:
                raise OrderPlacementError(f"Order placement failed: {response.text}")

            return response.json()

        except Exception as e:
            self.logger.error(f"Order placement error: {str(e)}")
            raise OrderPlacementError(f"Failed to place order: {str(e)}")

    def get_market_data(self, symbol: str) -> Dict:
        """Fetch market data for a symbol"""
        try:
            headers = self.get_request_headers()
            response = requests.get(
                f"{self.base_url}/market-quote/quotes",
                headers=headers,
                params={'symbol': symbol}
            )

            if response.status_code != 200:
                raise MarketDataError(f"Failed to fetch market data: {response.text}")

            return response.json()

        except Exception as e:
            self.logger.error(f"Market data fetch error: {str(e)}")
            raise MarketDataError(f"Failed to fetch market data: {str(e)}")