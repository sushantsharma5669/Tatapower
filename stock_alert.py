import os
import yfinance as yf
import requests
from datetime import datetime, timedelta

# Pushbullet API Key (Environment variable for security)
PUSHBULLET_API_KEY = os.getenv("PUSHBULLET_API_KEY")

# Stock symbols to monitor (NSE/BSE symbols or global tickers)
STOCK_SYMBOLS = ["TATAPOWER.NS", "RELIANCE.NS", "INFY.NS"]

# Maximum alerts per day
MAX_ALERTS = 20
alerts_sent_today = 0
alert_reset_time = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)

# Trade conditions (dynamic conditions can be added here)
TRADE_CONDITIONS = {
    "TATAPOWER.NS": {"buy": 414, "target_buy": 425, "stoploss_buy": 408, "sell": 408, "target_sell": 402, "stoploss_sell": 414},
    "RELIANCE.NS": {"buy": 2450, "target_buy": 2500, "stoploss_buy": 2400, "sell": 2400, "target_sell": 2350, "stoploss_sell": 2450},
    "INFY.NS": {"buy": 1400, "target_buy": 1450, "stoploss_buy": 1350, "sell": 1350, "target_sell": 1300, "stoploss_sell": 1400},
}

# Pushbullet alert function
def send_pushbullet_alert(title, message):
    """Send alerts to Pushbullet."""
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {"Access-Token": PUSHBULLET_API_KEY, "Content-Type": "application/json"}
    data = {"type": "note", "title": title, "body": message}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Alert sent: {title}")
    else:
        print(f"Failed to send alert: {response.content}")

# Check stock prices for all stocks
def check_stock_prices():
    global alerts_sent_today, alert_reset_time

    # Reset alert count at midnight
    if datetime.now() >= alert_reset_time:
        alerts_sent_today = 0
        alert_reset_time = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)

    # Skip if alert limit is reached
    if alerts_sent_today >= MAX_ALERTS:
        print("Max alerts sent for today.")
        return

    for symbol in STOCK_SYMBOLS:
        try:
            # Fetch current stock data
            stock = yf.Ticker(symbol)
            current_price = stock.history(period="1d", interval="1m").iloc[-1]['Close']
            print(f"Current price of {symbol}: {current_price}")

            # Get trade conditions for the stock
            conditions = TRADE_CONDITIONS[symbol]
            if current_price >= conditions["buy"]:
                # Long trade alert
                title = f"Buy Signal: {symbol}"
                message = (f"Entry Price: ₹{conditions['buy']}\nTarget: ₹{conditions['target_buy']}\n"
                           f"Stop-Loss: ₹{conditions['stoploss_buy']}\nCurrent Price: ₹{current_price}")
                send_pushbullet_alert(title, message)
                alerts_sent_today += 1

            elif current_price <= conditions["sell"]:
                # Short trade alert
                title = f"Sell Signal: {symbol}"
                message = (f"Entry Price: ₹{conditions['sell']}\nTarget: ₹{conditions['target_sell']}\n"
                           f"Stop-Loss: ₹{conditions['stoploss_sell']}\nCurrent Price: ₹{current_price}")
                send_pushbullet_alert(title, message)
                alerts_sent_today += 1

        except Exception as e:
            print(f"Error processing {symbol}: {e}")

# Main script loop
if __name__ == "__main__":
    import time
    print("Starting global stock alert system...")
    while True:
        try:
            check_stock_prices()
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(60)  # Check every minute
