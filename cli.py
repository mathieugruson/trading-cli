import requests
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import time
import argparse

# Function to fetch Kline data from KuCoin API
def fetch_kucoin_klines(symbol, granularity, start_time=None, end_time=None):
    url = "https://api-futures.kucoin.com/api/v1/kline/query"
    params = {
        "symbol": symbol,
        "granularity": granularity,
    }

    if start_time:
        params["from"] = int(start_time.timestamp() * 1000)  # Convert to milliseconds
    if end_time:
        params["to"] = int(end_time.timestamp() * 1000)  # Convert to milliseconds

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()["data"]
        # Convert to DataFrame
        df = pd.DataFrame(
            data, 
            columns=["time", "open", "high", "low", "close", "volume"]
        )
        df["time"] = pd.to_datetime(df["time"], unit="ms")
        df.set_index("time", inplace=True)
        df = df.astype(float)
        return df
    else:
        print("Error:", response.json())
        return None

# Function to plot Kline data
def plot_klines(df, symbol):
    mpf.plot(df, type="candle", style="charles", title=f"{symbol} Price Chart", volume=True)

# Main execution
if __name__ == "__main__":
    from datetime import datetime, timedelta
    parser = argparse.ArgumentParser(description="Fetch and display cryptocurrency charts using KuCoin API.")
    parser.add_argument(
        "-s", "--symbol", type=str, required=True, 
        help="Symbol of the asset (e.g., BTC-USDT, .KXBT)."
    )
    parser.add_argument(
        "-g", "--granularity", type=int, required=True,
        help="Granularity in minutes (e.g., 1, 5, 15, 30, 60, 120, 240, 480, 720, 1440)."
    )
    parser.add_argument(
        "-d", "--days", type=int, default=1, 
        help="Number of days of data to fetch (default: 1)."
    )
    
    args = parser.parse_args()
    # Parameters
    symbol = args.symbol
    granularity = args.granularity
    start_time = datetime.utcnow() - timedelta(days=2)  # 2 days ago
    end_time = datetime.utcnow()  # Now

    # Fetch and plot data
    df = fetch_kucoin_klines(symbol, granularity, start_time, end_time)
    if df is not None:
        plot_klines(df, symbol)
