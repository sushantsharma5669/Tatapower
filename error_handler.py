# error_handler.py
class TradingBotError(Exception):
    """Base exception class for Trading Bot errors"""
    pass

class AuthenticationError(TradingBotError):
    """Exception raised for authentication related errors"""
    pass

class MarketDataError(TradingBotError):
    """Exception raised for market data related errors"""
    pass

class OrderPlacementError(TradingBotError):
    """Exception raised for order placement errors"""
    pass