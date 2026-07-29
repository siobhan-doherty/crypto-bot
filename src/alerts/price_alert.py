import time
import logging
import pandas as pd
from datetime import datetime, timedelta, timezone
from src.alerts.config import AlertSettings
from src.alerts.models import PriceAlert
from src.alerts.models.sentiment import SentimentResult, SentimentRecord
from src.alerts.notifier import TelegramNotifier
from src.alerts.sentiment import get_sentiment_provider
from src.alerts.sentiment.huggingface import HuggingFaceSentiment
from src.alerts.repositories.sentiment_repository import SentimentRepository
from src.pattern_analytics.pattern_detector import PatternDetector
from src.exchange_wrapper import get_price
from typing import Optional, List, Dict, Any

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
        # Sentiment repository for historical storage
        self.sentiment_repo = SentimentRepository(
            mongo_uri = settings.mongo_uri or "mongodb://localhost:27017",
            retention_seconds = settings.sentiment_retention_seconds,
        )
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
        cooldown = timedelta(hours=1)
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


    def enhance_message_with_sentiment(self, message: str, symbol: str, price: float, exchange: str) -> tuple[str, Optional[SentimentResult]]:
        """
        Enhance message with sentiment analysis and store the sentiment.
        Returns:
            Tuple of (enhanced_message, sentiment_result)
        """
        # try primary provider with latency tracking
        start = time.time()
        result_data = self.sentiment.classify(message)
        elapsed = time.time() - start
        provider = self.settings.sentiment_provider.lower()
        
        sentiment_result = None
        if result_data and result_data.get("labels"):
            # success log latency & track cost
            logger.info(f"Sentiment ({provider}) took {elapsed:.2f}s")
            self._track_cost(provider, message, success=True)
            sentiment_result = SentimentResult(
                labels = result_data["labels"],
                scores = result_data["scores"],
                text = message,
                provider = provider,
            )
        else:
            # primary failed, check if fallback is enabled
            if self.settings.enable_sentiment_fallback:
                logger.warning(f"{provider} failed, falling back to Hugging Face")
                start = time.time()
                result_data = self.hf_sentiment.classify(message)
                elapsed = time.time() - start
                provider = "huggingface"
                if result_data and result_data.get("labels"):
                    logger.info(f"Sentiment ({provider}) took {elapsed:.2f}s (fallback)")
                    self._track_cost(provider, message, success=True)
                    sentiment_result = SentimentResult(
                        labels = result_data["labels"],
                        scores = result_data["scores"],
                        text = message,
                        provider = provider,
                    )
                else:
                    logger.error("Both sentiment providers failed")
            else:
                # fallback disabled, log error
                logger.error(f"Sentiment provider {provider} failed and fallback is disabled")

        # store sentiment in MongoDB if we got a result
        if sentiment_result:
            try:
                self.sentiment_repo.store_sentiment(
                    symbol = symbol,
                    sentiment_label = sentiment_result.top_label or "neutral",
                    confidence = sentiment_result.top_confidence or 0.0,
                    text = message,
                    provider = sentiment_result.provider,
                    price = price,
                    exchange = exchange,
                    timestamp = datetime.now(timezone.utc),
                    additional_metadata = {
                        "alert_condition": "unknown",  # can be enhanced
                        "all_labels": sentiment_result.labels,
                        "all_scores": sentiment_result.scores,
                    },
                )
                logger.debug(f"Stored sentiment for {symbol} @ {price}")
            except Exception as e:
                logger.error(f"Failed to store sentiment: {e}")

        # Add sentiment to message
        if sentiment_result:
            top_label = sentiment_result.top_label
            top_score = sentiment_result.top_confidence
            message += f"\n\n *Sentiment ({provider}):* {top_label} ({top_score:.2f})"
        
        return message, sentiment_result


    def enhance_message(self, message: str) -> str:
        """
        Legacy method - kept for backward compatibility.
        This version doesn't store sentiment.
        """
        result = self.enhance_message_with_sentiment(
            message, symbol = "unknown", price = 0.0, exchange = "unknown"
        )
        return result[0]


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
            price = None
            exchange = None
            for alert in self.alerts:
                if alert.symbol in msg:
                    symbol = alert.symbol
                    price_key = f"{alert.exchange}:{alert.symbol}"
                    price = prices.get(price_key)
                    exchange = alert.exchange
                    break

            if symbol and price is not None:
                # fetch price history for this symbol
                df = self._get_price_history(symbol)
                if df is not None:
                    pattern_info = self.pattern_detector.detect(df)
                    msg = self.pattern_detector.add_pattern_context_to_alert(msg, pattern_info)

            # use new method that stores sentiment
            enhanced_msg, _ = self.enhance_message_with_sentiment(
                msg, symbol = symbol or "unknown", price = price or 0.0, exchange = exchange or "unknown"
            )
            self.notifier.send(enhanced_msg)


    def run_forever(self) -> None:
        """main loop, runs every check_interval_seconds."""
        logger.info("Price Alert Engine started with sentiment history storage")
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
                columns = ["timestamp", "open", "high", "low", "close", "volume"],
            )
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit = "ms")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch historical data for {symbol}: {e}")
            return None
