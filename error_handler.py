class TradingBotError(Exception):
    """Base exception class for Trading Bot errors"""
    pass

class AuthenticationError(TradingBotError):
    """Exception raised for authentication related errors"""
    pass

class MarketDataError(TradingBotError):
    """Exception raised for market data related errors"""
    pass

class SignalGenerationError(TradingBotError):
    """Exception raised for signal generation related errors"""
    pass

class AlertError(TradingBotError):
    """Exception raised for alert sending related errors"""
    pass