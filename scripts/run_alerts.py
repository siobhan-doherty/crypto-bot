import argparse
import logging
import threading
import sys
from src.alerts.config import AlertSettings
from src.alerts.price_alert import PriceAlertEngine
from src.alerts.health import start_health_server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_forever():
    """Run the alert engine in an infinite loop."""
    # start health check server in background
    health_thread = threading.Thread(target = start_health_server, args = (8080,), daemon = True)
    health_thread.start()

    settings = AlertSettings()  # reads from .env
    engine = PriceAlertEngine(settings)
    engine.run_forever()


def run_once():
    """Run a single cycle of the alert engine and exit."""
    settings = AlertSettings()  # reads from .env
    engine = PriceAlertEngine(settings)
    engine.run_once()
    logger.info("Alert engine single run completed successfully")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description = "Run Price Alert Engine")
    parser.add_argument(
        "--once",
        action = "store_true",
        help = "Run a single cycle and exit (for scheduled/managed execution)",
    )
    parser.add_argument(
        "--forever",
        action = "store_true",
        default = True,
        help = "Run in infinite loop (default, for standalone service)",
    )
    
    args = parser.parse_args()
    
    if args.once:
        run_once()
        sys.exit(0)
    else:
        run_forever()
