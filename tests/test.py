import sys

from chase import account as acc
from chase import order as och
from chase import session
from chase import symbols as sym

# create Session
cs = session.ChaseSession(persistant_session=True, docker=False)

# Login to Chase.com
login = cs.login("your_username", "your_password", "last_four_of_your_cell_phone")

if login is False:
    sys.exit("Failed to login to chase.com")

# Make all account object
all_accounts = acc.AllAccount(cs)

if all_accounts.account_connectors is None:
    sys.exit("Failed to get account connectors exiting script...")

# Get Account Identifiers
print("====================================")
print(f"Account Identifiers: {all_accounts.account_connectors}")

# Get Base Account Details
account_ids = list(all_accounts.account_connectors.keys())

print("====================================")
print("ACCOUNT DETAILS")
print("====================================")
for account in account_ids:
    account = account.AccountDetails(account, all_accounts)
    print(account.nickname, account.mask, account.account_value)
print("====================================")

# Get Holdings
print("====================================")
print("HOLDINGS")
for account in account_ids:
    print("====================================")
    print(f"Account: {account}")
    symbols = sym.SymbolHoldings(account, cs)
    success = symbols.get_holdings()
    if success:
        for i, symbol in enumerate(symbols.positions):
            if symbols.positions[i]["instrumentLongName"] == "Cash and Sweep Funds":
                symbol = symbols.positions[i]["instrumentLongName"]
                value = symbols.positions[i]["marketValue"]["baseValueAmount"]
                print(f"Symbol: {symbol} Value: {value}")
            elif symbols.positions[i]["assetCategoryName"] == "EQUITY":
                try:
                    symbol = symbols.positions[i]["positionComponents"][0][
                        "securityIdDetail"
                    ][0]["symbolSecurityIdentifier"]
                    value = symbols.positions[i]["marketValue"]["baseValueAmount"]
                    quantity = symbols.positions[i]["tradedUnitQuantity"]
                    print(f"Symbol: {symbol} Value: {value} Quantity: {quantity}")
                except KeyError:
                    symbol = symbols.positions[i]["securityIdDetail"]["cusipIdentifier"]
                    value = symbols.positions[i]["marketValue"]["baseValueAmount"]
                    quantity = symbols.positions[i]["tradedUnitQuantity"]
                    print(f"Symbol: {symbol} Value: {value} Quantity: {quantity}")
    else:
        print(f"Failed to get holdings for account {account}")
print("====================================")

# Create Order Object
order = och.Order(cs)

# Get Order Statuses
print("====================================")
print("ORDER STATUSES")
for account in account_ids:
    order_statuses = order.get_order_statuses(account)
    print("====================================")
    print(f"Account: {account}")
    for order_status in order_statuses["orderSummaries"]:
        order_number = order_status["orderIdentifier"]
        order_type = order_status["tradeActionCode"]
        order_status_code = order_status["orderStatusCode"]
        print(
            f"Order Number: {order_number} Side: {order_type} Status: {order_status_code}"
        )
print("====================================")

# Get quote for INTC
symbol_quote = sym.SymbolQuote(account_ids[0], cs, "INTC")
print("====================================")
print("SYMBOL QUOTE")
print(
    f"{symbol_quote.security_description} ask price {symbol_quote.ask_price}, @{symbol_quote.as_of_time} and the last trade was {symbol_quote.last_trade_price}."
)
print("====================================")

# Place dry run order for INTC
messages = order.place_order(
    account_ids[0],
    1,
    ord.PriceType.MARKET,
    "INTC",
    ord.Duration.DAY,
    ord.OrderType.BUY,
    dry_run=True,
)
if messages["ORDER CONFIRMATION"] != "":
    print(messages["ORDER CONFIRMATION"])
else:
    print(messages)
