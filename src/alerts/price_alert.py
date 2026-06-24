import time
import logging
import ccxt
from datetime import datetime
from src.alerts.config import AlertSettings
from src.alerts.models import PriceAlert
from src.alerts.notifier import TelegramNotifier, HuggingFaceEnhancer
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class PriceAlertEngine:
    def __init__(self, settings: AlertSettings):
        self.settings = settings
        self.exchange = ccxt.binance()
        self.notifier = TelegramNotifier(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
        )
        self.hf = HuggingFaceEnhancer(settings.hf_token, settings.hf_model)
        self.alerts = [
            PriceAlert(
                symbol = s, 
                threshold = self.settings.price_threshold_above, 
                condition = "above"
            )
            for s in self.settings.symbols
        ] + [
            PriceAlert(
                symbol = s, 
                threshold = self.settings.price_threshold_below, 
                condition = "below"
            )
            for s in self.settings.symbols
        ]
        self._last_prices = {}  # symbol -> last price


    def fetch_prices(self) -> dict[str, float]:
        """Fetch latest prices for all symbols."""
        prices = {}
        for symbol in self.settings.symbols:
            try:
                ticker = self.exchange.fetch_ticker(symbol)
                prices[symbol] = ticker["last"]
                logger.debug(f"{symbol}: {ticker['last']}")
            except Exception as e:
                logger.error(f"Failed to fetch {symbol}: {e}")
        return prices


    def check_alerts(self, prices: dict[str, float]) -> list[str]:
        """Evaluate all alerts and return list of messages."""
        messages = []
        now = datetime.now(timezone.utc)
        cooldown = timedelta(hours = 1)

        for alert in self.alerts:
            symbol = alert.symbol
            current = prices.get(symbol)
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
                    continue   # skip, cooldown active

                # avoid duplicate alerts for same price level
                if alert.last_triggered_price is not None and abs(current - alert.last_triggered_price) <= 100:
                    continue

                alert.last_triggered_price = current
                alert.last_alert_time = now

                msg = (
                    f"*Price Alert!*\n"
                    f"Symbol: `{symbol}`\n"
                    f"Current: `${current:,.2f}`\n"
                    f"Threshold: `${alert.threshold:,.2f}` ({alert.condition})\n"
                    f"Time: {now.strftime('%Y-%m-%d %H:%M:%S UTC')}"
                )
                messages.append(msg)

        return messages


    def enhance_message(self, message: str) -> str:
        """Optionally enrich with HF sentiment analysis."""
        if not self.settings.hf_token:
            return message

        result = self.hf.classify(message, ["bullish", "bearish", "neutral"])
        if result and "labels" in result:
            top_label = result["labels"][0]
            top_score = result["scores"][0]
            message += f"\n\n*Sentiment:* {top_label} ({top_score:.2f})"
        return message


    def run_once(self) -> None:
        """Single alert check cycle."""
        prices = self.fetch_prices()
        if not prices:
            return

        raw_messages = self.check_alerts(prices)
        for msg in raw_messages:
            enhanced = self.enhance_message(msg)
            self.notifier.send(enhanced)


    def run_forever(self) -> None:
        """Main loop, runs every check_interval_seconds."""
        logger.info("Price Alert Engine started")
        while True:
            try:
                self.run_once()
            except Exception as e:
                logger.exception(f"Unexpected error in alert cycle: {e}")
            time.sleep(self.settings.check_interval_seconds)
