import os
import yfinance as yf
import time
from datetime import datetime
from pushbullet import Pushbullet

# Fetch the Pushbullet API key from environment variables
PB_API_KEY = os.getenv('PUSHBULLET_API_KEY')

if not PB_API_KEY:
    raise ValueError("Pushbullet API key is missing!")

# Initialize Pushbullet
pb = Pushbullet(PB_API_KEY)

# Function to send a Pushbullet notification
def send_pushbullet_alert(message):
    push = pb.push_note("Stock Alert", message)
    print(f"Sent notification: {message}")

# Constants
MIN_PRICE_MOVEMENT = 1.0  # 1% price movement for alerts
RSI_BUY_THRESHOLD = 20  # RSI threshold for buying
RSI_SELL_THRESHOLD = 80  # RSI threshold for selling

# Function to fetch stock data
def fetch_stock_data(symbol):
    stock = yf.Ticker(symbol)
    hist_data = stock.history(period="1d", interval="1m", actions=False, prepost=False)
    return symbol, hist_data

# Function to calculate RSI
def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi

# Function to analyze stock data and send alerts
def analyze_stock(symbol, hist_data):
    rsi = calculate_rsi(hist_data)
    current_price = hist_data['Close'].iloc[-1]
    price_change = (current_price - hist_data['Close'].iloc[-2]) / hist_data['Close'].iloc[-2] * 100

    # Debugging the values
    print(f"[DEBUG] {symbol} - Current Price: {current_price}, RSI: {rsi.iloc[-1]}, Price Change: {price_change}%")

    # Check RSI for Buy/Sell alerts
    if rsi.iloc[-1] < RSI_BUY_THRESHOLD and price_change < -MIN_PRICE_MOVEMENT:
        message = f"BUY ALERT for {symbol} - Current Price: {current_price}, RSI: {rsi.iloc[-1]}, Price Change: {price_change}%"
        send_pushbullet_alert(message)
    elif rsi.iloc[-1] > RSI_SELL_THRESHOLD and price_change > MIN_PRICE_MOVEMENT:
        message = f"SELL ALERT for {symbol} - Current Price: {current_price}, RSI: {rsi.iloc[-1]}, Price Change: {price_change}%"
        send_pushbullet_alert(message)

# Main function
def main():
    stock_symbols = ["ADANIGREEN.NS", "RELIANCE.NS", "TATAPOWER.NS"]

    for symbol in stock_symbols:
        try:
            symbol, hist_data = fetch_stock_data(symbol)
            analyze_stock(symbol, hist_data)
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")

        # Sleep for a minute to prevent hitting API limits
        time.sleep(60)

if __name__ == "__main__":
    main()
