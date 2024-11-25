import os
import yfinance as yf
import requests
from datetime import datetime, timedelta

# Fetch Pushbullet API key from environment variables
PUSHBULLET_API_KEY = os.getenv("PUSHBULLET_API_KEY")
if not PUSHBULLET_API_KEY:
    raise ValueError("Pushbullet API key is missing. Please set the PUSHBULLET_API_KEY environment variable.")

# Stock and trade parameters
STOCK_SYMBOL = "TATAPOWER.NS"
ENTRY_BUY = 414  # Buying entry level
ENTRY_SELL = 408  # Selling entry level
TARGET_BUY = 425  # Target for long trades
TARGET_SELL = 402  # Target for short trades
STOPLOSS_BUY = 408  # Stop-loss for long trades
STOPLOSS_SELL = 414  # Stop-loss for short trades

# Alert tracking
MAX_ALERTS = 10
alerts_sent_today = 0
alert_reset_time = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)

# Pushbullet alert function
def send_pushbullet_alert(title, message):
    """Send alerts to Pushbullet."""
    if not PUSHBULLET_API_KEY:
        print("Pushbullet API key is missing. Skipping alert.")
        return
    
    url = "https://api.pushbullet.com/v2/pushes"
    headers = {"Access-Token": PUSHBULLET_API_KEY, "Content-Type": "application/json"}
    data = {"type": "note", "title": title, "body": message}
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        print(f"Alert sent: {title}")
    else:
        print(f"Failed to send alert: {response.content.decode()}")

# Check stock price
def check_stock_price():
    """Fetch current stock price and generate alerts based on conditions."""
    global alerts_sent_today, alert_reset_time
    
    # Reset alert count at midnight
    if datetime.now() >= alert_reset_time:
        alerts_sent_today = 0
        alert_reset_time = datetime.now().replace(hour=0, minute=0, second=0) + timedelta(days=1)
    
    # Skip if alert limit is reached
    if alerts_sent_today >= MAX_ALERTS:
        print("Max alerts sent for today. No more alerts will be sent.")
        return
    
    # Fetch stock data
    stock = yf.Ticker(STOCK_SYMBOL)
    try:
        data = stock.history(period="1d", interval="1m")
        if data.empty:
            print("Error fetching stock data: No data available.")
            return
        
        current_price = data.iloc[-1]['Close']
        print(f"Current price of {STOCK_SYMBOL}: {current_price}")
    except Exception as e:
        print(f"Error fetching stock price: {e}")
        return
    
    # Trade signals
    if current_price >= ENTRY_BUY:
        # Long trade alert
        title = "Buy Signal: Tata Power"
        message = f"Entry Price: ₹{ENTRY_BUY}\nTarget: ₹{TARGET_BUY}\nStop-Loss: ₹{STOPLOSS_BUY}\nCurrent Price: ₹{current_price}"
        send_pushbullet_alert(title, message)
        alerts_sent_today += 1
    elif current_price <= ENTRY_SELL:
        # Short trade alert
        title = "Sell Signal: Tata Power"
        message = f"Entry Price: ₹{ENTRY_SELL}\nTarget: ₹{TARGET_SELL}\nStop-Loss: ₹{STOPLOSS_SELL}\nCurrent Price: ₹{current_price}"
        send_pushbullet_alert(title, message)
        alerts_sent_today += 1
    else:
        print("No actionable signal based on current price.")

# Main script loop
if __name__ == "__main__":
    check_stock_price()
