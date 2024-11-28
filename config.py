import os
from typing import Dict

class TradingConfig:
    """Configuration settings for the trading bot"""
    
    # Trading Parameters
    CAPITAL = 16000
    MAX_TRADES = 10
    RISK_RATIO = 2
    MAX_RISK_PER_TRADE = 0.02
    ACCURACY_THRESHOLD = 0.75
    HOLDING_DURATION = "2-3 hours"
    
    # API Parameters
    API_BASE_URL = "https://api.upstox.com/v2"
    API_VERSION = "2.0"
    API_RATE_LIMIT = 5  # calls per minute
    MAX_RETRIES = 3
    
    # Market Hours (IST)
    MARKET_OPEN_TIME = "0915"
    MARKET_CLOSE_TIME = "1530"
    
    # Recommended Stocks
    STOCK_LIST = [
        'RELIANCE.NS', 'HDFCBANK.NS', 'ICICIBANK.NS',
        'INFY.NS', 'TCS.NS', 'ADANIGREEN.NS',
        'TATAMOTORS.NS', 'BAJFINANCE.NS',
        'SBIN.NS', 'AXISBANK.NS', 'KOTAKBANK.NS'
    ]
    
    @staticmethod
    def get_env_variables() -> Dict[str, str]:
        """Get environment variables"""
        required_vars = {
            'UPSTOX_API_KEY': os.getenv('UPSTOX_API_KEY'),
            'UPSTOX_API_SECRET': os.getenv('UPSTOX_API_SECRET'),
            'PUSHBULLET_API_KEY': os.getenv('PUSHBULLET_API_KEY')
        }
        
        missing_vars = [key for key, value in required_vars.items() if not value]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        return required_vars