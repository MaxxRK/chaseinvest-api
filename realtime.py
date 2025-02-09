import threading
import time
from tradingview_ta import TA_Handler, Interval
import pandas as pd


# List of stock symbols to request
symbols = ["NVO", "TM", "DIS", "UBER", "JBHT", "KIM"]

# Fetch the analysis for a single symbol and return formatted data

def fetch_technical_analysis(symbol):
    """
    Fetches the technical analysis for a single stock symbol from NASDAQ or NYSE.
    
    Args:
        symbol (str): The stock symbol to fetch analysis for.
    
    Returns:
        dict: A dictionary containing technical analysis data.
    """
    exchanges = ["NASDAQ", "NYSE"]  # Try both exchanges
    for exchange in exchanges:
        try:
            handler = TA_Handler(
                symbol=symbol,
                exchange=exchange,
                screener="america",
                interval=Interval.INTERVAL_1_MINUTE
            )

            analysis = handler.get_analysis()

            return {
                'Symbol': symbol,
                'Exchange': exchange,
                'Recommendation': analysis.summary.get('RECOMMENDATION', 'N/A'),
                'Buy': analysis.summary.get('BUY', 0),
                'Sell': analysis.summary.get('SELL', 0),
                'Neutral': analysis.summary.get('NEUTRAL', 0),
                'High': analysis.indicators.get('high', None),
                'Low': analysis.indicators.get('low', None),
                'RSI': analysis.indicators.get('RSI', None),
                'Volume': analysis.indicators.get('volume', 0)
            }

        except Exception as e:
            continue  # Try the next exchange if this one fails

    return {"Symbol": symbol, "Error": f"Error fetching data for {symbol}: Not found on NASDAQ or NYSE"}

def TVfetch_technical_analysis(symbols):
    """
    Fetches technical analysis for multiple stock symbols concurrently using threading.
    
    Args:
        symbols (list): List of stock symbols to fetch technical analysis for.
    
    Returns:
        pd.DataFrame: DataFrame containing technical analysis details for the given symbols.
    """
    threads = []
    results = {}  # Dictionary to store results
    lock = threading.Lock()

    def worker(symbol):
        analysis_data = fetch_technical_analysis(symbol)
        with lock:
            results[symbol] = analysis_data

    for symbol in symbols:
        thread = threading.Thread(target=worker, args=(symbol,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    df = pd.DataFrame.from_dict(results, orient='index')
    return df

# Displaying the DataFrame
# import ace_tools as tools
# tools.display_dataframe_to_user(name="TradingView Analysis", dataframe=data)

def simulate_fetching():
    try:
        while True:
            TV_data = TVfetch_technical_analysis(symbols)   # Fetch all symbols and print side by side
            print(TV_data)
            # print(TV_data.loc["NVDL"]['RSI'])
            time.sleep(2)  # Pause for 2 seconds before the next fetch
    except KeyboardInterrupt:
        print("Program interrupted, stopping real-time data fetching.")

# simulate_fetching()