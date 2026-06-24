import logging
from src.alerts.config import AlertSettings
from src.alerts.price_alert import PriceAlertEngine

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    settings = AlertSettings()          # reads from .env
    engine = PriceAlertEngine(settings)
    engine.run_forever()
