import requests
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
import time
import argparse
import json
import os

# Define the resistance lines file
RESISTANCE_FILE = "resistance_lines.json"
# Load resistance lines from file at the start of the script
def load_resistance_lines():
    """Load resistance lines from a JSON file."""
    if os.path.exists(RESISTANCE_FILE):
        with open(RESISTANCE_FILE, "r") as file:
            try:
                data = json.load(file)
                if isinstance(data, dict):  # Ensure data is a dictionary
                    return data
            except json.JSONDecodeError:
                print("Error: Resistance lines file is corrupted. Initializing as empty dictionary.")
    return {}  # Return an empty dictionary if file doesn't exist or is corrupted


def save_resistance_lines():
    """Save resistance lines to a JSON file."""
    with open(RESISTANCE_FILE, "w") as file:
        json.dump(resistance_lines, file, indent=4)

# Global list to store resistance lines
resistance_lines = load_resistance_lines()

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
import numpy as np

def plot_klines(df, symbol):
    """
    Plot Kline data with resistance lines spanning the entire chart frame.
    """
    global resistance_lines

    # Define the date range of the chart
    start_date = df.index.min()
    end_date = df.index.max()

    # Prepare the resistance lines
    relevant_resistances = []
    if symbol in resistance_lines:
        relevant_resistances = resistance_lines[symbol]  # Use all resistance lines for the symbol

    # Prepare additional lines for mplfinance
    additional_lines = []
    for line in relevant_resistances:
        price = line["price"]

        # Create a ydata array that spans the entire chart
        ydata = [price] * len(df.index)  # Constant value for all x-axis points

        additional_lines.append(
            mpf.make_addplot(
                ydata,
                panel=0,  # Main panel
                color="red",  # Resistance line color
                linestyle="-",
            )
        )

    if additional_lines:
        mpf.plot(
            df,
            type="candle",
            style="charles",
            title=f"{symbol} Price Chart",
            volume=True,
            addplot=additional_lines if additional_lines else None
        )
    else:
        mpf.plot(
            df,
            type="candle",
            style="charles",
            title=f"{symbol} Price Chart",
            volume=True
        )


def add_resistance(symbol, price, start_date, end_date):
    """
    Add a resistance line for a specific symbol and save to file.
    """
    global resistance_lines

    # Ensure resistance_lines is a dictionary
    if not isinstance(resistance_lines, dict):
        resistance_lines = {}

    # Ensure the symbol key exists in the dictionary
    if symbol not in resistance_lines:
        resistance_lines[symbol] = []

    # Add the resistance line
    resistance_lines[symbol].append({
        "price": price,
        "start_date": start_date,
        "end_date": end_date
    })

    # Save to file
    save_resistance_lines()
    print(f"Added resistance for {symbol} at ${price} from {start_date} to {end_date}.")

def remove_resistance(symbol, price):
    """
    Remove a resistance line for a specific symbol based on price and save to file.
    """
    global resistance_lines
    if symbol in resistance_lines:
        # Filter out the resistance line with the specified price
        resistance_lines[symbol] = [
            line for line in resistance_lines[symbol] if line["price"] != price
        ]
        # If no resistance lines remain for the symbol, remove the symbol key
        if not resistance_lines[symbol]:
            del resistance_lines[symbol]

        save_resistance_lines()
        print(f"Removed resistance for {symbol} at ${price}.")
    else:
        print(f"No resistance lines found for {symbol}.")


# Main execution
if __name__ == "__main__":
    from datetime import datetime, timedelta
    parser = argparse.ArgumentParser(description="Fetch and display cryptocurrency charts using KuCoin API.")
    parser.add_argument("-s", "--symbol", type=str, required=True, help="Symbol of the asset (e.g., BTC-USDT).")
    parser.add_argument("-g", "--granularity", type=int, required=True, help="Granularity in minutes (e.g., 1, 60, 240).")
    parser.add_argument("-d", "--days", type=int, default=1, help="Number of days of data to fetch (default: 1).")
    parser.add_argument("--add-resistance", nargs=3, metavar=("PRICE", "START_DATE", "END_DATE"),
                        help="Add a resistance line. Format: PRICE START_DATE END_DATE (e.g., 98000 '2024-01-01' '2024-01-10').")
    parser.add_argument("--remove-resistance", type=float, help="Remove a resistance line by price.")
    parser.add_argument("--view-chart", action="store_true", help="View the chart with resistance lines.")
    

    args = parser.parse_args()

    # Validate CLI arguments
    if not (args.add_resistance or args.remove_resistance or args.view_chart):
        parser.error("You must specify at least one operation (--add-resistance, --remove-resistance, or --view-chart).")




    start_time = datetime.utcnow() - timedelta(days=args.days)
    end_time = datetime.utcnow()
    df = fetch_kucoin_klines(args.symbol, args.granularity, start_time, end_time)

    if df is None:
        print("Failed to fetch market data.")
        exit(1)

    # Process operations
    if args.add_resistance:
        try:
            price = float(args.add_resistance[0])
            start_date = datetime.strptime(args.add_resistance[1], "%Y-%m-%d")
            print('start_date ', start_date)
            end_date = datetime.strptime(args.add_resistance[2], "%Y-%m-%d")
            print('end_date ', end_date)

            if start_date > end_date:
                raise ValueError("Start date must be before or equal to end date.")

            add_resistance(args.symbol, price, start_date.isoformat(), end_date.isoformat())
        except ValueError as e:
            print(f"Invalid resistance input: {e}")
            exit(1)

    if args.remove_resistance:
        remove_resistance(args.symbol, args.remove_resistance)

    if args.view_chart:
        plot_klines(df, args.symbol)