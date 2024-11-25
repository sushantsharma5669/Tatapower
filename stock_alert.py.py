import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import pytz
import logging

# Specify timezone for market data
market_tz = pytz.timezone('Asia/Kolkata')

# Pushbullet API Key
PUSHBULLET_API_KEY = "o.sdZ1bFEeGj2tWPiwYeIqkwK0LQ0RCO4T"

# Function to send mobile alerts with time
def send_alert(title, message, position_time):
    try:
        for _ in range(3):  # Retry up to 3 times
            delivery_time = datetime.now(market_tz).strftime("%Y-%m-%d %H:%M:%S")
            message_with_time = (
                f"{message}\n"
                f"Position Time: {position_time}\n"
                f"Delivery Time: {delivery_time}"
            )
            url = "https://api.pushbullet.com/v2/pushes"
            headers = {"Access-Token": PUSHBULLET_API_KEY, "Content-Type": "application/json"}
            data = {"type": "note", "title": title, "body": message_with_time}
            response = requests.post(url, json=data, headers=headers)
            if response.status_code == 200:
                print(f"Alert sent: {title}\n{message_with_time}")
                break
            else:
                print(f"Retry Alert Failed: {response.status_code}")
    except Exception as e:
        print(f"Alert Error: {e}")

# Check if today is a working day
def is_market_open(today):
    if today.weekday() >= 5:  # Saturday or Sunday
        return False
    return True  # Add holiday logic as needed

# Get the last working day
def last_working_day(today):
    while not is_market_open(today):
        today -= timedelta(days=1)
    return today

# Fetch Yahoo Finance Data
def fetch_data(ticker, interval="1m", period="1d"):
    try:
        print(f"Fetching data for {ticker}...")
        data = yf.download(ticker, interval=interval, period=period)
        if data.empty:
            raise ValueError(f"No data available for ticker: {ticker}.")
        data.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        data.reset_index(inplace=True)
        return data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return pd.DataFrame()

# Indicators Calculation
def calculate_indicators(data):
    try:
        data['EMA9'] = data['Close'].ewm(span=9).mean()
        data['EMA21'] = data['Close'].ewm(span=21).mean()
        delta = data['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = -delta.where(delta < 0, 0).rolling(14).mean()
        data['RSI'] = 100 - (100 / (1 + gain / loss))
        data['BB_MA'] = data['Close'].rolling(window=20).mean()
        data['BB_STD'] = data['Close'].rolling(window=20).std()
        data['BB_Upper'] = data['BB_MA'] + (2 * data['BB_STD'])
        data['BB_Lower'] = data['BB_MA'] - (2 * data['BB_STD'])
        data = data.dropna()
        return data
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        return pd.DataFrame()

# Position Sizing Function
def calculate_position_size(capital, price, risk_percentage=1):
    try:
        risk_per_trade = capital * (risk_percentage / 100)
        stop_loss = price * 0.01  # Stop loss 1% of price
        if stop_loss == 0:
            raise ValueError("Stop-loss cannot be zero.")
        position_size = risk_per_trade / stop_loss
        max_position_size = capital * 5 / price  # Assuming 5x leverage
        return min(position_size, max_position_size)
    except Exception as e:
        print(f"Error calculating position size: {e}")
        return 0

def apply_scalping_strategy(data, capital):
    try:
        buffer = 0.1  # Allowable difference for EMA alignment
        # Ensure columns exist and print dataframe shape
        print("Columns before strategy:", data.columns)

        # Refined Signal Logic
        data.loc[:, 'Signal'] = np.where(
            (data['Close'] > data['EMA9']) & ((data['EMA9'] - data['EMA21']).abs() <= buffer) & (data['RSI'] > 45),
            'Buy',
            np.where(
                (data['Close'] < data['EMA9']) & ((data['EMA9'] - data['EMA21']).abs() <= buffer) & (data['RSI'] < 55),
                'Sell',
                'Hold'
            )
        )

        # Check DataFrame Shape after modification
        print("Data shape after strategy:", data.shape)
        print("Signal Column Values:\n", data[['Datetime', 'Signal']].tail())

        if not data.empty:
            last_signal = data.iloc[-1]
            price = last_signal['Close']
            signal = last_signal['Signal']

            # Debug signal details
            print(f"Signal Details:\n{last_signal[['Datetime', 'Close', 'EMA9', 'EMA21', 'RSI', 'Signal']]}")
            
            if signal in ['Buy', 'Sell']:
                target = price * 1.03  # Target 3% above entry
                stop_loss = price * 0.99  # Stop-loss 1% below entry
                position_size = calculate_position_size(capital, price)
                position_time = last_signal['Datetime'].strftime("%Y-%m-%d %H:%M:%S")

                send_alert(
                    "Scalping Signal Alert",
                    f"Signal: {signal}\nPrice: {price}\nPosition Size: {int(position_size)} shares\n"
                    f"Target: {target:.2f}\nStop Loss: {stop_loss:.2f}",
                    position_time
                )
            else:
                print(f"Signal remains 'Hold'. Conditions checked: Close={price}, EMA9={last_signal['EMA9']}, "
                      f"EMA21={last_signal['EMA21']}, RSI={last_signal['RSI']}")

        return data
    except Exception as e:
        print(f"Error applying scalping strategy: {e}")
        return pd.DataFrame()


# Enable logging
logging.basicConfig(level=logging.DEBUG)  # Display debug messages

# Fetch Yahoo Finance Data
def fetch_data(ticker, interval="1m", period="1d"):
    try:
        logging.debug(f"Fetching data for {ticker}...")  # Logging data fetching time
        data = yf.download(ticker, interval=interval, period=period)
        if data.empty:
            raise ValueError(f"No data available for ticker: {ticker}.")
        data.columns = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
        data.reset_index(inplace=True)

        # Log the time when the data is fetched
        logging.debug(f"Data fetched for {ticker} at {datetime.now(market_tz)}")  # Logging fetch time

        return data
    except Exception as e:
        logging.error(f"Error fetching data: {e}")
        return pd.DataFrame()


# Main Execution
if __name__ == "__main__":
    ticker = "ADANIGREEN.NS"
    capital = 17000
    today = datetime.now().date()

    if not is_market_open(today):
        today = last_working_day(today)
        period = "5d"  # Fetch historical data
    else:
        period = "1d"

    data = fetch_data(ticker, interval="1m", period=period)

    if not data.empty:
        data = calculate_indicators(data)
        if not data.empty:
            data = apply_scalping_strategy(data, capital)
