import time
import logging
from datetime import datetime, timedelta, timezone
from src.alerts.config import AlertSettings
from src.alerts.models import PriceAlert
from src.alerts.notifier import TelegramNotifier
from src.alerts.sentiment import get_sentiment_provider
from src.exchange_wrapper import get_price

logger = logging.getLogger(__name__)


class PriceAlertEngine:
    def __init__(self, settings: AlertSettings):
        self.settings = settings
        self.notifier = TelegramNotifier(
            settings.telegram_bot_token,
            settings.telegram_chat_id,
        )
        self.sentiment = get_sentiment_provider(settings)

        # build alerts from config, each alert now has its own exchange
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


    def fetch_prices(self) -> dict[str, float]:
        """Fetch latest prices for all symbols using per alert exchange configuration."""
        prices = {}
        for alert in self.alerts:
            key = f"{alert.exchange}:{alert.symbol}"
            if key in prices:
                continue  # already fetched this symbol from this exchange

            try:
                # use alert's exchange with its fallback list
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
        result = self.sentiment.classify(message)
        if result and result.get("labels"):
            top_label = result["labels"][0]
            top_score = result["scores"][0]
            provider = self.settings.sentiment_provider
            message += f"\n\n*Sentiment ({provider}):* {top_label} ({top_score:.2f})"
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
