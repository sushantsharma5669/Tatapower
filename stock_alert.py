import os
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time

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

# Analyze stock data (function for each stock)
def analyze_stock(symbol):
    global alerts_sent_today

    # Fetch stock data
    stock = yf.Ticker(symbol)
    try:
        hist_data = stock.history(period="1d", interval="1m")  # Fetching 1 day of data with 1-minute intervals for more granularity
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

        # Log details during non-market hours (this helps with validation)
        if not is_market_open():
            print(f"Last Trading Details for {symbol}:")
            print(f"Current Price: ₹{current_price:.2f}, RSI: {rsi:.2f}, Price Change: {price_change:.2f}%")
            return  # Skip alert sending during non-market hours but log data

        # Alert Conditions (Only if market is open or closed)
        if alerts_sent_today < MAX_ALERTS:
            if price_change > MIN_PRICE_MOVEMENT and rsi < RSI_THRESHOLD_BUY:
                send_pushbullet_alert(
                    f"Buy Signal for {symbol}",
                    f"Current Price: ₹{current_price:.2f}\nRSI: {rsi:.2f}\nPrice Change: {price_change:.2f}%"
                )
                alerts_sent_today += 1
            elif price_change < -MIN_PRICE_MOVEMENT and rsi > RSI_THRESHOLD_SELL:
                send_pushbullet_alert(
                    f"Sell Signal for {symbol}",
                    f"Current Price: ₹{current_price:.2f}\nRSI: {rsi:.2f}\nPrice Change: {price_change:.2f}%"
                )
                alerts_sent_today += 1
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")

# Main loop
def main():
    global alerts_sent_today
    while True:
        try:
            # Process each stock one by one (no threading for simplicity)
            for stock in STOCK_LIST:
                analyze_stock(stock)

            # Reduce the sleep time to 2 minutes for faster iterations during non-market hours
            time.sleep(120)  # Run every 2 minutes (adjust if necessary)

        except Exception as e:
            print(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()
