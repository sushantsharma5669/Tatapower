import yfinance as yf
import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime, timedelta
import pytz
import socket
import platform
from typing import Dict, List, Optional
from oauth_handler import UPStoxAuth
from error_handler import TradingBotError

class TradingBot:
    def __init__(self, capital=80000, max_trades=5):
        self.capital = capital
        self.max_trades = max_trades
        self.auth_handler = UPStoxAuth()
        self.pushbullet_api_key = self.auth_handler.get_pushbullet_key()
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.risk_reward_ratio = 2
        self.accuracy_threshold = 0.75
        self.holding_duration = "2-3 hours"
        self.setup_logging()

    def setup_logging(self):
        """Configure logging system"""
        logging.basicConfig(
            filename='logs/trading_bot.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def get_system_info(self):
        """Collect system and execution environment details"""
        return {
            'hostname': socket.gethostname(),
            'os': platform.system(),
            'os_version': platform.version(),
            'python_version': platform.python_version(),
            'processor': platform.processor()
        }

    def fetch_historical_data(self, ticker: str, period='3mo', interval='1d') -> Optional[pd.DataFrame]:
        """Enhanced data fetching with fallback mechanism"""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)
            
            if df is None or df.empty or len(df) < 10:
                self.logger.warning(f"Insufficient data for {ticker}")
                return None
            
            return df
        except Exception as e:
            self.logger.error(f"Data fetch error for {ticker}: {e}")
            return None

    def get_market_sentiment(self, df: pd.DataFrame) -> Dict:
        """Analyze market sentiment based on recent price movements"""
        recent_returns = df['Close'].pct_change().tail(5)
        sentiment = {
            'trend': 'Bullish' if recent_returns.mean() > 0 else 'Bearish',
            'volatility': recent_returns.std() * 100,
            'consecutive_days_direction': 'Positive' if all(recent_returns > 0) else 'Negative' if all(recent_returns < 0) else 'Mixed'
        }
        return sentiment

    def calculate_accuracy(self, df: pd.DataFrame) -> float:
        """Calculate strategy accuracy based on historical data"""
        try:
            df['Signal'] = np.where(
                (df['Close'].pct_change() > 0) & 
                (df['Volume'] > df['Volume'].mean()), 1, 0
            )
            
            df['Profitable'] = np.where(
                df['Signal'].shift(1) == 1,
                df['Close'] > df['Close'].shift(1),
                False
            )
            
            accuracy = df['Profitable'].mean()
            return round(accuracy * 100, 2)
        except Exception as e:
            self.logger.error(f"Error calculating accuracy: {e}")
            return 0.0

    def get_entry_conditions(self, df: pd.DataFrame) -> Dict:
        """Calculate entry conditions and timing"""
        last_row = df.iloc[-1]
        current_time = datetime.now(self.ist_timezone)
        
        entry_conditions = {
            'entry_time': current_time.strftime("%H:%M:%S"),
            'entry_price': last_row['Close'],
            'target_price': round(last_row['Close'] * (1 + 0.02 * self.risk_reward_ratio), 2),
            'stop_loss': round(last_row['Close'] * (1 - 0.02), 2),
            'accuracy': self.calculate_accuracy(df),
            'holding_duration': self.holding_duration
        }
        
        return entry_conditions

    def generate_trading_signals(self) -> List[Dict]:
        """Generate comprehensive trading signals"""
        recommended_stocks = [
            'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
            'INFY.NS', 'TCS.NS', 'ADANIGREEN.NS',
            'TATAMOTORS.NS', 'BAJFINANCE.NS',
            'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS'
        ]
        
        trading_signals = []
        current_time = datetime.now(self.ist_timezone)

        for ticker in recommended_stocks:
            try:
                df = self.fetch_historical_data(ticker)
                if df is not None:
                    entry_conditions = self.get_entry_conditions(df)
                    
                    if entry_conditions['accuracy'] >= self.accuracy_threshold:
                        signal = {
                            'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                            'stock_name': ticker,
                            'entry_conditions': entry_conditions,
                            'market_sentiment': self.get_market_sentiment(df),
                            'system_details': self.get_system_info()
                        }
                        trading_signals.append(signal)

                if len(trading_signals) >= self.max_trades:
                    break

            except Exception as e:
                self.logger.error(f"Error processing {ticker}: {e}")

        return trading_signals

    def send_alerts(self, signals: List[Dict]):
        """Send comprehensive trading alerts"""
        url = "https://api.pushbullet.com/v2/pushes"
        headers = {
            "Access-Token": self.pushbullet_api_key,
            "Content-Type": "application/json"
        }

        alert_message = "🚀 Trading Signals & Market Insights 📊\n"
        alert_message += f"🕒 Generated at: {signals[0]['timestamp']}\n\n"

        for signal in signals:
            entry_conditions = signal['entry_conditions']
            alert_message += f"""
🔹 {signal['stock_name']}
   
   ⏰ Entry Time: {entry_conditions['entry_time']}
   📈 Entry Price: ₹{entry_conditions['entry_price']}
   🎯 Target: ₹{entry_conditions['target_price']}
   🛑 Stop Loss: ₹{entry_conditions['stop_loss']}
   ✅ Strategy Accuracy: {entry_conditions['accuracy']}%
   ⌛ Holding Duration: {entry_conditions['holding_duration']}

   📊 Market Sentiment:
   • Trend: {signal['market_sentiment']['trend']}
   • Volatility: {round(signal['market_sentiment']['volatility'], 2)}%
   • Recent Movement: {signal['market_sentiment']['consecutive_days_direction']}

   ---
            """

        risk_advisory = "\n⚠️ Risk Advisory:\n" + \
            "• This is an automated recommendation\n" + \
            "• Please conduct your own research\n" + \
            "• Risk management is crucial\n" + \
            "• Past performance doesn't guarantee future results"

        alert_message += risk_advisory

        payload = {
            "type": "note",
            "title": f"Trading Signals - {datetime.now(self.ist_timezone).strftime('%d %b %Y')}",
            "body": alert_message
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                self.logger.info("Trading alerts sent successfully")
            else:
                self.logger.error(f"Alert sending failed with status code: {response.status_code}")
        except Exception as e:
            self.logger.error(f"Alert sending failed: {e}")

    def execute_strategy(self):
        """Execute complete trading strategy"""
        try:
            self.logger.info(f"Starting trading strategy execution at {datetime.now(self.ist_timezone)}")
            
            # Generate signals
            signals = self.generate_trading_signals()
            
            # Send alerts if signals are generated
            if signals:
                self.send_alerts(signals)
                self.logger.info(f"Generated {len(signals)} trading signals")
            else:
                self.logger.warning("No trading signals generated")
            
        except Exception as e:
            self.logger.error(f"Strategy execution failed: {e}")
            raise TradingBotError(f"Strategy execution failed: {str(e)}")

if __name__ == "__main__":
    bot = TradingBot()
    bot.execute_strategy()