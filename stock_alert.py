import os
import yfinance as yf
import requests
from datetime import datetime, timedelta
import time
import concurrent.futures  # For parallel execution

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

# Store market open status to avoid checking repeatedly
market_open = None

def is_market_open():
    global market_open
    if market_open is None:  # Set this value once
        now = datetime.now()
        market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
        market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
        market_open = market_open_time <= now <= market_close_time
    return market_open

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

def analyze_stock(symbol):
    global alerts_sent_today
    start_time = time.time()
    
    try:
        stock = yf.Ticker(symbol)
        hist_data = stock.history(period="1d", interval="1m")  # Fetch granular data
        if hist_data.empty:
            print(f"No data for {symbol}")
            return

        current_price = hist_data.iloc[-1]['Close']
        prev_close = hist_data.iloc[-2]['Close']
        price_change = ((current_price - prev_close) / prev_close) * 100

        gains = hist_data['Close'].diff().apply(lambda x: x if x > 0 else 0).mean()
        losses = -1 * hist_data['Close'].diff().apply(lambda x: x if x < 0 else 0).mean()
        rsi = 100 if losses == 0 else 100 - (100 / (1 + (gains / losses)))

        print(f"[DEBUG] {symbol} - Current Price: {current_price}, RSI: {rsi}, Price Change: {price_change}%")

        if is_market_open() and alerts_sent_today < MAX_ALERTS:
            if price_change > MIN_PRICE_MOVEMENT and rsi < RSI_THRESHOLD_BUY:
                send_pushbullet_alert(f"Buy Signal for {symbol}", f"Price: {current_price}, RSI: {rsi}, Change: {price_change}%")
                alerts_sent_today += 1
            elif price_change < -MIN_PRICE_MOVEMENT and rsi > RSI_THRESHOLD_SELL:
                send_pushbullet_alert(f"Sell Signal for {symbol}", f"Price: {current_price}, RSI: {rsi}, Change: {price_change}%")
                alerts_sent_today += 1

    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")
    finally:
        end_time = time.time()
        print(f"[DEBUG] {symbol} - Analysis Time: {end_time - start_time:.2f}s")

def main():
    while True:
        try:
            start_loop = time.time()
            with concurrent.futures.ThreadPoolExecutor() as executor:  # Run stock analysis in parallel
                executor.map(analyze_stock, STOCK_LIST)
            
            print(f"[DEBUG] Loop Execution Time: {time.time() - start_loop:.2f}s")
            time.sleep(60)  # Reduce sleep for faster testing during non-market hours
        except Exception as e:
            print(f"Error in main loop: {e}")

if __name__ == "__main__":
    main()
