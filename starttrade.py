import sys
from chase import account as acc
from chase import order as och
from chase import session
from chase import symbols as sym
from screeninfo import get_monitors
import ctypes
import time
from datetime import datetime
import json
import pandas as pd
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from realtime import TVfetch_technical_analysis
from datetime import timedelta
import os
# 8005667636

stocksToCheck = ["PLTU", "KIM", "TSLL", "BRKU", "JPM"]
# stocksToCheck = ["DJT", "TSLL", "NVDL", "ORCL"]
# stocksToCheck = ["DJT", "ARB", "PLTR", "NVDL"]
# stocksToCheck = ["MELI", "DJT", "TSLL", "CNEY", "VCIG"]
# stocksToCheck = ["PLTR"]
# 長記性stocksToCheck = ["CRKN", "WCT", "XCUR", "SBFM", "MTEM", "ADN", "JTAI"]
global amount_to_buy, max_value, factor
amount_to_buy=7000  # Buy 1 unit per trade
max_value = 0 
factor = 2.5

scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100
REFRESH_INTERVAL = 120  # 2 minutes in seconds
last_refresh_time = time.time()
MARKET_CLOSE_TIME = datetime.now().replace(hour=16, minute=0, second=0, microsecond=0)
SELL_WINDOW = timedelta(minutes=15)

# get current screen resolution
def get_screen_resolution():
    monitor = get_monitors()[0]  # Get the first monitor (primary screen)
    print("your monitor width and height:", monitor.width, monitor.height)
    return monitor.width, monitor.height

# Check if the current time is within market hours (9:30 AM to 5:00 PM)
def is_market_open():
    now = datetime.now()
    market_open = now.replace(hour=9, minute=00, second=0, microsecond=0)
    market_close = now.replace(hour=15, minute=30, second=0, microsecond=0)
    # return market_open <= now <= market_close
    return True
    
if not is_market_open():
    print("Market is closed. Waiting for market hours... term will be ending")
    sys.exit()
    
# Get screen resolution
screen_width, screen_height = get_screen_resolution()

# create Session Headless does not work at the moment it must be set to false.
cs = session.ChaseSession(
   headless=False, width=screen_width/scaleFactor, height=screen_height/scaleFactor
)

login_one = cs.login("charliechung88", "your_password", "last_four_of_your_cell_phone")

# Login to Chase.com
all_accounts = acc.AllAccount(cs)

if all_accounts.account_connectors is None:
    sys.exit("Failed to get account connectors exiting script...")

# Get Account Identifiers
print("====================================")
# print(f"Account Identifiers: {all_accounts.account_connectors}")

# Get Base Account Details
account_ids = list(all_accounts.account_connectors.keys())
for account in account_ids:
    symbols = sym.SymbolHoldings(account, cs)
    success = symbols.get_holdings()
    if success: # Initialize max_value to 0 or None if you want to handle no values found

        # Loop through each position and check if it's "Cash and Sweep Funds"
        for position in symbols.positions:
            if position.get("instrumentLongName") == "Cash and Sweep Funds":
                # Get the market value dictionary
                market_value = position.get("marketValue")

                # Check if market_value is a dictionary and contains 'baseValueAmount'
                if isinstance(market_value, dict):
                    temp_value = market_value.get("baseValueAmount", 0)
                    
                    # Update max_value if temp_value is positive and higher than the current max_value
                    if temp_value > 0:
                        max_value = max(max_value, temp_value)

        # Print the maximum value found
        if max_value > 0:
            print(f"Maximum Positive Value for Cash and Sweep Funds: {max_value}")
        else:
            print("No positive values found for Cash and Sweep Funds.")

order = och.Order(cs)
# print("====================================")
# print("ACCOUNT DETAILS")
# print("====================================")
# for account in account_ids:
#     account = acc.AccountDetails(account, all_accounts)
#     print(account.nickname, account.mask, account.account_value)
# print("====================================")

# Get Holdings
# print("====================================")
# print("HOLDINGS")
# for account in account_ids:
#     print("====================================")
#     print(f"Account: {all_accounts.account_connectors[account]}")
#     symbols = sym.SymbolHoldings(account, cs)
#     success = symbols.get_holdings()
#     if success:
#         for i, symbol in enumerate(symbols.positions):
#             if symbols.positions[i]["instrumentLongName"] == "Cash and Sweep Funds":
#                 symbol = symbols.positions[i]["instrumentLongName"]
#                 value = symbols.positions[i]["marketValue"]["baseValueAmount"]
#                 print(f"Symbol: {symbol} Value: {value}")
#             elif symbols.positions[i]["assetCategoryName"] == "EQUITY":
#                 try:
#                     symbol = symbols.positions[i]["positionComponents"][0][
#                         "securityIdDetail"
#                     ][0]["symbolSecurityIdentifier"]
#                     value = symbols.positions[i]["marketValue"]["baseValueAmount"]
#                     quantity = symbols.positions[i]["tradedUnitQuantity"]
#                     print(f"Symbol: {symbol} Value: {value} Quantity: {quantity}")
#                 except KeyError:
#                     symbol = symbols.positions[i]["securityIdDetail"]["cusipIdentifier"]
#                     value = symbols.positions[i]["marketValue"]["baseValueAmount"]
#                     quantity = symbols.positions[i]["tradedUnitQuantity"]
#                     print(f"Symbol: {symbol} Value: {value} Quantity: {quantity}")
#     else:
#         print(f"Failed to get holdings for account {account}")
# print("====================================")

# Loop to continuously fetch real-time data during market hours
# while True:
#     if is_market_open():
#         CHASEfetch_real_time_quotes()
#     else:
#         print("Market is closed. Waiting for market hours...")
#     time.sleep(2)

# ====================== compare chart =================
# oriimport time

def CHASEfetch_real_time_quote(stock, retry_attempts=2, delay_between_retries=5):
    """
    Fetches real-time stock quote for a single stock and retries if an error occurs.
    
    Args:
        stock (str): The stock symbol to fetch data for.
        retry_attempts (int): Maximum number of retry attempts.
        delay_between_retries (int): Delay in seconds between retry attempts.
    
    Returns:
        dict: A dictionary containing stock data for the specified stock, or None if all attempts fail.
    """
    attempt = 0
    while attempt < retry_attempts:
        try:
            symbol_quote = sym.SymbolQuote(account_ids[0], cs, stock)
            return {
                "security_description": symbol_quote.security_description,
                "ask_price": symbol_quote.ask_price,
                "last_trade_price": symbol_quote.last_trade_price,
                "as_of_time": symbol_quote.as_of_time
            }
        except Exception as e:
            attempt += 1
            print(f"Error occurred: {e}. Retrying... (Attempt {attempt}/{retry_attempts})")
            time.sleep(delay_between_retries)
            
    print(f"Failed to fetch data for {stock} after {retry_attempts} attempts.")
    return None  # Return None to indicate failure

def should_make_trade(tv_data, chase_data, stock_symbol, max_value):
    """
    Determines if a trade should be made based on the provided Chase and TradingView data.
    
    Args:
        chase_data (dict): A dictionary containing the real-time stock data from Chase.
        tv_data (dict): A dictionary containing the technical analysis data from TradingView.
        stock_symbol (str): The stock symbol to check the wallet balance for.
        max_value (float): The maximum available value for trading.

    Returns:
        bool: True if all trade conditions are met, False otherwise.
    """

    wallet_balance = wallets.get(stock_symbol, 0)
    print(f"Wallet balance for {stock_symbol}: {wallet_balance}")

    recommendation = tv_data["Recommendation"]
    high = tv_data['High']
    low = tv_data['Low']
    last_trade = chase_data['last_trade_price']
    # buy_signals = tv_data['Buy']
    # sell_signals = tv_data['Sell']
    volume = tv_data.get('Volume', 0)  # Add volume data if available
    price_condition = ((high * 2 / 3) + (low / 3))

    # Condition 1: Minimum funds and price check
    if last_trade < 5:
        print(f"{stock_symbol} trade skipped: Price below threshold (last_trade = {last_trade})")
        return False

    # Condition 2: Volume check
    if volume < 100:  # Example: Only trade stocks with a volume over 100,000
        print(f"{stock_symbol} trade skipped: Low trading volume (volume = {volume})")
        return False

    # Condition 3: Recommendation check
    if recommendation in ["SELL", "STRONG_SELL", "NEUTRAL"]:
    # if recommendation in ["SELL", "STRONG_SELL", "NEUTRAL"]:
        print(f"{stock_symbol} trade skipped: Recommendation not favorable (recommendation = {recommendation})")
        return False

    # Condition 4: Price condition
    if price_condition / last_trade < 1.001:
        print(f"{stock_symbol} trade skipped: (high*3/5 + low*2/5)/last trade < 1.001 (value = {price_condition / last_trade})")
        return False

    # Condition 5: Signal threshold
    # if buy_signals - sell_signals < 6:
    #     print(f"{stock_symbol} trade skipped: Not enough buy signals (Buy: {buy_signals}, Sell: {sell_signals})")
    #     return False

    # All conditions met
    print(f"Trade conditions met for {stock_symbol}. Proceeding with trade.")
    return True


wallets = {symbol: max_value/len(stocksToCheck) for symbol in stocksToCheck}
print(wallets)

# Placeholder for tracking trades
trades = []
sell_orders = {}  # To track sell orders with target prices

# Function to record a trade in a JSON file and Excel

def record_trade(trade_data):
    global trades
    trades.append(trade_data)

    # Get today's date in MM-DD format
    today = datetime.now().strftime("%m-%d")

    # Generate base filename for JSON and Excel
    json_filename_base = f"starttrades_log_{today}"
    excel_filename_base = f"starttrades_log_{today}"

    # Initialize version number
    version = 1

    # Check if a file with the same name already exists, and append version number if needed
    json_filename = f"{json_filename_base}({version}).json"
    excel_filename = f"{excel_filename_base}({version}).xlsx"

    while os.path.exists(json_filename) or os.path.exists(excel_filename):
        version += 1
        json_filename = f"{json_filename_base}({version}).json"
        excel_filename = f"{excel_filename_base}({version}).xlsx"

    # Save trades to JSON with the versioned filename
    with open(json_filename, 'w') as f:
        json.dump(trades, f, indent=4)

    # Save trades to Excel with the versioned filename
    df = pd.DataFrame(trades)
    df.to_excel(excel_filename, index=False)

    print(f"Trade record saved as {json_filename} and {excel_filename}")

def determine_sell_price(buy_price, rsi, high, low, recommendation):
    """
    Determine a dynamic sell price based on technical indicators like RSI, high/low prices, and recommendation.
    
    Args:
        buy_price (float): The price at which the stock was bought.
        rsi (float): The RSI value.
        high (float): The stock's high price.
        low (float): The stock's low price.
        recommendation (str): The recommendation from technical analysis (e.g., "BUY", "STRONG_BUY").
        factor (float): An adjustable multiplier for dynamic sell price calculation.

    Returns:
        float: The calculated sell price threshold.
    """
    # Ensure buy_price and factor are floats
    buy_price = float(buy_price)
    global factor 
    factor = float(factor)

    # Dynamic sell price logic based on the recommendation
    if recommendation == "STRONG_BUY":
        sell_price_threshold = buy_price + buy_price * 0.006 * factor  # Target a 1.2% profit for strong buy
    elif recommendation == "BUY":
        sell_price_threshold = buy_price + buy_price * 0.004 * factor  # Target a 1% profit for buy
    else:
        sell_price_threshold = buy_price + buy_price * 0.001 * factor  # Default to 0.7% profit target

    # # Adjust sell price if RSI indicates overbought or oversold
    # if rsi < 30:  # If RSI is oversold, expect more upside potential
    #     sell_price_threshold = max(sell_price_threshold, low * 1.01 * factor)
    # elif rsi > 80:  # If RSI is overbought, target a quicker sell
    #     sell_price_threshold = min(sell_price_threshold, high * 0.999 * factor)

    return round(sell_price_threshold, 2)

def make_trade(order, stock_symbol, chase_data, tv_data, account_ids):
    """
    Execute a buy trade and set both a stop-loss and take-profit sell order for the specified stock.
    
    Args:
        order (Order): The order object to place the trade.
        stock_symbol (str): The stock symbol for which the trade is to be made.
        chase_data (dict): A dictionary containing the real-time stock data from Chase.
        tv_data (dict): A dictionary containing the technical analysis data from TradingView.
        account_id (str): The account ID to execute the trade.
    
    Returns:
        float or None: The price at which the trade was made, or None if the trade was not executed.
    """
    global wallets
    global amount_to_buy

    price = round(((tv_data['Low'] + tv_data['High']) / 4) + (chase_data['last_trade_price'] / 2), 2)
    trade_cost = amount_to_buy
    print(stock_symbol, price)
    if not price or price > 0:
        amount = max(1, int(amount_to_buy // price))
    else:
        return
    
    try:
        # Step 1: Execute the buy trade
        print(f"Attempting to place a buy order for {stock_symbol} at price {price} with amount {amount}.")
        messages = order.place_order(
            account_ids[0],
            amount,
            och.PriceType.LIMIT,
            stock_symbol,
            och.Duration.DAY,
            och.OrderSide.BUY,
            limit_price=price,
            dry_run=False,  # Set to False to place an actual order
        )
        print("Messages:", messages)
        # Step 2: Confirm the buy order
        if "ORDER CONFIRMATION" in messages and messages["ORDER CONFIRMATION"]:
            wallets[stock_symbol] -= trade_cost
            trade_data = {
                "symbol": stock_symbol,
                "trade_type": "buy",
                "amount": amount,
                "price": price,
                "wallet_after_trade": round(wallets[stock_symbol], 2),
                "timestamp": str(datetime.now())
            }
            record_trade(trade_data)
            print(f"Buy order executed for {stock_symbol}: Bought {amount} at {price}. Wallet balance: {wallets[stock_symbol]}")

            # Determine the take-profit price dynamically
            take_profit_price = determine_sell_price(
                buy_price=price,
                rsi=tv_data['RSI'],
                high=tv_data['High'],
                low=tv_data['Low'],
                recommendation=tv_data['Recommendation']
            )

            # Step 3: Place a take-profit sell order
            print(f"stop for experiment Placing a take-profit order for {stock_symbol} at {take_profit_price}")
            take_profit_messages = order.place_order(
                account_ids[0],
                amount,
                och.PriceType.LIMIT,
                stock_symbol,
                och.Duration.DAY,
                och.OrderSide.SELL,
                limit_price=take_profit_price,
                dry_run=False,
            )

            if "ORDER CONFIRMATION" in take_profit_messages and take_profit_messages["ORDER CONFIRMATION"]:
                print(f"Take-profit order placed for {stock_symbol} at {take_profit_price}")
            else:
                print(f"Failed to place take-profit order for {stock_symbol}. Response: {take_profit_messages}")

        else:
            print(f"Failed to place buy order for {stock_symbol}. Buy response: {messages}")
        return price

    except Exception as e:
        print(f"Error during trade for {stock_symbol}: {e}")
        return None
    
def sell_all_positions(account_ids, all_accounts, order):
    """
    Sells all open positions at market price at the end of the day based on holdings.

    Args:
        account_ids (list): List of account IDs.
        all_accounts (AllAccount): Instance of AllAccount for account information.
        order (Order): The order object to place trades.

    Returns:
        None
    """
    print("Executing end-of-day sell for all positions...")
    
    for account in account_ids:
        print(f"Checking holdings for account: {all_accounts.account_connectors[account]}")
        symbols = sym.SymbolHoldings(account, cs)
        success = symbols.get_holdings()
        
        if success:
            for position in symbols.positions:
                # Ensure the position is an equity with a positive quantity
                if position.get("assetCategoryName") == "EQUITY":
                    try:
                        symbol = position["positionComponents"][0]["securityIdDetail"][0]["symbolSecurityIdentifier"]
                        quantity = position["tradedUnitQuantity"]

                        if quantity > 0:
                            # Place the market sell order for the available quantity
                            print(f"Placing market sell order for {symbol}, Quantity: {round(quantity)}")
                            messages = order.place_order(
                                account,
                                round(quantity),  # Sell all available units
                                och.PriceType.MARKET,  # Market order for immediate execution
                                symbol,
                                och.Duration.DAY,
                                och.OrderSide.SELL,  # Standard SELL order for specific quantity
                                dry_run=False  # Execute the actual sell
                            )
                            print(f"Sell order placed for {symbol}, Quantity: {quantity}")
                        else:
                            print(f"No quantity to sell for {symbol}")

                    except KeyError as e:
                        print(f"Failed to extract symbol or quantity: {e}")

                else:
                    print(f"Skipping non-equity asset: {position.get('instrumentLongName', 'Unknown')}")

        else:
            print(f"Failed to get holdings for account {account}")

    print("End-of-day sell process completed.")

# Main loop to fetch data during market hours and execute trades
while True:
    # Check if market is open
    if not is_market_open():
        print("Market is closed. Exiting.")
        sell_all_positions(account_ids, all_accounts, order)
        sys.exit()

    # current_time = datetime.now()
    # if MARKET_CLOSE_TIME - current_time <= SELL_WINDOW:
    #     # Execute sell all if within the window before close
    #     sell_all_positions(account_ids[0])
    #     print("End-of-day sell executed. Exiting.")
    #     sys.exit()  # Exit af

    # Check if 15 minutes have passed since the last refresh
    current_time = time.time()
    if current_time - last_refresh_time > REFRESH_INTERVAL:
        print("Refreshing data due to timeout...")
        # Refresh logic or reload session/page
        
        tempStockToCheck = ["TSLL"]
        CHASEfetch_real_time_quote(tempStockToCheck)

        last_refresh_time = current_time  # Reset the last refresh time after refreshing

    # Fetch technical analysis data
    TV_data = TVfetch_technical_analysis(stocksToCheck)
    
    for stock in stocksToCheck:
        if stock not in TV_data.index:
            print(f"{stock} not found in TV_data.")
            continue 
        tv_data = TV_data.loc[stock]

        # Check if a buy trade should be made
        chase_data = CHASEfetch_real_time_quote(stock)
        
        if max_value > 3000 and chase_data and should_make_trade(tv_data, chase_data, stock, max_value):
            last_refresh_time = time.time()
            print("Trade made, refresh timer reset.")
            # Place the trade
            make_trade(order, stock, chase_data, tv_data, account_ids)

    # Sleep for a short period before checking again
    time.sleep(5)