import yfinance as yf
import requests
import time
from datetime import datetime
import pytz
import concurrent.futures

# Configuration for the alerts
MIN_PRICE_MOVEMENT = 1.0  # Minimum 1% price movement to trigger alerts (down from 5%)
RSI_THRESHOLD_BUY = 20  # Buy if RSI is below 20 (more lenient)
RSI_THRESHOLD_SELL = 80  # Sell if RSI is above 80 (more lenient)
MAX_ALERTS = 5  # Maximum alerts per day
alerts_sent_today = 0

# Pushbullet API key for sending alerts
PUSHBULLET_API_KEY = "your_pushbullet_api_key"

# Stock symbols to monitor
STOCK_SYMBOLS = ['ADANIGREEN.NS', 'RELIANCE.NS', 'TATAPOWER.NS']

# Timezone for India (IST)
india_tz = pytz.timezone('Asia/Kolkata')

# Function to send alert using Pushbullet
def send_pushbullet_alert(title, message):
    try:
        url = "https://api.pushbullet.com/v2/pushes"
        headers = {
            "Access-Token": PUSHBULLET_API_KEY
        }
        data = {
            "type": "note",
            "title": title,
            "body": message
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print(f"Alert sent: {title} - {message}")
        else:
            print(f"Error sending alert: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"Error sending Pushbullet alert: {e}")

# Check if the market is open (9:15 AM to 3:30 PM IST, Monday to Friday)
def is_market_open():
    now = datetime.now(india_tz)
    market_open_time = now.replace(hour=9, minute=15, second=0, microsecond=0)
    market_close_time = now.replace(hour=15, minute=30, second=0, microsecond=0)
    return market_open_time <= now <= market_close_time

# Fetch historical data for a stock symbol
def fetch_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist_data = stock.history(period="1d", interval="1m", actions=False, prepost=False)
        return symbol, hist_data
    except Exception as e:
        print(f"Error fetching data for {symbol}: {e}")
        return symbol, None

# Analyze stock data and trigger alerts based on price change and RSI
def analyze_stock(symbol, hist_data):
    global alerts_sent_today
    try:
        # Get current price and previous closing price
        current_price = hist_data.iloc[-1]['Close']
        prev_close = hist_data.iloc[-2]['Close']
        price_change = ((current_price - prev_close) / prev_close) * 100

        # Calculate RSI (Relative Strength Index)
        gains = hist_data['Close'].diff().apply(lambda x: x if x > 0 else 0).mean()
        losses = -1 * hist_data['Close'].diff().apply(lambda x: x if x < 0 else 0).mean()
        rsi = 100 if losses == 0 else 100 - (100 / (1 + (gains / losses)))

        print(f"[DEBUG] {symbol} - Current Price: {current_price}, RSI: {rsi}, Price Change: {price_change}%")

        # Check if market is open and alerts limit is not exceeded
        if is_market_open() and alerts_sent_today < MAX_ALERTS:
            # Check if price change exceeds threshold and RSI meets conditions
            if price_change > MIN_PRICE_MOVEMENT and rsi < RSI_THRESHOLD_BUY:
                send_pushbullet_alert(f"Buy Signal for {symbol}", f"Price: {current_price}, RSI: {rsi}, Change: {price_change}%")
                alerts_sent_today += 1
            elif price_change < -MIN_PRICE_MOVEMENT and rsi > RSI_THRESHOLD_SELL:
                send_pushbullet_alert(f"Sell Signal for {symbol}", f"Price: {current_price}, RSI: {rsi}, Change: {price_change}%")
                alerts_sent_today += 1
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")

# Main function to run the script
def main():
    global alerts_sent_today
    try:
        # Create a thread pool to fetch stock data concurrently for all symbols
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {executor.submit(fetch_stock_data, symbol): symbol for symbol in STOCK_SYMBOLS}
            for future in concurrent.futures.as_completed(futures):
                symbol, hist_data = future.result()
                if hist_data is not None:
                    analyze_stock(symbol, hist_data)

    except Exception as e:
        print(f"Error in main function: {e}")

if __name__ == "__main__":
    main()
