import os
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time  # Importing the time module

# Fetch the Pushbullet API key from the environment variables securely
PUSHBULLET_API_KEY = os.getenv("PUSHBULLET_API_KEY")  # Ensure this is set properly in the environment
POLYGON_API_KEY = "E63VhUztCTlpFfTNSMgR0K4xPj43ZpQC"  # Your Polygon API key, keep it hardcoded or in environment if needed

if not PUSHBULLET_API_KEY:
    print("Pushbullet API key not set. Please ensure it's in the environment variables.")
    exit(1)

# Stock and trade parameters
STOCK_LIST = ["ADANIGREEN.NS", "TATAPOWER.NS", "RELIANCE.NS"]  # Expandable stock list
MAX_ALERTS = 20
alerts_sent_today = 0
alert_reset_time = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)

# Conditions
RSI_THRESHOLD_BUY = 30
RSI_THRESHOLD_SELL = 70
MIN_PRICE_MOVEMENT = 5  # Minimum % movement to trigger alerts

# Market hours check (9:15 AM to 3:30 PM IST)
def is_market_open():
    now = datetime.now()
    market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open_time <= now <= market_close_time

# Pushbullet alert function
def send_pushbullet_alert(title, message):
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {"Access-Token": PUSHBULLET_API_KEY, "Content-Type": "application/json"}
    data = {"type": "note", "title": title, "body": message}
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        print(f"Alert sent: {title}")
    else:
        print(f"Failed to send alert: {response.content}")

# Analyze stock data
def analyze_stock(symbol):
    global alerts_sent_today

    # Fetch stock data
    stock = yf.Ticker(symbol)
    try:
        hist_data = stock.history(period="5d", interval="1d")  # Changed to valid period "5d"
        if len(hist_data) < 2:
            print(f"Not enough data for {symbol}")
            return  # Skip this stock if not enough data

        current_price = hist_data.iloc[-1]['Close']
        prev_close = hist_data.iloc[-2]['Close']
        price_change = ((current_price - prev_close) / prev_close) * 100

        # Fetch RSI (simplified calculation)
        gains = hist_data['Close'].diff().apply(lambda x: x if x > 0 else 0).mean()
        losses = -1 * hist_data['Close'].diff().apply(lambda x: x if x < 0 else 0).mean()
        if losses == 0:  # Prevent division by zero
            rsi = 100
        else:
            rsi = 100 - (100 / (1 + (gains / losses)))

        # Alert Conditions (Only if market is closed or certain conditions are met)
        if alerts_sent_today < MAX_ALERTS:
            if not is_market_open():  # Check if market is closed
                if price_change > MIN_PRICE_MOVEMENT and rsi < RSI_THRESHOLD_BUY:
                    send_pushbullet_alert(
                        f"Buy Signal for {symbol} (Post Market)",
                        f"Current Price: ₹{current_price:.2f}\nRSI: {rsi:.2f}\nPrice Change: {price_change:.2f}%"
                    )
                    alerts_sent_today += 1
                elif price_change < -MIN_PRICE_MOVEMENT and rsi > RSI_THRESHOLD_SELL:
                    send_pushbullet_alert(
                        f"Sell Signal for {symbol} (Post Market)",
                        f"Current Price: ₹{current_price:.2f}\nRSI: {rsi:.2f}\nPrice Change: {price_change:.2f}%"
                    )
                    alerts_sent_today += 1
            else:  # Market is open, do normal checks
                if price_change > MIN_PRICE_MOVEMENT and rsi < RSI_THRESHOLD_BUY:
                    send_pushbullet_alert(
                        f"Buy Signal for {symbol}",
                        f"Current Price: ₹{current_price:.2f}\nRSI: {rsi:.2f}\nPrice Change: {price_change:.2f}%"
                    )
                    alerts_sent_today += 1
                elif price_change < -MIN_PRICE_MOVEMENT and rsi > RSI_THRESHOLD_SELL:
                    send_pushbullet_alert(
                      
