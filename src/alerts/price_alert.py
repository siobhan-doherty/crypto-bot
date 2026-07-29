import time
import logging
import pandas as pd
from datetime import datetime, timedelta, timezone
from src.alerts.config import AlertSettings
from src.alerts.models import PriceAlert
from src.alerts.notifier import TelegramNotifier
from src.alerts.sentiment import get_sentiment_provider
from src.alerts.sentiment.huggingface import HuggingFaceSentiment
from src.exchange_wrapper import get_price
from src.pattern_analytics.pattern_detector import PatternDetector

logger = logging.getLogger(__name__)


class PriceAlertEngine:
    def __init__(self, settings: AlertSettings):
        self.settings = settings
        self.notifier = TelegramNotifier(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
        )
        # primary sentiment provider, Mistral or HugginFace
        self.sentiment = get_sentiment_provider(settings)
        # secondary HF for fallback
        self.hf_sentiment = HuggingFaceSentiment(settings.hf_token, settings.hf_model)
        # cost tracking
        self.cost_tracker = {
            "mistral": {"requests": 0, "tokens": 0, "cost": 0.0},
            "huggingface": {"requests": 0, "tokens": 0, "cost": 0.0},
        }
        # build alerts
        self.alerts = []
        for alert_config in self.settings.alerts:
            self.alerts.append(
                PriceAlert(
                    symbol = alert_config["symbol"],
                    exchange = alert_config.get("exchange", "binance"),
                    threshold = alert_config["threshold"],
                    condition = alert_config["condition"],
                    fallback_exchanges = alert_config.get("fallback_exchanges"),
                )
            ) 
        logger.info(f"Loaded {len(self.alerts)} alerts")
        for alert in self.alerts:
            logger.info(
                f"{alert.symbol} @ {alert.exchange} {alert.condition} ${alert.threshold}"
            )
        
        self.pattern_detector = PatternDetector()


    def fetch_prices(self) -> dict[str, float]:
        """Fetch latest prices for all symbols using per alert exchange configuration."""
        prices = {}
        for alert in self.alerts:
            key = f"{alert.exchange}:{alert.symbol}"
            if key in prices:
                continue  # already fetched this symbol from this exchange
            try:
                fallback = alert.fallback_exchanges or self.settings.default_fallback_exchanges
                price = get_price(
                    symbol = alert.symbol,
                    exchange = alert.exchange,
                    fallback_exchanges = fallback,
                )
                prices[key] = price
                logger.debug(f"{key}: {price}")
            except Exception as e:
                logger.error(f"Failed to fetch {key}: {e}")

        return prices


    def check_alerts(self, prices: dict[str, float]) -> list[str]:
        """Evaluate all alerts and return list of messages."""
        messages = []
        now = datetime.now(timezone.utc)
        cooldown = timedelta(hours = 1)
        for alert in self.alerts:
            key = f"{alert.exchange}:{alert.symbol}"
            current = prices.get(key)
            if current is None:
                continue

            triggered = False
            if alert.condition == "above" and current > alert.threshold:
                triggered = True
            elif alert.condition == "below" and current < alert.threshold:
                triggered = True
            if triggered:
                # check cooldown
                if alert.last_alert_time and (now - alert.last_alert_time) < cooldown:
                    continue
                # avoid duplicate alerts for same price level
                if alert.last_triggered_price is not None and abs(current - alert.last_triggered_price) <= 100:
                    continue

                alert.last_triggered_price = current
                alert.last_alert_time = now
                msg = (
                    f"*Price Alert!*\n"
                    f"Symbol: `{alert.symbol}`\n"
                    f"Exchange: `{alert.exchange}`\n"
                    f"Current: `${current:,.2f}`\n"
                    f"Threshold: `${alert.threshold:,.2f}` ({alert.condition})\n"
                    f"Time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
                messages.append(msg)

        return messages


    def enhance_message(self, message: str) -> str:
        # try primary provider with latency tracking
        start = time.time()
        result = self.sentiment.classify(message)
        elapsed = time.time() - start
        provider = self.settings.sentiment_provider.lower()
        if result and result.get("labels"):
            # success log latency & track cost
            logger.info(f"Sentiment ({provider}) took {elapsed:.2f}s")
            self._track_cost(provider, message, success = True)
        else:
            # primary failed, check if fallback is enabled
            if self.settings.enable_sentiment_fallback:
                logger.warning(f"{provider} failed, falling back to Hugging Face")
                start = time.time()
                result = self.hf_sentiment.classify(message)
                elapsed = time.time() - start
                provider = "huggingface"
                if result and result.get("labels"):
                    logger.info(f"Sentiment ({provider}) took {elapsed:.2f}s (fallback)")
                    self._track_cost(provider, message, success = True)
                else:
                    logger.error("Both sentiment providers failed")
                    return message  # no sentiment added
            else:
                # fallback disabled, log error & return original message
                logger.error(f"Sentiment provider {provider} failed and fallback is disabled")
                return message

        # add sentiment to message
        top_label = result["labels"][0]
        top_score = result["scores"][0]
        message += f"\n\n *Sentiment ({provider}):* {top_label} ({top_score:.2f})"
        return message


    def _track_cost(self, provider: str, text: str, success: bool):
        """estimate token usage and accumulate cost."""
        tokens = len(text) // 4
        self.cost_tracker[provider]["requests"] += 1
        self.cost_tracker[provider]["tokens"] += tokens
        # mock pricing, per 1M tokens, adjust based on actual API
        pricing = {
            "mistral": 0.20,      # $0.20 per 1M tokens for small model
            "huggingface": 0.0,   # free
        }
        cost = (tokens / 1_000_000) * pricing.get(provider, 0)
        self.cost_tracker[provider]["cost"] += cost
        # log cost summary every 10 requests
        if self.cost_tracker[provider]["requests"] % 10 == 0:
            logger.info(
                f"Cost summary ({provider}): "
                f"{self.cost_tracker[provider]['requests']} requests, "
                f"{self.cost_tracker[provider]['tokens']} tokens, "
                f"${self.cost_tracker[provider]['cost']:.4f}"
            )


    def run_once(self) -> None:
        """single alert check cycle."""
        prices = self.fetch_prices()
        if not prices:
            return

        raw_messages = self.check_alerts(prices)
        # for each alert, detect pattern & enrich
        for msg in raw_messages:
            # extract symbol from message
            symbol = None
            for alert in self.alerts:
                if alert.symbol in msg:
                    symbol = alert.symbol
                    break

            if symbol:
                # fetch price history for this symbol
                df = self._get_price_history(symbol)
                if df is not None:
                    pattern_info = self.pattern_detector.detect(df)
                    msg = self.pattern_detector.add_pattern_context_to_alert(msg, pattern_info)
            enhanced = self.enhance_message(msg)
            self.notifier.send(enhanced)


    def run_forever(self) -> None:
        """main loop, runs every check_interval_seconds."""
        logger.info("Price Alert Engine started")
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.exception(f"Unexpected error in alert cycle: {e}")
            time.sleep(self.settings.check_interval_seconds)


    def _get_price_history(self, symbol: str, timeframe: str = "1m", limit: int = 60) -> pd.DataFrame:
        """
        Fetch recent OHLCV data for symbol using CCXT.
        Returns DataFrame with columns timestamp, open, high, low, close, volume.
        """
        import ccxt
        import pandas as pd

        exchange = ccxt.binance()
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe = timeframe, limit = limit)
            if not ohlcv:
                return None

            df = pd.DataFrame(
                ohlcv,
                columns = ["timestamp", "open", "high", "low", "close", "volume"]
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit = "ms")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return None
