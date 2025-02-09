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

scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

# get current screen resolution
def get_screen_resolution():
    monitor = get_monitors()[0]  # Get the first monitor (primary screen)
    print("your monitor width and height:", monitor.width, monitor.height)
    return monitor.width, monitor.height

# Check if the current time is within market hours (9:30 AM to 5:00 PM)
def is_market_open():
    now = datetime.now()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=17, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close
    
if not is_market_open():
    print("Market is closed. Waiting for market hours... term will be ending")
    sys.exit()
    
# Get screen resolution
screen_width, screen_height = get_screen_resolution()

# create Session Headless does not work at the moment it must be set to false.
cs = session.ChaseSession(
   headless=False, width=screen_width/scaleFactor, height=screen_height/scaleFactor
)

login_one = cs.login("your_username", "your_password", "last_four_of_your_cell_phone")

# Login to Chase.com
all_accounts = acc.AllAccount(cs)

if all_accounts.account_connectors is None:
    sys.exit("Failed to get account connectors exiting script...")

# Get Account Identifiers
print("====================================")
print(f"Account Identifiers: {all_accounts.account_connectors}")

# Get Base Account Details
account_ids = list(all_accounts.account_connectors.keys())

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

def CHASEfetch_real_time_quotes(stocksToCheck, retry_attempts=2, delay_between_retries=5):
    """
    Fetches real-time stock quotes and retries the operation if an error occurs.
    
    Args:
        stocksToCheck (list): List of stocks to check.
        retry_attempts (int): Maximum number of retry attempts.
        delay_between_retries (int): Delay in seconds between retry attempts.
    
    Returns:
        dict: A dictionary containing stock data for each stock, or None if all attempts fail.
    """
    attempt = 0
    while attempt < retry_attempts:
        try:
            results = {}
            for stock in stocksToCheck:
                symbol_quote = sym.SymbolQuote(account_ids[0], cs, stock)
                results[stock] = {
                    "security_description": symbol_quote.security_description,
                    "ask_price": symbol_quote.ask_price,
                    "last_trade_price": symbol_quote.last_trade_price,
                    "as_of_time": symbol_quote.as_of_time
                }
            return results  # Return the results if successful

        except Exception as e:
            attempt += 1
            print(f"Error occurred: {e}. Retrying... (Attempt {attempt}/{retry_attempts})")

            if attempt >= retry_attempts:
                print(f"Failed after {retry_attempts} attempts.")
                return None  # Return None or {} to indicate failure

# def CHASEfetch_real_time_quotes(stocksToCheck):
#     def wait_for_element(selector, max_attempts=5, delay=5):
#         attempts = 0
#         while attempts < max_attempts:
#             try:
#                 element = cs.page.wait_for_selector(selector, state="visible", timeout=10000)
#                 if element:
#                     print(f"Element {selector} found!")
#                     return element
#             except PlaywrightTimeoutError:
#                 attempts += 1
#                 print(f"Attempt {attempts}: Element {selector} not found, retrying in {delay} seconds...")
#                 time.sleep(delay)

#         raise Exception(f"Failed to locate element {selector} after {max_attempts} attempts.")

#     try:
#         results = {}
#         for stock in stocksToCheck:
#             # Retry logic for waiting for the stock quote element
#             wait_for_element("#equityQuoteDetails > section")

#             # Fetch the stock data
#             symbol_quote = sym.SymbolQuote(account_ids[0], cs, stock)

#             # Store the fetched data in the results dictionary
#             results[stock] = {
#                 "security_description": symbol_quote.security_description,
#                 "ask_price": symbol_quote.ask_price,
#                 "last_trade_price": symbol_quote.last_trade_price,
#                 "as_of_time": symbol_quote.as_of_time
#             }

#         # Return the results for comparison or further use
#         return results

#     except PlaywrightTimeoutError as e:
#         # Handle any timeout errors that occur while fetching data
#         print(f"Timeout while fetching the stock quote: {e}")
#         raise

def should_make_trade(chase_data, tv_data, stock_symbol):
    """
    Determines if a trade should be made based on the provided Chase and TradingView data.
    
    Args:
        chase_data (dict): A dictionary containing the real-time stock data from Chase.
        tv_data (dict): A dictionary containing the technical analysis data from TradingView.
        stock_symbol (str): The stock symbol to check the wallet balance for.
    
    Returns:
        bool: True if all trade conditions are met, False otherwise.
    """
    # Get the wallet balance for the current stock
    wallet_balance = wallets[stock_symbol]
    print(f"Wallet balance for {stock_symbol}: {wallet_balance}")
    print(chase_data, tv_data)
    rsi = tv_data['RSI']
    Recommendation = tv_data["Recommendation"]
    high = tv_data['High']
    low = tv_data['Low']
    last_trade = chase_data['last_trade_price']
    buy_signals = tv_data['Buy']
    sell_signals = tv_data['Sell']
    
    # # Condition 1: RSI under 50
    # if rsi >= 75:
    #     print(f"{stock_symbol} trade skipped: RSI is too high ({rsi})")
    #     return False
    
    # Condition 2: ((high * 2/3) + (low * 1/3)) / last trade >= 0.02 this is fake 
    # price_condition = ((high * 2 / 3) + (low * 1 / 3)) / last_trade
    # print(high,low, low, last_trade, ((high * 2 / 3) + (low / 3)), ((high * 2 / 3) + (low * 1 / 3)) / last_trade, price_condition < 0.02)
    # if price_condition < 1.002:
    #     print(f"{stock_symbol} trade skipped: Price condition not met (value = {price_condition})")
    #     return False
    
    # # Condition 3: Buy - Sell < 6:
    if(buy_signals-sell_signals < 6):
        print(f"{stock_symbol} trade skipped: Not enough buy signals (Buy: {buy_signals}, Sell: {sell_signals})")
        return False
    
    # if(Recommendation != ("STRONG_BUY" or "BUY")): 保險一點
    if(Recommendation != ("STRONG_BUY" or "BUY")):
        return False
    
    # All conditions met, return True and print success message
    print(f"Trade conditions met for {stock_symbol}. Proceeding with trade.")
    return True

from realtime import TVfetch_technical_analysis

# 下10%
stocksToCheck = ["NVDL"]
wallets = {symbol: 10000 for symbol in stocksToCheck}

# Placeholder for tracking trades
trades = []
sell_orders = {}  # To track sell orders with target prices

# Function to record a trade in a JSON file and Excel
def record_trade(trade_data):
    global trades
    trades.append(trade_data)
    
    # Save trades to JSON
    with open("trades_log.json", 'w') as f:
        json.dump(trades, f, indent=4)
    
    # Save trades to Excel
    df = pd.DataFrame(trades)
    df.to_excel("trades_log.xlsx", index=False)

def determine_sell_price(price, rsi, high, low, recommendation):
    # Base target sell price as a percentage above buy price
    sell_price_threshold = price * 1.05  # Default to 5% increase

    # Adjust based on RSI
    if rsi > 70:
        # If RSI is high (overbought), reduce target sell price for a quicker exit
        sell_price_threshold = price * 1.03  # More conservative, 3% increase
    elif rsi < 30:
        # If RSI is low (oversold), aim for a higher sell price
        sell_price_threshold = price * 1.07  # More aggressive, 7% increase

    # Adjust based on recommendation
    if recommendation == "STRONG_BUY":
        # Aim for a higher sell price if the recommendation is strong
        sell_price_threshold = price * 1.10  # Target 10% increase
    elif recommendation == "BUY":
        # Moderate increase for a normal "BUY" recommendation
        sell_price_threshold = price * 1.05  # Stick with 5%

    # Compare to High/Low prices and adjust accordingly
    mid_price = (high + low) / 2
    # potentially higher
    print(sell_price_threshold, high, high * 0.98)
    # if sell_price_threshold > high:
    #     # Don't set the sell price higher than the recent high
    #     sell_price_threshold = high * 0.98  # Aim slightly below the high for a quick sell
    if sell_price_threshold < mid_price:
        # Ensure the sell price is not below the average of high/low
        sell_price_threshold = mid_price

    return round(sell_price_threshold, 2)  # Return rounded to 2 decimal places

# Function to simulate a trade
def make_trade(stock_symbol, chase_data, tv_data):
    global wallets
    amount = 1  # Buy 1 unit per trade
    price = round(chase_data['last_trade_price'], 2)  # Round buy price to 2 decimal places
    trade_cost = amount * price

    # Check if the wallet has enough funds to buy
    if wallets[stock_symbol] >= trade_cost:
        # Execute the buy trade
        wallets[stock_symbol] -= trade_cost
        trade_data = {
            "symbol": stock_symbol,
            "trade_type": "buy",
            "amount": amount,
            "price": price,  # Rounded price
            "wallet_after_trade": round(wallets[stock_symbol], 2),  # Round wallet balance
            "timestamp": str(datetime.now())
        }
        record_trade(trade_data)
        print(f"Trade executed: Bought {amount} of {stock_symbol} at {price}, Wallet balance: {wallets[stock_symbol]}")

        # Determine a dynamic sell price based on RSI, high/low prices, and recommendation
        sell_price_threshold = determine_sell_price(price, tv_data['RSI'], tv_data['High'], tv_data['Low'], tv_data['Recommendation'])

        # Set the sell order
        sell_orders[stock_symbol] = {
            "amount": amount,
            "target_price": sell_price_threshold,  # Dynamic sell price
            "timestamp": str(datetime.now())
        }
        print(f"Sell order placed for {stock_symbol} at target price {sell_price_threshold}")
        return price  # Return the final trade price
    else:
        print(f"Not enough funds to buy {stock_symbol}")
        return None  # Return None if trade is not executed

# Function to check sell orders and execute when conditions are met
def execute_sell_orders(chase_data):
    global wallets
    for stock, order in list(sell_orders.items()):
        current_price = round(chase_data[stock]['last_trade_price'], 2)  # Round sell price to 2 decimals
        target_price = order['target_price']

        # If the current price has reached the target price, sell the stock
        if current_price >= target_price:
            sell_value = round(order['amount'] * current_price, 2)  # Round sell value
            wallets[stock] += sell_value
            wallets[stock] = round(wallets[stock], 2)  # Round wallet balance
            trade_data = {
                "symbol": stock,
                "trade_type": "sell",
                "amount": order['amount'],
                "price": current_price,  # Rounded sell price
                "wallet_after_trade": wallets[stock],  # Rounded wallet balance
                "timestamp": str(datetime.now())
            }
            record_trade(trade_data)
            print(f"Sell order executed for {stock} at {current_price}, Wallet balance: {wallets[stock]}")

            # Remove the completed sell order
            del sell_orders[stock]


# Main loop to fetch data during market hours and execute trades
while True:
    if not is_market_open():
        print("Market is closed. Waiting for market hours... term will be ending")
        sys.exit()

    Chase_data = CHASEfetch_real_time_quotes(stocksToCheck)  # Fetch real-time quotes

    if Chase_data is None:
        print("Failed to fetch Chase data, skipping this iteration.")
        continue  # Skip this iteration if Chase data is not available

    TV_data = TVfetch_technical_analysis(stocksToCheck)  # Fetch technical analysis

    for stock in stocksToCheck:
        chase_data = Chase_data.get(stock)  # Safely access data from the dictionary
        if chase_data is None:
            print(f"No data found for {stock} in Chase_data.")
            continue  # Skip to the next stock if data is None

        if stock not in TV_data.index:
            print(f"{stock} not found in TV_data.")
            continue 
        
        tv_data = TV_data.loc[stock]

        # Check if a buy trade should be made and print the wallet balance
        if should_make_trade(chase_data, tv_data, stock):
            make_trade(stock, chase_data, tv_data)
    
    # Check and execute any sell orders
    execute_sell_orders(Chase_data)
    time.sleep(2)