class ExchangeError(Exception):
    """Base exception for exchange wrapper errors."""
    pass

class ExchangeConnectionError(ExchangeError):
    """Raised when unable to connect to an exchange."""
    pass

class ExchangeSymbolNotFound(ExchangeError):
    """Raised when the requested symbol is not found on the exchange."""
    pass

class ExchangeRateLimitError(ExchangeError):
    """Raised when rate limit is exceeded."""
    pass
