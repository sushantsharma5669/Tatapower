import pytz
from datetime import datetime
import holidays
from config import TradingConfig

class MarketTiming:
    def __init__(self):
        self.ist_timezone = pytz.timezone('Asia/Kolkata')
        self.market_holidays = holidays.IN()
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        current_time = datetime.now(self.ist_timezone)
        
        # Check for weekends
        if current_time.weekday() >= 5:
            return False
            
        # Check for market holidays
        if current_time.date() in self.market_holidays:
            return False
            
        current_time_str = current_time.strftime('%H%M')
        return TradingConfig.MARKET_OPEN_TIME <= current_time_str <= TradingConfig.MARKET_CLOSE_TIME