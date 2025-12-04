"""Stores all the urls for the chase website used in this api."""


def login_page() -> str:
    """Return the Chase login page URL.

    Returns:
        str: The URL of the Chase login page.

    """
    return "https://secure05c.chase.com/web/auth/#/logon/logon/chaseOnline"


def auth_code_page() -> str:
    """Return the Chase authentication code page URL.

    Returns:
        str: The URL of the Chase authentication code page.

    """
    return "https://secure05c.chase.com/web/auth/#/logon/recognizeUser/provideAuthenticationCode"


def landing_page() -> str:
    """Return the Chase landing page URL.

    Returns:
        str: The URL of the Chase landing page.

    """
    return "https://secure.chase.com/web/auth/dashboard#/dashboard/overview"


def opt_out_verification_page() -> str:
    """Return the Chase opt-out verification page URL.

    Returns:
        str: The URL of the Chase opt-out verification page.

    """
    return "https://secure05c.chase.com/web/auth/#/logon/recognizeUser/esasiOptout"


def account_info() -> str:
    """Return the Chase account information URL.

    Returns:
        str: The URL of the Chase account information page.

    """
    return "https://secure.chase.com/svc/rl/accounts/secure/v1/dashboard/module/list"
    # The old URL is below, it seems to be deprecated now.
    # https://secure09ea.chase.com/svc/rl/accounts/secure/v1/dashboard/module/list,


def account_holdings(account_id: str) -> str:
    """Return the URL for the account holdings page for a specific account.

    This function takes an account ID as an argument and returns the URL for the
    account holdings page for that account on the Chase website.

    Args:
        account_id (str): The ID of the account for which to generate the URL.

    Returns:
        str: The URL for the account holdings page for the specified account.

    """
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/oi-portfolio/positions/render;ai={account_id}"


def holdings_json() -> str:
    """Return the URL for the holdings JSON endpoint.

    Returns:
        str: The URL to fetch holdings in JSON format.

    """
    return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-investment-positions/v2/positions"


def order_page() -> str:
    """Return the order page URL.

    Return the URL for the order page on the Chase website; this variant does not
    require an account id and returns the generic equity order entry URL.

    Returns:
        str: The URL for the order page.

    """
    return "https://secure.chase.com/web/auth/dashboard#/dashboard/oi-trade/equity/entry"


def quote_url() -> str:
    """Return the URL for the quote endpoint.

    Returns:
        str: The URL to fetch equity quotes.

    """
    return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-equity-quote/v1/quotes"

def execute_order(order_type: str) -> str:
    """Return the URL for the order execution endpoint.

    Args:
        order_type (str): The type of order, either "buy" or "sell".

    Returns:
        str: The URL to execute the specified type of order.

    """
    if order_type.lower() == "buy":
        return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/investor-servicing/digital-equity-trades/v1/buy-orders"
    elif order_type.lower() == "sell":
        return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/investor-servicing/digital-equity-trades/v1/sell-orders"
    else:
        raise ValueError("order_type must be either 'buy' or 'sell'")

def validate_order(order_type: str) -> str:
    """Return the URL for the order validation endpoint.

    Args:
        order_type (str): The type of order, either "buy" or "sell".

    Returns:
        str: The URL to validate the specified type of order.

    """
    if order_type.lower() == "buy":
        return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/investor-servicing/digital-equity-trades/v1/buy-order-validations"
    elif order_type.lower() == "sell":
        return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/investor-servicing/digital-equity-trades/v1/sell-order-validations"
    else:
        raise ValueError("order_type must be either 'buy' or 'sell'")


def order_analytics() -> str:
    """Return the URL for the order analytics raw events endpoint.

    Returns:
        str: The full URL to the public raw analytics events endpoint used by Chase.

    """
    return "https://secure.chase.com/events/analytics/public/v1/events/raw/"


def order_status(account_id: str) -> str:
    """Return the URL for the order status page for a specific account.

    This function takes an account ID as an argument and returns the URL for the
    order status page for that account on the Chase website.

    Args:
        account_id (str): The ID of the account for which to generate the URL.

    Returns:
        str: The URL for the order status page for the specified account.

    """
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/order/status;ai={account_id};orderStatus=ALL"


def order_info() -> str:
    """Return the Chase digital trade orders summaries endpoint URL.

    Returns:
        str: The URL for fetching digital trade order summaries.

    """
    return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-trade-orders/v1/summaries"


def get_headers() -> dict[str, str]:
    """Return the default HTTP headers used for requests to Chase endpoints.

    Returns:
        dict[str, str]: A mapping of header names to header values.

    """
    return {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Content-Length": "20",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }

# API Endpoints
API_ACCOUNT_LIST = "https://secure.chase.com/svc/rl/accounts/secure/v1/dashboard/module/list"
API_POSITIONS = "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-investment-positions/v2/positions"

# Trading Endpoints
API_QUOTE = "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-equity-quote/v1/quotes"
API_VALIDATE_BUY = "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/investor-servicing/digital-equity-trades/v1/buy-order-validations"
API_EXECUTE_BUY = "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/investor-servicing/digital-equity-trades/v1/buy-orders"
API_VALIDATE_SELL = "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/investor-servicing/digital-equity-trades/v1/sell-order-validations"
API_EXECUTE_SELL = "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/investor-servicing/digital-equity-trades/v1/sell-orders"
