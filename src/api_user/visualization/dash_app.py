import sys
from pathlib import Path
import json
from dash_extensions import WebSocket
import pandas as pd
import plotly.express as px

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from src.api_user.visualization import (
    # Core components
    register_callbacks,
    # Data functions
    fetch_historical_data,
    get_available_date_range,
    COLORS,
    PLOT_LAYOUT
)
from .layout_historical import create_layout_historical

import dash
from dash import html, dcc, Output, Input
import dash_bootstrap_components as dbc
Y_VALUE = "close"

def create_app():
    """Create and configure the Dash application."""
    # Default trading pair
    TRADING_PAIR = "BTCUSDT"

    # Get the full date range
    min_date, max_date = get_available_date_range()
    print(f"Available date range: {min_date} to {max_date}")

    # Fetch the dataset for the dashboard
    df = fetch_historical_data()
    if not df.empty:
        print("Sample data:")
        print(df[["open_datetime", "close_datetime", "open", "close"]].head())
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

    # Set the title of the app
    app.title = "Crypto Dashboard"

    # Set up the layout using the historical layout component
   # app.layout = create_layout_historical(df, TRADING_PAIR, COLORS)
    data_points = []
    app.layout = html.Div([
        html.H2("Real-time Line Plot"),
        dcc.Graph(id="live-graph"),
        WebSocket(id="ws", url=f'ws://localhost:8000/ws/stream/{TRADING_PAIR}'),  # adjust URL if needed
    ])

    # Register callbacks
    # register_callbacks(app, fetch_historical_data)

    @app.callback(
        Output("live-graph", "figure"),
        [Input("ws", "message")],
    )
    def update_graph(ws_message):
        if not ws_message or "data" not in ws_message:
            return dash.no_update

        try:
            message = json.loads(ws_message["data"])
            
            # If there's an error in the message, log it and return no update
            if "error" in message:
                print(f"Error from WebSocket ({message.get('symbol', 'unknown')}): {message['error']}")
                return dash.no_update
                
            # Get the data list from the message
            if "data" not in message or not isinstance(message["data"], list):
                print(f"Unexpected message format: {message}")
                return dash.no_update
                
            data = message["data"]
            symbol = message.get("symbol", "UNKNOWN")
            
            if not data:
                print(f"No data received for {symbol}")
                return dash.no_update
                
            df = pd.DataFrame(data)
            
            # Check if required columns exist
            required_columns = {'ts', Y_VALUE}
            missing_columns = required_columns - set(df.columns)
            
            if missing_columns:
                print(f"\n=== WARNING: Missing required columns: {missing_columns} ===")
                print("Available columns:", df.columns.tolist())
                
                # Handle missing timestamp
                if 'ts' in missing_columns:
                    ts_columns = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower() or 'ts' in col.lower()]
                    if ts_columns:
                        print(f"Found potential timestamp columns: {ts_columns}")
                        df = df.rename(columns={ts_columns[0]: 'ts'})
                        print(f"Renamed column '{ts_columns[0]}' to 'ts'")
                        missing_columns.remove('ts')
                    else:
                        print("No timestamp column found. Using index.")
                        df['ts'] = df.index
                
                # Handle missing Y_VALUE
                if Y_VALUE in missing_columns:
                    value_columns = [col for col in df.columns if 'change' in col.lower() or 'value' in col.lower() or 'price' in col.lower()]
                    if value_columns:
                        print(f"Found potential value columns: {value_columns}")
                        df = df.rename(columns={value_columns[0]: Y_VALUE})
                        print(f"Using column '{value_columns[0]}' as {Y_VALUE}")
                        missing_columns.remove(Y_VALUE)
                    else:
                        print(f"No {Y_VALUE} column found. Using zeros.")
                        df[Y_VALUE] = 0.0
            
            # Ensure data types are correct
            if 'ts' in df.columns and pd.api.types.is_string_dtype(df['ts']):
                print("\nConverting timestamp to datetime")
                df['ts'] = pd.to_datetime(df['ts'])
            
            if Y_VALUE in df.columns:
                df[Y_VALUE] = pd.to_numeric(df[Y_VALUE], errors='coerce').fillna(0.0)
            
            # Sort by timestamp
            df = df.sort_values('ts')
            
            print("\n=== Processed DataFrame ===")
            print(f"Columns: {df.columns.tolist()}")
            print(f"First row: {df.iloc[0].to_dict() if not df.empty else 'Empty DataFrame'}")
            print(f"First timestamp: {df['ts'].iloc[0] if not df.empty else 'N/A'}")
            print(f"Last timestamp: {df['ts'].iloc[-1] if not df.empty else 'N/A'}")
            print(f"{Y_VALUE} range: {df[Y_VALUE].min() if not df.empty else 'N/A'} to {df[Y_VALUE].max() if not df.empty else 'N/A'}")
            
        except Exception as e:
            print(f"\n=== ERROR in update_graph ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            traceback.print_exc()
            return dash.no_update
        
        # Create the plot
        fig = px.line(
            df, 
            x="ts", 
            y=Y_VALUE, 
            title=f"{Y_VALUE} Over Time",
            labels={"ts": "Time", Y_VALUE: Y_VALUE},
            markers=True
        )
        
        # Ensure ts is datetime
        if not df.empty:
            df['ts'] = pd.to_datetime(df['ts'])
            latest_time = df['ts'].max()
            # Calculate the start time for the default 15-minute view
            start_time = latest_time - pd.Timedelta(minutes=15)
            # Convert to datetime strings for the range
            x_range = [start_time, latest_time]
        else:
            x_range = None
            
        # Improve x-axis formatting
        fig.update_layout(
            xaxis=dict(
                type='date',
                tickformat='%H:%M:%S',  # Show time in hours:minutes:seconds
                rangeslider_visible=True,
                range=x_range,  # Focus on last 15 minutes by default
                rangeselector=dict(
                    buttons=list([
                        dict(count=15, label="15m", step="minute", stepmode="backward"),
                        dict(count=1, label="1h", step="hour", stepmode="backward"),
                        dict(count=6, label="6h", step="hour", stepmode="backward"),
                        dict(count=1, label="1d", step="day", stepmode="backward"),
                        dict(step="all")
                    ])
                )
            ),
            yaxis_title=Y_VALUE,
            margin=dict(l=50, r=50, t=50, b=100),
            showlegend=True
        )
        
        return fig

    return app

if __name__ == "__main__":
    # This block runs when the script is executed directly
    try:
        # Try relative import first (works when run as a module)
        from . import init_app
    except ImportError:
        # Fall back to absolute import (works when run directly)
        import sys
        from pathlib import Path

        project_root = Path(__file__).parent.parent.parent.parent
        sys.path.insert(0, str(project_root))
        from src.api_user.visualization import init_app

    app = init_app()
    app.run_server(debug=True, host="0.0.0.0", port=8050)
