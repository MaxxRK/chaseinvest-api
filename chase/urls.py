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
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/oi-portfolio/positions/render;ai={account_id}"


def holdings_json():
    return "https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-investment-positions/v1/positions"


def order_page(account_id):
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/entry;ai={account_id};sym="


def quote_endpoint(ticker):
    return f"https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-equity-quote/v1/quotes?securitySymbolCode={ticker}&securityValidateIndicator=true"


def order_preview_page(account_id):
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/preview;ai={account_id}"


def order_analytics():
    return "https://secure.chase.com/events/analytics/public/v1/events/raw/"


def warning_page(account_id):
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/warnings;ai={account_id}"


def after_hours_warning(account_id):
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/afterHours;ai={account_id}"


def order_confirmation():
    return f"https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/confirmation"


def order_status(account_id):
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


# 'https://secure09ea.chase.com/web/auth/dashboard#/dashboard/overview',
