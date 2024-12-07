import yfinance as yf
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator
from datetime import datetime, timedelta
import time
import requests
import pytz

# Specify timezone for market data
market_tz = pytz.timezone('Asia/Kolkata')

# Pushbullet API Key
PUSHBULLET_API_KEY = "o.sdZ1bFEeGj2tWPiwYeIqkwK0LQ0RCO4T"

# Function to send mobile alerts with time
def send_alert(title, message):
    try:
        # Current time for message delivery (converted to market timezone)
        delivery_time = datetime.now(market_tz).strftime("%Y-%m-%d %H:%M:%S")

        # Construct the message with timestamps and signal type
        message_with_time = (
            f"Rule No:1 \n"
             f"{title}\n"
            f"{message}\n"
            f"Delivery Time: {delivery_time}"
        )

        url = "https://api.pushbullet.com/v2/pushes"
        headers = {
            "Access-Token": PUSHBULLET_API_KEY,
            "Content-Type": "application/json"
        }
        data = {
            "type": "note",
            "title": title,
            "body": message_with_time
        }
        response = requests.post(url, json=data, headers=headers)
        if response.status_code == 200:
            print(f"Alert sent: {title}\n{message_with_time}")
        else:
            print(f"Failed to send alert: {response.status_code}, {response.text}")
    except Exception as e:
        print(f"Error sending alert: {e}")

# Define constants
NIFTY_TICKER = "^NSEI"  # NIFTY 50 index
SGX_NIFTY_TICKER = "^STI"  # SGX NIFTY as proxy
OPTION_INTERVAL = 15 * 60  # Option updates every 15 minutes
CHECK_INTERVAL = 3600   # Check every 1 hour
PRE_OPEN_START = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
PRE_OPEN_END = datetime.now().replace(hour=9, minute=15, second=0, microsecond=0)

# Function: Fetch real-time data
def fetch_data(ticker, period="1d", interval="1m"):
    """Fetch live data for a given ticker."""
    try:
        data = yf.download(ticker, period=period, interval=interval)
        return data
    except Exception as e:
        send_push_notification("Error Fetching Data", f"{ticker} data could not be fetched: {e}")
        return None

# Function: Pre-opening analysis
def pre_opening_analysis():
    """Analyze pre-opening sentiment based on SGX NIFTY and previous close."""
    sgx_data = fetch_data(SGX_NIFTY_TICKER, period="1d", interval="1m")
    nifty_data = fetch_data(NIFTY_TICKER, period="5d", interval="1d")

    if sgx_data is not None and not sgx_data.empty and nifty_data is not None and not nifty_data.empty:
        sgx_last = sgx_data['Close'].iloc[-1]
        nifty_prev_close = nifty_data['Close'].iloc[-2]  # Previous day's close
        gap = (sgx_last - nifty_prev_close) / nifty_prev_close * 100

        sentiment = "Bullish" if gap > 0.5 else "Bearish" if gap < -0.5 else "Sideways"
        message = f"Pre-Opening Sentiment: {sentiment}\nSGX NIFTY: {sgx_last:.2f}\nGap: {gap:.2f}%"
        send_push_notification("Pre-Opening Alert", message)
    else:
        send_push_notification("Pre-Opening Alert", "Unable to fetch SGX or NIFTY data.")

# Function: Analyze trend and indicators
def analyze_trend(data):
    """Analyze market trend based on RSI, SMA, and price levels."""
    rsi = RSIIndicator(data['Close']).rsi()
    sma_50 = SMAIndicator(data['Close'], window=50).sma_indicator()
    sma_200 = SMAIndicator(data['Close'], window=200).sma_indicator()

    last_close = data['Close'].iloc[-1]
    if rsi.iloc[-1] > 70:
        trend = "Overbought (Bearish trend expected)"
    elif rsi.iloc[-1] < 30:
        trend = "Oversold (Bullish trend expected)"
    elif last_close > sma_50.iloc[-1] > sma_200.iloc[-1]:
        trend = "Bullish (Above SMA50 and SMA200)"
    elif last_close < sma_50.iloc[-1] < sma_200.iloc[-1]:
        trend = "Bearish (Below SMA50 and SMA200)"
    else:
        trend = "Sideways (No clear trend)"

    return trend

# Function: Send Pushbullet notification
def send_push_notification(title, message):
    """Send Pushbullet notification."""
    try:
        send_alert(title, message)
    except Exception as e:
        print(f"Error sending notification: {e}")

# Function: Hourly updates
def hourly_update():
    """Send hourly updates on NIFTY trend."""
    data = fetch_data(NIFTY_TICKER)
    if data is not None and not data.empty:
        trend = analyze_trend(data)
        last_close = data['Close'].iloc[-1]
        message = f"NIFTY Current Trend: {trend}\nLast Close: {last_close:.2f}\nAction: {('Buy Call' if 'Bullish' in trend else 'Buy Put' if 'Bearish' in trend else 'Wait for clarity')}"
        send_push_notification("Hourly Update", message)

# Function: Real-time options monitoring
def options_monitoring():
    """Monitor live options data and send trade suggestions."""
    # This requires integration with an options chain API for live data.
    send_push_notification("Options Monitoring", "This feature will require live options chain integration.")

# Main function
def main():
    send_push_notification("Script Started", "Monitoring NIFTY Index Options...")

    while True:
        now = datetime.now()
        if PRE_OPEN_START <= now <= PRE_OPEN_END:
            pre_opening_analysis()
        elif 9 <= now.hour <= 15:
            hourly_update()
            options_monitoring()
        else:
            send_push_notification("Market Closed", "No updates during off-hours.")
            time.sleep(3600)  # Sleep until the next check

        time.sleep(OPTION_INTERVAL)

if __name__ == "__main__":
    main()
