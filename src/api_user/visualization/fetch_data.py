import os
import requests
import pandas as pd
from typing import Optional, Tuple
from datetime import datetime, timedelta, timezone

# Get API base URL from environment variables with default
API_BASE_URL = os.getenv('API_BASE_URL', 'http://crypto_fastapi:8000')

def get_available_date_range() -> Tuple[datetime, datetime]:
    """
    Fetch the available date range from the FastAPI endpoint.
    
    Returns:
        Tuple[datetime, datetime]: (min_date, max_date) from the API
    """
    try:
        # Use the /market/range endpoint to get the date range
        response = requests.get(f"{API_BASE_URL}/market/range")
        response.raise_for_status()
        
        data = response.json()
        
        # Parse the dates from the response
        min_date = datetime.fromisoformat(data['min_date']).replace(tzinfo=timezone.utc)
        max_date = datetime.fromisoformat(data['max_date']).replace(tzinfo=timezone.utc)
        
        return min_date, max_date
        
    except Exception as e:
        print(f"Error fetching date range from API: {e}")
        # Fallback to default range if API call fails
        end_date = datetime.now(timezone.utc)
        return end_date - timedelta(days=7), end_date

def fetch_historical_data(
    trading_pair: str = "BTCUSDT",
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None
) -> pd.DataFrame:
    """
    Fetch historical data for a specific trading pair from the FastAPI endpoint.
    
    Args:
        trading_pair: The trading pair to fetch data for (e.g., 'BTCUSDT')
        start_time: Optional start time for the data range
        end_time: Optional end time for the data range (defaults to latest available data)
        
    Returns:
        pd.DataFrame: DataFrame containing the historical OHLCV data
    """
    try:
        # Prepare query parameters
        params = {
            'symbol': trading_pair.upper(),
            'interval': '1d'  # Default interval, adjust if needed
        }
        
        if start_time:
            params['start_time'] = int(start_time.timestamp() * 1000)  # Convert to milliseconds
        if end_time:
            params['end_time'] = int(end_time.timestamp() * 1000)  # Convert to milliseconds
        
        response = requests.get(f"{API_BASE_URL}/market/ohlcv", params=params)
        response.raise_for_status()
        
        data = response.json()
        
        if not data:
            print(f"No data found for {trading_pair} in the specified date range")
            return pd.DataFrame()
        
        df = pd.DataFrame(data)
        
        if 'open_time' in df.columns:
            df['open_time'] = pd.to_datetime(df['open_time'], unit='ms')
        if 'close_time' in df.columns:
            df['close_time'] = pd.to_datetime(df['close_time'], unit='ms')
        
        # Ensure numeric columns are numeric
        numeric_cols = ['open', 'high', 'low', 'close', 'volume', 'quote_asset_volume', 
                       'number_of_trades', 'taker_buy_base_asset_volume', 
                       'taker_buy_quote_asset_volume']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Sort by open_time if it exists
        if 'open_time' in df.columns:
            df = df.sort_values('open_time')
            print(f"Fetched {len(df)} records for {trading_pair} from {df['open_time'].min()} to {df['open_time'].max()}")
        else:
            print(f"Fetched {len(df)} records for {trading_pair}")
            
        return df
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"Unexpected error: {e}")
        return pd.DataFrame()