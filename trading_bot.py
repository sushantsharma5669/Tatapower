import yfinance as yf
import pandas as pd
import numpy as np
import requests
import time
from datetime import datetime, timedelta
from pytz import timezone

# Pushbullet API for notifications
PUSHBULLET_TOKEN = "o.sdZ1bFEeGj2tWPiwYeIqkwK0LQ0RCO4T"

def send_pushbullet_notification(title, body):
    try:
        url = "https://api.pushbullet.com/v2/pushes"
        headers = {"Access-Token": PUSHBULLET_TOKEN, "Content-Type": "application/json"}
        data = {"type": "note", "title": title, "body": body}
        response = requests.post(url, json=data, headers=headers)
        print(f"Notification sent: {response.status_code}")
    except Exception as e:
        print(f"Error sending notification: {e}")

def check_pre_market():
    """Check pre-market conditions and send alert"""
    try:
        current_time = datetime.now(timezone('Asia/Kolkata'))

        # Check if it's a weekday
        if current_time.weekday() >= 5:  # Saturday = 5, Sunday = 6
            return False

        # Convert current time to string for comparison
        current_time_str = current_time.strftime('%H:%M')

        # Pre-market alert timings (8:00 AM to 9:15 AM)
        if '08:00' <= current_time_str < '09:15':
            # Fetch pre-market data
            premarket_data = yf.download("^NSEI", period="1d", interval="1m")
            if not premarket_data.empty:
                # Extract float values using the recommended method
                last_close = float(premarket_data['Close'].iloc[-1].iloc[0])
                prev_close = float(premarket_data['Close'].iloc[0].iloc[0])

                # Calculate percentage change
                change_percent = ((last_close - prev_close) / prev_close * 100)

                # Format the message
                message = (
                    f"Pre-Market Alert!\n"
                    f"Time: {current_time_str}\n"
                    f"Last Close: {last_close:.2f}\n"
                    f"Previous Day Close: {prev_close:.2f}\n"
                    f"Change: {change_percent:.2f}%"
                )

                # Send notification and print debug info
                send_pushbullet_notification("NIFTY Pre-Market Alert", message)
                print(message)
                return True
    except Exception as e:
        print(f"Error in pre-market check: {e}")
        import traceback
        print(traceback.format_exc())
    return False

def fetch_data(ticker="^NSEI", interval="1m", days=1):
    try:
        print("\n=== Data Fetch Details ===")
        end_time = datetime.now(timezone('Asia/Kolkata'))
        start_time = end_time - timedelta(days=days)

        # If current time is before market opens, fetch previous day's data
        if end_time.hour < 9 or (end_time.hour == 9 and end_time.minute < 15):
            end_time = end_time - timedelta(days=1)
            start_time = end_time - timedelta(days=days)

        data = yf.download(ticker, start=start_time, end=end_time, interval=interval)

        if data.empty:
            print("No data received from yfinance")
            return pd.DataFrame()

        # Convert index to India time
        try:
            if data.index.tz is None:
                data.index = data.index.tz_localize('UTC').tz_convert('Asia/Kolkata')
            else:
                data.index = data.index.tz_convert('Asia/Kolkata')
        except Exception as e:
            print(f"Timezone conversion warning: {e}")
            try:
                data.index = data.index.tz_localize(None).tz_localize('Asia/Kolkata')
            except Exception as e2:
                print(f"Timezone localization warning: {e2}")

        print(f"Data shape: {data.shape}")
        print(f"Data range: {data.index[0]} to {data.index[-1]}")
        print(f"Timezone: {data.index.tz}")
        return data
    except Exception as e:
        print(f"Error in fetch_data: {e}")
        return pd.DataFrame()

def calculate_indicators(data):
    try:
        print("\n=== Calculating Indicators ===")
        data = data.copy()
        data["EMA9"] = data["Close"].ewm(span=9, adjust=False).mean()
        data["EMA21"] = data["Close"].ewm(span=21, adjust=False).mean()
        data["ATR"] = (data["High"] - data["Low"]).rolling(window=14).mean()
        data["VWAP"] = (data["Close"] * data["Volume"]).cumsum() / data["Volume"].cumsum()

        print("Latest indicator values:")
        if not data.empty:
            print(f"EMA9: {data['EMA9'].iloc[-1]:.2f}")
            print(f"EMA21: {data['EMA21'].iloc[-1]:.2f}")
            print(f"ATR: {data['ATR'].iloc[-1]:.2f}")

        return data
    except Exception as e:
        print(f"Error calculating indicators: {e}")
        return data

def opening_range_breakout(data, start_time="09:15", end_time="09:45"):
    try:
        print("\n=== Opening Range Analysis ===")

        # Convert times to India timezone if needed
        if data.index.tz is None:
            data.index = data.index.tz_localize('Asia/Kolkata')
        else:
            # Convert to Indian timezone regardless of current timezone
            try:
                data.index = data.index.tz_convert('Asia/Kolkata')
            except Exception as e:
                print(f"Timezone conversion warning: {e}")

        print(f"Market opening time (expected): {start_time}")
        print(f"Range end time (expected): {end_time}")
        print(f"Current timezone: {data.index.tz}")

        # Get opening range data
        opening_range = data.between_time(start_time, end_time)

        print("\nOpening range data points:")
        for idx, row in opening_range.iterrows():
            print(f"Time: {idx.strftime('%H:%M:%S')}, High: {row['High']}, Low: {row['Low']}")

        if opening_range.empty:
            print("Warning: No data found in opening range!")
            return {"high": None, "low": None}

        high_val = opening_range["High"].max().item()
        low_val = opening_range["Low"].min().item()

        print(f"\nCalculated Range:")
        print(f"High: {high_val}")
        print(f"Low: {low_val}")
        print(f"Range size: {high_val - low_val}")

        # Verify if these values actually exist in our data
        high_time = opening_range[opening_range["High"] == high_val].index[0]
        low_time = opening_range[opening_range["Low"] == low_val].index[0]
        print(f"High price occurred at: {high_time.strftime('%H:%M:%S')}")
        print(f"Low price occurred at: {low_time.strftime('%H:%M:%S')}")

        return {
            "high": high_val,
            "low": low_val
        }
    except Exception as e:
        print(f"Error in opening_range_breakout: {e}")
        import traceback
        print(traceback.format_exc())
        return {"high": None, "low": None}

def check_signals(data, breakout, india_vix):
    try:
        print("\n=== Signal Check Debug ===")

        if data.empty:
            print("No data available")
            return None, None, None, None

        latest = data.iloc[-1].copy()
        previous = data.iloc[-2].copy()

        latest_high = latest["High"].item()
        latest_low = latest["Low"].item()
        latest_close = latest["Close"].item()
        latest_ema9 = latest["EMA9"].item()
        latest_ema21 = latest["EMA21"].item()
        latest_atr = latest["ATR"].item()

        previous_ema9 = previous["EMA9"].item()
        previous_ema21 = previous["EMA21"].item()

        print(f"Latest values - High: {latest_high:.2f}, Low: {latest_low:.2f}, Close: {latest_close:.2f}")
        print(f"Latest EMAs - EMA9: {latest_ema9:.2f}, EMA21: {latest_ema21:.2f}")
        print(f"Previous EMAs - EMA9: {previous_ema9:.2f}, EMA21: {previous_ema21:.2f}")

        breakout_high = breakout["high"]
        breakout_low = breakout["low"]

        print(f"Breakout values - High: {breakout_high:.2f}, Low: {breakout_low:.2f}")

        breakout_signal = None
        if latest_high > breakout_high:
            breakout_signal = "BUY"
        elif latest_low < breakout_low:
            breakout_signal = "SELL"

        print(f"Breakout signal: {breakout_signal}")

        ema_signal = None
        if previous_ema9 < previous_ema21 and latest_ema9 > latest_ema21:
            ema_signal = "BUY"
        elif previous_ema9 > previous_ema21 and latest_ema9 < latest_ema21:
            ema_signal = "SELL"

        print(f"EMA signal: {ema_signal}")

        if breakout_signal == ema_signal and ema_signal is not None:
            print(f"Signal: {ema_signal} at {latest_close:.2f} with ATR: {latest_atr:.2f} and India VIX: {india_vix}")
            return ema_signal, latest_close, latest_atr, india_vix
        else:
            print("No valid signal: Either breakout or EMA conditions are not met.")
            return None, None, None, None

    except Exception as e:
        print(f"Error in Signal Logic: {e}")
        import traceback
        print(traceback.format_exc())
        return None, None, None, None

def fetch_india_vix():
    try:
        vix_data = yf.download("^INDIAVIX", period="1d", interval="1m")
        if not vix_data.empty:
            return vix_data.iloc[-1]["Close"]
        return None
    except Exception as e:
        print(f"Error fetching VIX: {e}")
        return None

def calculate_position_size(capital, entry_price, atr):
    try:
        risk_per_trade = 0.01
        capital_per_trade = capital * risk_per_trade
        position_size = capital_per_trade / (atr * 2)
        return position_size
    except Exception as e:
        print(f"Error calculating position size: {e}")
        return 0

def calculate_targets(entry_price, atr, vix):
    try:
        multiplier = 1.5 if vix > 20 else 1
        stop_loss = entry_price - (atr * multiplier) if entry_price > 0 else entry_price + (atr * multiplier)
        target = entry_price + (atr * multiplier * 2) if entry_price > 0 else entry_price - (atr * multiplier * 2)
        return stop_loss, target
    except Exception as e:
        print(f"Error calculating targets: {e}")
        return None, None

def backtest_strategy(start_date, end_date, ticker="^NSEI"):
    try:
        print(f"\n=== Starting Backtest from {start_date} to {end_date} ===")

        # Convert dates to datetime if they're strings
        if isinstance(start_date, str):
            start_date = pd.Timestamp(start_date)
        if isinstance(end_date, str):
            end_date = pd.Timestamp(end_date)

        results = []
        current_chunk_start = start_date

        while current_chunk_start <= end_date:
            # Calculate chunk end date (7 days from start to stay within 8-day limit)
            current_chunk_end = min(current_chunk_start + timedelta(days=7), end_date)

            print(f"\nFetching data for period: {current_chunk_start.date()} to {current_chunk_end.date()}")

            # Fetch data for current chunk
            chunk_data = yf.download(ticker,
                                   start=current_chunk_start,
                                   end=current_chunk_end + timedelta(days=1),  # Add 1 day to include end date
                                   interval="1m")

            if not chunk_data.empty:
                print(f"Got {len(chunk_data)} minutes of data")

                # Process each day in the chunk
                for single_date in pd.date_range(current_chunk_start, current_chunk_end):
                    if single_date.weekday() < 5:  # Only process weekdays
                        day_data = chunk_data[chunk_data.index.date == single_date.date()]

                        if not day_data.empty:
                            print(f"\nAnalyzing {single_date.date()}")

                            # Calculate indicators
                            day_data = calculate_indicators(day_data)

                            # Get opening range
                            opening_range = opening_range_breakout(day_data)

                            if opening_range["high"] is not None:
                                # Get VIX data
                                vix_data = yf.download("^INDIAVIX",
                                                     start=single_date,
                                                     end=single_date + timedelta(days=1),
                                                     interval="1d")
                                vix_value = vix_data["Close"].mean() if not vix_data.empty else None

                                # Analyze each minute for signals
                                signals = []
                                for i in range(1, len(day_data)):
                                    signal, price, atr, _ = check_signals(day_data.iloc[i-1:i+1],
                                                                        opening_range,
                                                                        vix_value)
                                    if signal:
                                        signals.append({
                                            "time": day_data.index[i].strftime('%H:%M'),
                                            "type": signal,
                                            "price": price,
                                            "atr": atr
                                        })

                                results.append({
                                    "date": single_date.date(),
                                    "opening_range_high": opening_range["high"],
                                    "opening_range_low": opening_range["low"],
                                    "day_high": day_data["High"].max(),
                                    "day_low": day_data["Low"].min(),
                                    "signals": signals,
                                    "data_points": len(day_data)
                                })

                                print(f"Signals found: {len(signals)}")
                        else:
                            print(f"No data available for {single_date.date()}")

            # Move to next chunk
            current_chunk_start = current_chunk_end + timedelta(days=1)

        # Convert results to DataFrame
        results_df = pd.DataFrame(results)

        # Save results to CSV
        if not results_df.empty:
            filename = f"backtest_results_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.csv"
            results_df.to_csv(filename)
            print(f"\nResults saved to {filename}")

            # Print summary
            print("\n=== Backtest Summary ===")
            print(f"Total days analyzed: {len(results_df)}")
            print(f"Days with signals: {len(results_df[results_df['signals'].apply(len) > 0])}")

            # Calculate success rate if you have actual results
            print("\nDetailed Signal Analysis:")
            for _, day in results_df[results_df['signals'].apply(len) > 0].iterrows():
                print(f"\nDate: {day['date']}")
                print(f"Number of signals: {len(day['signals'])}")
                for signal in day['signals']:
                    print(f"  {signal['time']}: {signal['type']} at {signal['price']:.2f}")

        return results_df

    except Exception as e:
        print(f"Error in backtest_strategy: {e}")
        import traceback
        print(traceback.format_exc())
        return pd.DataFrame()

def daily_strategy_check():
    """
    Modified to only check the most recent available trading day
    """
    try:
        # Get yesterday's date
        today = datetime.now()
        yesterday = today - timedelta(days=1)

        # If yesterday was weekend, go back to Friday
        while yesterday.weekday() >= 5:
            yesterday = yesterday - timedelta(days=1)

        print(f"\n=== Daily Strategy Check for {yesterday.date()} ===")

        # Run backtest for just this day
        results = backtest_strategy(yesterday, yesterday)

        if not results.empty:
            print("\nDetailed Analysis:")
            for _, day in results.iterrows():
                print(f"\nDate: {day['date']}")
                print(f"Opening Range: {day['opening_range_high']:.2f} - {day['opening_range_low']:.2f}")
                print(f"Day Range: {day['day_high']:.2f} - {day['day_low']:.2f}")
                print(f"Data points: {day['data_points']}")

                if len(day['signals']) > 0:
                    print("\nSignals:")
                    for signal in day['signals']:
                        print(f"{signal['time']}: {signal['type']} at {signal['price']:.2f}")

        return results
    except Exception as e:
        print(f"Error in daily check: {e}")
        import traceback
        print(traceback.format_exc())
        return None

def main():
    print("Starting NIFTY Intraday Scalping...")
    print("1. Run live trading")
    print("2. Run daily check")
    print("3. Run backtest")

    choice = input("Enter your choice (1/2/3): ")

    if choice == "1":
        run_live_trading()
    elif choice == "2":
        daily_strategy_check()
    elif choice == "3":
        start_date = input("Enter start date (YYYY-MM-DD): ")
        end_date = input("Enter end date (YYYY-MM-DD): ")
        backtest_strategy(start_date, end_date)
    else:
        print("Invalid choice")

def run_live_trading():
    breakout = None
    capital = 100000
    trades_today = 0
    max_trades = 15
    last_premarket_check = None

    while True:
        try:
            current_time = datetime.now(timezone('Asia/Kolkata'))
            current_time_str = current_time.strftime('%H:%M')
            print(f"Current Time: {current_time_str}")

            # Pre-market check (8:00 AM to 9:15 AM)
            if '08:00' <= current_time_str < '09:15':
                if last_premarket_check is None or (current_time - last_premarket_check).seconds >= 300:  # Check every 5 minutes
                    if check_pre_market():
                        last_premarket_check = current_time
                time.sleep(300)  # Sleep for 5 minutes
                continue

            # Regular market hours check (9:15 AM to 3:30 PM)
            if not ('09:15' <= current_time_str <= '15:30'):
                print("Market is closed. No trades.")
                time.sleep(300)  # Sleep for 5 minutes during off-hours
                continue

            nifty_data = fetch_data()
            if nifty_data.empty:
                print("No data received")
                time.sleep(60)
                continue

            nifty_data = calculate_indicators(nifty_data)

            if len(nifty_data) < 2:
                print("Waiting for more data...")
                time.sleep(60)
                continue

            if breakout is None and current_time_str >= '09:15':
                breakout = opening_range_breakout(nifty_data)
                print(f"Setting breakout levels: {breakout}")

            india_vix = fetch_india_vix()
            if india_vix is None:
                print("India VIX data unavailable")
                time.sleep(60)
                continue

            signal, entry_price, atr, vix = check_signals(nifty_data, breakout, india_vix)

            if signal:
                position_size = calculate_position_size(capital, entry_price, atr)
                stop_loss, target = calculate_targets(entry_price, atr, vix)
                accuracy = round(100 - vix, 2)

                message = (
                    f"{signal} Signal Detected!\n"
                    f"Entry Price: {entry_price:.2f}\nStop Loss: {stop_loss:.2f}\n"
                    f"Target: {target:.2f}\nIndia VIX: {vix}\nPosition Size: {position_size:.2f} units\n"
                    f"Estimated Accuracy: {accuracy}%\nTrades Today: {trades_today}/{max_trades}"
                )
                print(message)
                send_pushbullet_notification("NIFTY Scalping Alert", message)

                trades_today += 1

                if trades_today >= max_trades:
                    print(f"Maximum trades for the day reached: {max_trades}")
                    break

            time.sleep(60)

        except Exception as e:
            print(f"Error in main loop: {e}")
            import traceback
            print(traceback.format_exc())
            time.sleep(60)

def save_trade_history(trade_data):
    try:
        # Create a DataFrame for the new trade
        trade_df = pd.DataFrame([trade_data])

        # Try to load existing history
        try:
            history = pd.read_csv('trade_history.csv')
            history = pd.concat([history, trade_df], ignore_index=True)
        except FileNotFoundError:
            history = trade_df

        # Save updated history
        history.to_csv('trade_history.csv', index=False)
        print("Trade history updated successfully")
    except Exception as e:
        print(f"Error saving trade history: {e}")

def load_trade_history():
    try:
        return pd.read_csv('trade_history.csv')
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as e:
        print(f"Error loading trade history: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nProgram stopped by user")
    except Exception as e:
        print(f"Critical error: {e}")
        import traceback
        print(traceback.format_exc())
