"""
Command-line interface for sentiment analytics.
Run with: python scripts/sentiment_analytics_cli.py --symbol BTC/USDT --days 30
"""
import argparse
import json
import logging
from datetime import datetime, timezone, timedelta
from src.alerts.config import AlertSettings
from src.alerts.services.sentiment_analytics import SentimentAnalyticsService

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description = "Sentiment Analytics CLI")
    parser.add_argument("--symbol", type = str, required = True, help = "Trading pair (e.g., BTC/USDT)")
    parser.add_argument("--days", type = int, default = 30, help = "Number of days to analyze")
    parser.add_argument(
        "--action", type = str, default = "correlation", 
        choices = ["correlation", "trend", "anomalies", "training_data"], 
        help = "Analysis action to perform"
    )
    parser.add_argument("--output", type = str, default = None, help = "Output file (JSON)")
    args = parser.parse_args()
    # load settings
    settings = AlertSettings()
    mongo_uri = settings.mongo_uri or "mongodb://localhost:27017"
    # initialize analytics service
    analytics = SentimentAnalyticsService(mongo_uri)
    # calculate time range
    end_time = datetime.now(timezone.utc)
    start_time = end_time - timedelta(days = args.days)
    logger.info(f"Analyzing {args.symbol} from {start_time} to {end_time}")
    # perform action
    if args.action == "correlation":
        result = analytics.calculate_correlation(
            symbol = args.symbol,
            start_time = start_time,
            end_time = end_time,
        )
    elif args.action == "trend":
        result = analytics.detect_sentiment_trend(
            symbol = args.symbol,
            start_time = start_time,
            end_time = end_time,
        )
    elif args.action == "anomalies":
        result = analytics.get_sentiment_anomalies(
            symbol = args.symbol,
            start_time = start_time,
            end_time = end_time,
        )
    elif args.action == "training_data":
        X, y = analytics.prepare_training_data(
            symbol = args.symbol,
            start_time = start_time,
            end_time = end_time,
        )
        result = {
            "features_shape": X.shape,
            "targets_shape": y.shape,
            "sample_features": X[:5].tolist() if len(X) > 0 else [],
            "sample_targets": y[:5].tolist() if len(y) > 0 else [],
        }
    else:
        result = {"error": "Unknown action"}
    # output
    if args.output:
        with open(args.output, "w") as f:
            json.dump(result, f, indent = 2, default = str)
        logger.info(f"Results saved to {args.output}")
    else:
        print(json.dumps(result, indent = 2, default = str))


if __name__ == "__main__":
    main()
