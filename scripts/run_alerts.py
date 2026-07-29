import logging
import threading
from src.alerts.config import AlertSettings
from src.alerts.price_alert import PriceAlertEngine
from src.alerts.health import start_health_server

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    # start health check server in background
    health_thread = threading.Thread(target = start_health_server, args = (8080,), daemon = True)
    health_thread.start()

    # start alert engine
    settings = AlertSettings()          # reads from .env
    engine = PriceAlertEngine(settings)
    engine.run_forever()
