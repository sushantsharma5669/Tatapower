import os
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time
import concurrent.futures

# Fetch the Pushbullet API key from the environment variables securely
PUSHBULLET_API_KEY = os.getenv("PUSHBULLET_API_KEY")
if not PUSHBULLET_API_KEY:
    print("Pushbullet API key not set. Please ensure it's in the environment variables.")
    exit(1)

STOCK_LIST = ["ADANIGREEN.NS", "TATAPOWER.NS", "RELIANCE.NS"]
RSI_THRESHOLD_BUY = 30
RSI_THRESHOLD_SELL = 70
MIN_PRICE_MOVEMENT = 5  # Minimum % movement to trigger alerts
MAX_ALERTS = 5  # Limit to prevent spamming
alerts_sent_today = 0

def is_market_open():
    now = datetime.now()
    market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open_time <= now <= market_close_time

def send_pushbullet_alert(title, message):
    try:
        url = "https://api.pushbullet.com/v2/pushes"
        headers = {"Access-Token": PUSHBULLET_API_KEY, "Content-Type": "application/json"}
        data = {"type": "note", "title": title, "body": message}
        response = requests.post(url, json=data, headers=headers, timeout=10)  # Add timeout
        if response.status_code == 200:
            print(f"Alert sent: {title}")
        else:
            print(f"Failed to send alert: {response.content}")
    except Exception as e:
        print(f"Error sending alert: {e}")

def fetch_stock_data(symbol):
    stock = yf.Ticker(symbol)
    hist_data = stock.history(period="1d", interval="1m")  # Fetch granular data
    return symbol, hist_data

def analyze_stock(symbol, hist_data):
    global alerts_sent_today
    try:
        current_price = hist_data.iloc[-1]['Close']
        prev_close = hist_data.iloc[-2]['Close']
        price_change = ((current_price - prev_close) / prev_close) * 100

        # Calculate RSI
        gains = hist_data['Close'].diff().apply(lambda x: x if x > 0 else 0).mean()
        losses = -1 * hist_data['Close'].diff().apply(lambda x: x if x < 0 else 0).mean()
        rsi = 100 if losses == 0 else 100 - (100 / (1 + (gains / losses)))

        print(f"[DEBUG] {symbol} - Current Price: {current_price}, RSI: {rsi}, Price Change: {price_change}%")

        # Check if market is open and alerts limit is not exceeded
        if is_market_open() and alerts_sent_today < MAX_ALERTS:
            if price_change > MIN_PRICE_MOVEMENT and rsi < RSI_THRESHOLD_BUY:
                send_pushbullet_alert(f"Buy Signal for {symbol}", f"Price: {current_price}, RSI: {rsi}, Change: {price_change}%")
                alerts_sent_today += 1
            elif price_change < -MIN_PRICE_MOVEMENT and rsi > RSI_THRESHOLD_SELL:
                send_pushbullet_alert(f"Sell Signal for {symbol}", f"Price: {current_price}, RSI: {rsi}, Change: {price_change}%")
                alerts_sent_today += 1
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")

def main():
    market_open = is_market_open()  # Check once for all stocks
    
    # Using ThreadPoolExecutor to fetch data for all stocks in parallel
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(fetch_stock_data, stock) for stock in STOCK_LIST]
        for future in concurrent.futures.as_completed(futures):
            symbol, hist_data = future.result()
            analyze_stock(symbol, hist_data)

if __name__ == "__main__":
    main()
