import threading
import time
from tradingview_ta import TA_Handler, Interval
import pandas as pd

# List of stock symbols to request
symbols = ["TSLL", "NVDL", "MELI"]

# Fetch the analysis for a single symbol and return formatted data

def fetch_technical_analysis(symbol):
    """
    Fetches the technical analysis for a single stock symbol and returns the data as a dictionary.
    
    Args:
        symbol (str): The stock symbol to fetch analysis for.
    
    Returns:
        dict: A dictionary containing technical analysis data.
    """
    try:
        # Create a handler for the symbol
        handler = TA_Handler(
            symbol=symbol,
            exchange="NASDAQ",  # Use the correct exchange for the stock
            screener="america",  # Use the correct screener
            interval=Interval.INTERVAL_1_MINUTE  # Set to 1-minute interval
        )

        # Fetch the analysis
        analysis = handler.get_analysis()

        # Return analysis details as a dictionary
        return {
            'Symbol': symbol,
            'Recommendation': analysis.summary['RECOMMENDATION'],
            'Buy': analysis.summary['BUY'],
            'Sell': analysis.summary['SELL'],
            'Neutral': analysis.summary['NEUTRAL'],
            'High': analysis.indicators['high'],
            'Low': analysis.indicators['low'],
            'RSI': analysis.indicators['RSI']
        }

    except Exception as e:
        return {"Symbol": symbol, "Error": f"Error fetching data for {symbol}: {e}"}


def TVfetch_technical_analysis(symbols):
    """
    Fetches technical analysis for multiple stock symbols concurrently using threading 
    and returns the data as a DataFrame.
    
    Args:
        symbols (list): List of stock symbols to fetch technical analysis for.
    
    Returns:
        pd.DataFrame: DataFrame containing technical analysis details for the given symbols.
    """
    try:
        # Fetch the analysis for multiple symbols in separate threads
        threads = []
        results = {}  # Dictionary to store results with stock symbols as keys
        lock = threading.Lock()  # To prevent race conditions when updating results

        def worker(symbol):
            analysis_data = fetch_technical_analysis(symbol)  # Fetch data for the symbol
            with lock:  # Ensure thread-safe access to the shared results dictionary
                results[symbol] = analysis_data

        # Create and start a thread for each symbol
        for symbol in symbols:
            thread = threading.Thread(target=worker, args=(symbol,))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Convert results to a DataFrame
        df = pd.DataFrame.from_dict(results, orient='index')
        return df

    except Exception as e:
        print(f"Error fetching or printing symbols: {e}")
        return pd.DataFrame()


def simulate_fetching():
    try:
        while True:
            TV_data = TVfetch_technical_analysis(symbols)   # Fetch all symbols and print side by side
            print(TV_data)
            # print(TV_data.loc["NVDL"]['RSI'])
            time.sleep(2)  # Pause for 2 seconds before the next fetch
    except KeyboardInterrupt:
        print("Program interrupted, stopping real-time data fetching.")

simulate_fetching()