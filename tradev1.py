import sys
from chase import account as acc
from chase import order as och
from chase import session
from chase import symbols as sym
from screeninfo import get_monitors
import ctypes
import time
from datetime import datetime

# Scaling factor and screen resolution setup
scaleFactor = ctypes.windll.shcore.GetScaleFactorForDevice(0) / 100

def get_screen_resolution():
    monitor = get_monitors()[0]  # Get the first monitor (primary screen)
    print("your monitor width and height:", monitor.width, monitor.height)
    return monitor.width, monitor.height

# Get screen resolution
screen_width, screen_height = get_screen_resolution()

# Create Session
cs = session.ChaseSession(
   headless=False, width=screen_width / scaleFactor, height=screen_height / scaleFactor
)

# Login to Chase
login_one = cs.login("your_username", "your_password", "last_four_of_your_cell_phone")

# Access accounts
all_accounts = acc.AllAccount(cs)
if all_accounts.account_connectors is None:
    sys.exit("Failed to get account connectors exiting script...")

account_ids = list(all_accounts.account_connectors.keys())

# Check if the current time is within market hours
def is_market_open():
    now = datetime.now()
    market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = now.replace(hour=17, minute=0, second=0, microsecond=0)
    return market_open <= now <= market_close

# Fetch real-time quotes
def CHASEfetch_real_time_quotes(stocksToCheck):
    for stock in stocksToCheck:
        try:
            symbol_quote = sym.SymbolQuote(account_ids[0], cs, stock)
            print(
                f"{symbol_quote.security_description} ask price {symbol_quote.ask_price}, "
                f"@{symbol_quote.as_of_time} and the last trade was {symbol_quote.last_trade_price}."
            )
        except Exception as e:
            print(f"Error fetching quote for {stock}: {e}")

order = och.Order(cs)
# Place an order (simulate or real)
def place_trade(symbol, qty=1):
    try:
        messages = order.place_order(
            account_ids[0],
            qty,
            och.PriceType.MARKET,
            symbol,
            och.Duration.DAY,
            och.OrderSide.BUY,
            dry_run=True  # Change to False for live trading
        )
        if messages["ORDER CONFIRMATION"] != "":
            print(messages["ORDER CONFIRMATION"])
        else:
            print(messages)
    except Exception as e:
        print(f"Error placing order: {e}")

# Main loop to run both tasks
def main_loop():
    stocksToCheck = ["TSLL", "NVDL"]
    while True:
        if is_market_open():
            # Fetch quotes every 2 seconds
            CHASEfetch_real_time_quotes(stocksToCheck)
        else:
            print("Market is closed. Waiting for market hours...")
        
        # Optionally allow trading based on user input
        # user_input = input("Type 'trade' to place an order or press Enter to skip: ").lower()
        # if user_input == 'trade':
        #     place_trade("INTC")
        
        # Pause before next iteration (or waiting for next market open)
        time.sleep(2)

# Start the loop
try:
    main_loop()
except KeyboardInterrupt:
    print("Program interrupted, stopping real-time data fetching.")
