import yfinance as yf
import time
import datetime
import pytz
import pandas as pd
from pushbullet import Pushbullet

# Set up Pushbullet
PB_API_KEY = "your_pushbullet_api_key"  # Replace with your Pushbullet API Key
pb = Pushbullet(PB_API_KEY)

# Global constants and thresholds
MAX_ALERTS = 5
alerts_sent_today = 0
MIN_PRICE_MOVEMENT = 0.5  # 0.5% minimum price movement for alert
RSI_THRESHOLD_BUY = 20  # RSI below 20 for buying
RSI_THRESHOLD_SELL = 80  # RSI above 80 for selling

# Function to send alert through Pushbullet
def send_pushbullet_alert(title, message):
    try:
        push = pb.push_note(title, message)
    except Exception as e:
        print(f"Error sending alert: {e}")

# Manual Test Alert to confirm Pushbullet functionality
def send_test_alert():
    try:
        send_pushbullet_alert("Test Alert", "This is a test alert to check if Pushbullet is working.")
    except Exception as e:
        print(f"Error in sending test alert: {e}")

# Function to check if market is open (simple placeholder, replace with actual market hours logic)
def is_market_open():
    # Assuming market hours are from 9:00 AM to 3:30 PM IST
    now = datetime.datetime.now(pytz.timezone("Asia/Kolkata"))
    return now.hour >= 9 and now.hour < 15

# Fetch stock data and calculate RSI and price change
def fetch_stock_data(symbol):
    stock = yf.Ticker(symbol)
    hist_data = stock.history(period="5d", interval="1m")  # Get 5 days of data with 1-minute intervals
    return symbol, hist_data

# Analyze stock data to trigger alerts based on price change and RSI
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
                print(f"[DEBUG] Triggering Buy Alert for {symbol} - Price: {current_price}, RSI: {rsi}")
                send_pushbullet_alert(f"Buy Signal for {symbol}", f"Price: {current_price}, RSI: {rsi}, Change: {price_change}%")
                alerts_sent_today += 1
            elif price_change < -MIN_PRICE_MOVEMENT and rsi > RSI_THRESHOLD_SELL:
                print(f"[DEBUG] Triggering Sell Alert for {symbol} - Price: {current_price}, RSI: {rsi}")
                send_pushbullet_alert(f"Sell Signal for {symbol}", f"Price: {current_price}, RSI: {rsi}, Change: {price_change}%")
                alerts_sent_today += 1
    except Exception as e:
        print(f"Error analyzing {symbol}: {e}")

# Main function to control flow
def main():
    symbols = ['ADANIGREEN.NS', 'RELIANCE.NS', 'TATAPOWER.NS']  # Add your stock symbols here
    
    # Send test alert on each run to confirm functionality
    send_test_alert()

    for symbol in symbols:
        try:
            symbol, hist_data = fetch_stock_data(symbol)
            analyze_stock(symbol, hist_data)
        except Exception as e:
            print(f"Error processing {symbol}: {e}")

    # Wait for a while before checking again (to avoid too many API calls in a short time)
    time.sleep(60)

# Start the main function in a loop to run periodically (e.g., every minute)
if __name__ == "__main__":
    while True:
        main()
