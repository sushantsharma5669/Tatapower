# Intraday Trading Bot

An automated intraday trading system that generates signals and executes trades using Upstox API. The bot implements a risk-managed approach with real-time notifications via Pushbullet.

## Features

- Automated intraday trading signals
- Risk management with 1:2 risk-reward ratio
- Real-time Pushbullet notifications
- Integration with Upstox trading platform
- Comprehensive error handling and logging

## Prerequisites

- Python 3.9 or higher
- Upstox trading account
- Pushbullet account
- Required API credentials

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/intraday-trading-bot.git
cd intraday-trading-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API credentials
```

## Configuration

- Trading Capital: ₹16,000
- Maximum Trades per Day: 10
- Risk per Trade: 2%
- Risk-Reward Ratio: 1:2

## Usage

Run the trading bot:
```bash
python src/trading_bot.py
```

## GitHub Actions

The bot is configured to run automatically during market hours using GitHub Actions. Check `.github/workflows/trading_bot.yml` for the schedule configuration.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This bot is for educational purposes only. Trade at your own risk. Past performance does not guarantee future results.