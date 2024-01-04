""" Stores all the urls for the chase website used in this api. """


def login_page():
    return "https://secure05c.chase.com/web/auth/#/logon/logon/chaseOnline"


def auth_code_page():
    return "https://secure05c.chase.com/web/auth/#/logon/recognizeUser/provideAuthenticationCode"


def landing_page():
    return "https://secure.chase.com/web/auth/dashboard#/dashboard/overview"


def account_info():
    return [
        "https://secure.chase.com/svc/rl/accounts/secure/v1/dashboard/data/list",
        "https://secure09ea.chase.com/svc/rl/accounts/secure/v1/dashboard/data/list",
    ]


def account_holdings(account_id):
    """
    Generates the URL for the account holdings page for a specific account.

    This function takes an account ID as an argument and returns the URL for the
    account holdings page for that account on the Chase website.

    Args:
        account_id (str): The ID of the account for which to generate the URL.

    Returns:
        str: The URL for the account holdings page for the specified account.
    """
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/oi-portfolio/positions/render;ai={account_id}"


def holdings_json():
    return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-investment-positions/v1/positions"


def order_page(account_id):
    """
    Generates the URL for the order page for a specific account.

    This function takes an account ID as an argument and returns the URL for the
    order page for that account on the Chase website.

    Args:
        account_id (str): The ID of the account for which to generate the URL.

    Returns:
        str: The URL for the order page for the specified account.
    """
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/entry;ai={account_id};sym="


def quote_endpoint(ticker):
    """
    Generates the URL for the quote endpoint for a specific ticker.

    This function takes a ticker symbol as an argument and returns the URL for the
    quote endpoint for that ticker on the Chase website.

    Args:
        ticker (str): The ticker symbol for which to generate the URL.

    Returns:
        str: The URL for the quote endpoint for the specified ticker.
    """
    return f"https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-equity-quote/v1/quotes?securitySymbolCode={ticker}&securityValidateIndicator=true"


def order_preview_page(account_id):
    """
    Generates the URL for the order preview page for a specific account.

    This function takes an account ID as an argument and returns the URL for the
    order preview page for that account on the Chase website.

    Args:
        account_id (str): The ID of the account for which to generate the URL.

    Returns:
        str: The URL for the order preview page for the specified account.
    """
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/preview;ai={account_id}"


def order_analytics():
    return "https://secure.chase.com/events/analytics/public/v1/events/raw/"


def warning_page(account_id):
    """
    Generates the URL for the warning page for a specific account.

    This function takes an account ID as an argument and returns the URL for the
    warning page for that account on the Chase website.

    Args:
        account_id (str): The ID of the account for which to generate the URL.

    Returns:
        str: The URL for the warning page for the specified account.
    """
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/warnings;ai={account_id}"


def after_hours_warning(account_id):
    """
    Generates the URL for the after hours warning page for a specific account.

    This function takes an account ID as an argument and returns the URL for the
    after hours warning page for that account on the Chase website.

    Args:
        account_id (str): The ID of the account for which to generate the URL.

    Returns:
        str: The URL for the after hours warning page for the specified account.
    """
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/afterHours;ai={account_id}"


def order_confirmation():
    return "https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/confirmation"


def order_status(account_id):
    """
    Generates the URL for the order status page for a specific account.

    This function takes an account ID as an argument and returns the URL for the
    order status page for that account on the Chase website.

    Args:
        account_id (str): The ID of the account for which to generate the URL.

    Returns:
        str: The URL for the order status page for the specified account.
    """
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/order/status;ai={account_id};orderStatus=ALL"


def order_info():
    return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-trade-orders/v1/summaries"


def get_headers():
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
        "Content-Length": "20",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    }
    return headers
