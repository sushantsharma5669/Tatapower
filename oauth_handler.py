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

    def place_order(self, order_params: Dict) -> Dict:
        """
        Place an order using Upstox API V2 according to official documentation
        """
        try:
            if not self.access_token:
                self.authenticate()

            headers = {
                'accept': 'application/json',
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {self.access_token}'
            }

            # Transform params to match Upstox API requirements
            formatted_order = {
                'quantity': order_params['quantity'],
                'product': order_params.get('product', 'I'),  # I for Intraday
                'validity': order_params.get('validity', 'DAY'),
                'price': order_params['price'],
                'instrument_token': f"NSE_EQ|{order_params['symbol']}",
                'order_type': order_params['order_type'],
                'transaction_type': order_params['transaction_type'],
                'disclosed_quantity': order_params.get('disclosed_quantity', 0),
                'trigger_price': order_params.get('trigger_price', 0),
                'is_amo': order_params.get('is_amo', False)
            }

            response = requests.post(
                f"{self.base_url}/order/place",
                headers=headers,
                json=formatted_order
            )

            if response.status_code == 200:
                self.logger.info("Order placed successfully")
                return response.json()
            else:
                error_message = f"Order placement failed: {response.text}"
                self.logger.error(error_message)
                raise OrderPlacementError(error_message)

        except Exception as e:
            self.logger.error(f"Order placement error: {str(e)}")
            raise OrderPlacementError(f"Failed to place order: {str(e)}")

# trading_bot.py
class TradingBot:
    def place_trade(self, signal: Dict) -> Dict:
        """
        Place a trade based on the generated signal
        """
        try:
            # Calculate quantity based on risk management
            quantity = self.calculate_position_size(signal)

            # Prepare main order parameters
            order_params = {
                'symbol': signal['stock_name'].replace('.NS', ''),
                'quantity': quantity,
                'price': signal['entry_conditions']['entry_price'],
                'transaction_type': 'BUY' if signal['market_sentiment']['trend'] == 'Bullish' else 'SELL',
                'order_type': 'LIMIT',
                'product': 'I',  # Intraday
                'validity': 'DAY',
                'disclosed_quantity': 0,
                'trigger_price': signal['entry_conditions']['entry_price'],
                'is_amo': False
            }

            # Place the main order
            order_response = self.auth_handler.place_order(order_params)
            self.logger.info(f"Main order placed: {order_response}")

            if order_response.get('status') == 'success':
                # Place stop loss order
                sl_params = order_params.copy()
                sl_params.update({
                    'price': signal['entry_conditions']['stop_loss'],
                    'transaction_type': 'SELL' if order_params['transaction_type'] == 'BUY' else 'BUY',
                    'order_type': 'SL',
                    'trigger_price': signal['entry_conditions']['stop_loss']
                })
                
                sl_response = self.auth_handler.place_order(sl_params)
                self.logger.info(f"Stop loss order placed: {sl_response}")

                # Place target order
                target_params = order_params.copy()
                target_params.update({
                    'price': signal['entry_conditions']['target_price'],
                    'transaction_type': 'SELL' if order_params['transaction_type'] == 'BUY' else 'BUY',
                    'order_type': 'LIMIT'
                })
                
                target_response = self.auth_handler.place_order(target_params)
                self.logger.info(f"Target order placed: {target_response}")

            return {
                'main_order': order_response,
                'stop_loss': sl_response if 'sl_response' in locals() else None,
                'target': target_response if 'target_response' in locals() else None
            }

        except Exception as e:
            self.logger.error(f"Trade placement failed: {e}")
            raise OrderPlacementError(f"Failed to place trade: {str(e)}")