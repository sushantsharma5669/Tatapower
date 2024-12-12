import pandas as pd
import numpy as np
import logging
import json
import os
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import yfinance as yf
from pushbullet import Pushbullet
import requests
from threading import Lock
import warnings
warnings.filterwarnings('ignore')

# Configuration dictionary (embedded in code for Colab)
CONFIG = {
    "trading_params": {
        "underlying": "^NSEI",
        "option_types": ["CE", "PE"],
        "strike_range_percent": 3,
        "lot_size": 50
    },
    "strategy_params": {
        "min_vix": 12,
        "max_vix": 30,
        "min_score": 3,
        "cooldown_minutes": 60
    },
    "risk_management": {
        "max_loss_per_trade": 5000,
        "stop_loss_percent": 50,
        "target_profit_percent": 100
    },
    "alerts": {
        "pushbullet_token": "o.sdZ1bFEeGj2tWPiwYeIqkwK0LQ0RCO4T",  # Add your token here
        "telegram_token": "7750303719:AAFzrIXkNXx10EXb-RRN-b5mgSFAU_XtUZU",    # Add your token here
       "telegram_chat_id": "7721014575"   # Add your chat ID here
    }
}

class AlertSystem:
    def __init__(self, config: dict):
        self.config = config
        self.pushbullet = self._setup_pushbullet()
        self.telegram_base_url = f"https://api.telegram.org/bot{config.get('telegram_token', '')}"

    def _setup_pushbullet(self) -> Optional[Pushbullet]:
        try:
            if self.config.get('pushbullet_token'):
                return Pushbullet(self.config['pushbullet_token'])
        except Exception as e:
            print(f"Pushbullet setup error: {e}")
        return None

    def send_telegram_message(self, message: str):
        try:
            if self.config.get('telegram_token') and self.config.get('telegram_chat_id'):
                url = f"{self.telegram_base_url}/sendMessage"
                data = {
                    "chat_id": self.config['telegram_chat_id'],
                    "text": message,
                    "parse_mode": "HTML"
                }
                response = requests.post(url, data=data)
                if not response.ok:
                    print(f"Telegram API error: {response.text}")
        except Exception as e:
            print(f"Telegram send error: {e}")

    def send_pushbullet_alert(self, title: str, message: str):
        try:
            if self.pushbullet:
                self.pushbullet.push_note(title, message)
        except Exception as e:
            print(f"Pushbullet send error: {e}")

    def send_alert(self, signal: Dict):
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            message = (
                f"🔔 NIFTY Options Signal Alert 1 \n\n"
                f"💰 Price Action:\n"
                f"NIFTY Spot: {signal['spot']:.2f}\n"
                f"Strike: {signal['strike']}\n"
                f"Option: {signal['type']}\n"
                f"Premium: {signal['premium']:.2f}\n\n"
                f"📈 Trade Setup:\n"
                f"Action: {signal['direction']}\n"
                f"Stop Loss: {signal['stop_loss']:.2f}\n"
                f"Target: {signal['target']:.2f}\n"
                f"Score: {signal['score']}/5\n\n"
                f"📊 Analysis:\n"
                f"Distance from Spot: {signal['distance']:.2f}%\n"
                f"VIX: {signal.get('vix', 0):.2f}\n\n"
                f"💡 Trade Reasons:\n"
            )

            for reason in signal['reasons']:
                message += f"• {reason}\n"

            print(message)  # Print to Colab output

            title = f"NIFTY {signal['type']} - {signal['direction']}"

            self.send_pushbullet_alert(title, message)
            self.send_telegram_message(message)

        except Exception as e:
            print(f"Error sending alert: {e}")

class NiftyOptionsTrader:
    def __init__(self):
        # Use embedded config for Colab
        self.config = CONFIG
        self.setup_logging()
        self.alert_system = AlertSystem(self.config.get('alerts', {}))
        self.nifty_spot = None
        self.vix = None
        self.last_alert_time = {}

    def setup_logging(self):
        # Simplified logging for Colab
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('NiftyOptionsTrader')

    def get_nifty_data(self) -> bool:
        try:
            nifty = yf.Ticker("^NSEI")
            nifty_data = nifty.history(period="1d")
            if not nifty_data.empty:
                self.nifty_spot = nifty_data['Close'].iloc[-1]

                vix = yf.Ticker("^INDIAVIX")
                vix_data = vix.history(period="1d")
                self.vix = vix_data['Close'].iloc[-1] if not vix_data.empty else 15

                print(f"Current NIFTY: {self.nifty_spot:.2f} | VIX: {self.vix:.2f}")
                return True
        except Exception as e:
            print(f"Error fetching NIFTY data: {e}")
        return False

    def analyze_strike(self, strike: float, opt_type: str) -> Optional[Dict]:
        try:
            strike_key = f"{strike}_{opt_type}"
            if strike_key in self.last_alert_time:
                last_time = self.last_alert_time[strike_key]
                cooldown = self.config['strategy_params']['cooldown_minutes']
                if (datetime.now() - last_time).seconds < (cooldown * 60):
                    return None

            distance_from_spot = abs((strike - self.nifty_spot) / self.nifty_spot * 100)
            if distance_from_spot > 3:
                return None

            score = 0
            reasons = []
            direction = None

            # Premium calculations
            itm_premium = abs(self.nifty_spot - strike) + (self.nifty_spot * 0.01)
            otm_premium = (self.nifty_spot * 0.005) * (1 - distance_from_spot/3)

            # ATM analysis
            if distance_from_spot <= 0.5:
                score += 2
                reasons.append("ATM Option - High liquidity")
                premium = self.nifty_spot * 0.015

            # Option specific analysis
            if opt_type == "CE":
                if strike <= self.nifty_spot:
                    premium = itm_premium
                    if self.vix > 18:
                        score += 1
                        reasons.append("ITM Call - High VIX")
                        direction = "SELL"
                else:
                    premium = otm_premium
                    if self.vix < 15:
                        score += 1
                        reasons.append("OTM Call - Low VIX")
                        direction = "BUY"
            else:
                if strike >= self.nifty_spot:
                    premium = itm_premium
                    if self.vix > 18:
                        score += 1
                        reasons.append("ITM Put - High VIX")
                        direction = "SELL"
                else:
                    premium = otm_premium
                    if self.vix < 15:
                        score += 1
                        reasons.append("OTM Put - Low VIX")
                        direction = "BUY"

            if distance_from_spot < 2:
                score += 1
                reasons.append("High liquidity zone")

            min_score = self.config['strategy_params']['min_score']
            if score >= min_score:
                signal = {
                    'strike': strike,
                    'type': opt_type,
                    'direction': direction,
                    'score': score,
                    'reasons': reasons,
                    'spot': self.nifty_spot,
                    'vix': self.vix,
                    'distance': distance_from_spot,
                    'premium': round(premium, 2),
                    'stop_loss': round(premium * 1.5, 2),
                    'target': round(premium * 0.5, 2)
                }

                self.last_alert_time[strike_key] = datetime.now()
                return signal

            return None

        except Exception as e:
            print(f"Error analyzing strike {strike}: {e}")
            return None

    def run_once(self):
        """Single scan iteration for Colab"""
        print("\n=== Starting NIFTY Options Scan ===")

        if self.get_nifty_data():
            opportunities = []

            range_percent = self.config['trading_params']['strike_range_percent']
            min_strike = self.nifty_spot * (1 - range_percent/100)
            max_strike = self.nifty_spot * (1 + range_percent/100)

            min_strike = round(min_strike/50) * 50
            max_strike = round(max_strike/50) * 50

            for strike in range(int(min_strike), int(max_strike)+50, 50):
                for opt_type in self.config['trading_params']['option_types']:
                    signal = self.analyze_strike(strike, opt_type)
                    if signal:
                        opportunities.append(signal)

            if opportunities:
                opportunities.sort(key=lambda x: x['score'], reverse=True)
                top_opportunities = opportunities[:1]

                print(f"\nFound {len(top_opportunities)} strong opportunities:")
                for opp in top_opportunities:
                    self.alert_system.send_alert(opp)
            else:
                print("\nNo significant opportunities found")

        print("\n=== Scan Complete ===")

# Create and run the trader
trader = NiftyOptionsTrader()
trader.run_once()  # Run single scan

# To run continuous scanning (will run until stopped):
"""
while True:
    trader.run_once()
    time.sleep(60)  # Wait 1 minute between scans
"""
