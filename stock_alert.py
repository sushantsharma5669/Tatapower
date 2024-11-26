import yfinance as yf
import pandas as pd
import numpy as np
import requests
import logging
from datetime import datetime, timedelta
import pytz
import socket
import platform

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s: %(message)s',
    filename='market_insights.log'
)

class EnhancedMarketScanner:
    def __init__(self, capital=80000, max_trades=5):
        self.capital = capital
        self.max_trades = max_trades
        self.pushbullet_api_key = self.load_pushbullet_key()

    def load_pushbullet_key(self):
        """Load Pushbullet API Key from environment variable."""
        import os
        key = os.getenv("PUSHBULLET_API_KEY")
        if not key:
            logging.error("Pushbullet API Key not found in environment variables!")
            raise ValueError("Pushbullet API Key not found!")
        return key

    def fetch_historical_data(self, ticker, period='3mo', interval='1d'):
        """Enhanced data fetching with fallback mechanism."""
        try:
            stock = yf.Ticker(ticker)
            df = stock.history(period=period, interval=interval)

            if df is None or df.empty or len(df) < 10:
                logging.warning(f"Insufficient data for {ticker}")
                return None

            return df
        except Exception as e:
            logging.error(f"Data fetch error for {ticker}: {e}")
            return None

    def get_system_info(self):
        """Collect system and execution environment details."""
        return {
            'hostname': socket.gethostname(),
            'os': platform.system(),
            'os_version': platform.version(),
            'python_version': platform.python_version(),
            'processor': platform.processor()
        }

    def get_market_sentiment(self, df):
        """Analyze market sentiment based on recent price movements."""
        recent_returns = df['Close'].pct_change().tail(5)
        sentiment = {
            'trend': 'Bullish' if recent_returns.mean() > 0 else 'Bearish',
            'volatility': recent_returns.std() * 100,
            'consecutive_days_direction': 'Positive' if all(recent_returns > 0) else 'Negative' if all(recent_returns < 0) else 'Mixed'
        }
        return sentiment

    def generate_offline_recommendations(self):
        """Generate recommendations with enhanced insights."""
        recommended_stocks = [
            'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
            'INFY.NS', 'TCS.NS', 'ADANIGREEN.NS',
            'TATAMOTORS.NS', 'BAJFINANCE.NS',
            'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS'
        ]

        offline_alerts = []
        current_time = datetime.now(pytz.timezone('Asia/Kolkata'))

        for ticker in recommended_stocks:
            try:
                df = self.fetch_historical_data(ticker)

                if df is not None:
                    last_close = df['Close'].iloc[-1]
                    volatility = df['Close'].pct_change().std() * 100
                    avg_volume = df['Volume'].mean()

                    sentiment = self.get_market_sentiment(df)
                    system_info = self.get_system_info()

                    if (volatility > 2 and avg_volume > 500000):
                        recommendation = {
                            'timestamp': current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
                            'stock_name': ticker,
                            'last_close': last_close,
                            'volatility': round(volatility, 2),
                            'avg_volume': round(avg_volume, 0),
                            'potential_entry_range': [
                                round(last_close * 0.98, 2),
                                round(last_close * 1.02, 2)
                            ],
                            'market_sentiment': sentiment,
                            'system_details': system_info
                        }
                        offline_alerts.append(recommendation)

                if len(offline_alerts) >= self.max_trades:
                    break

            except Exception as e:
                logging.error(f"Offline processing error for {ticker}: {e}")

        return offline_alerts

    def send_offline_alerts(self, alerts):
        """Send comprehensive offline market insights."""
        url = "https://api.pushbullet.com/v2/pushes"
        headers = {
            "Access-Token": self.pushbullet_api_key,
            "Content-Type": "application/json"
        }

        alert_message = "🚀 Comprehensive Market Insights 📊\n"
        alert_message += f"🕒 Generated at: {alerts[0]['timestamp']}\n\n"

        for alert in alerts:
            alert_message += f"""
🔹 {alert['stock_name']}
   📈 Last Close: ₹{alert['last_close']}
   📊 Volatility: {alert['volatility']}%
   📊 Avg Volume: {alert['avg_volume']}
   🎯 Potential Entry: ₹{alert['potential_entry_range'][0]} - ₹{alert['potential_entry_range'][1]}

   📊 Market Sentiment:
   • Trend: {alert['market_sentiment']['trend']}
   • Volatility: {round(alert['market_sentiment']['volatility'], 2)}%
   • Recent Movement: {alert['market_sentiment']['consecutive_days_direction']}

   💻 Execution Environment:
   • Hostname: {alert['system_details']['hostname']}
   • OS: {alert['system_details']['os']} {alert['system_details']['os_version']}
   • Python: {alert['system_details']['python_version']}
   • Processor: {alert['system_details']['processor']}

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
            "title": f"Market Insights - {datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %b %Y')}",
            "body": alert_message
        }

        try:
            response = requests.post(url, json=payload, headers=headers)
            logging.info("Comprehensive market alerts sent successfully")
        except Exception as e:
            logging.error(f"Alert sending failed: {e}")

def main():
    scanner = EnhancedMarketScanner()

    logging.info(f"Script execution started at {datetime.now()}")

    try:
        offline_recommendations = scanner.generate_offline_recommendations()

        if offline_recommendations:
            scanner.send_offline_alerts(offline_recommendations)
        else:
            logging.warning("No recommendations generated")

    except Exception as e:
        logging.error(f"Unexpected error in main execution: {e}")

if __name__ == "__main__":
    main()
