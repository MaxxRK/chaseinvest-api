def login_page():
    return 'https://secure05c.chase.com/web/auth/#/logon/logon/chaseOnline'

def auth_page():
    return 

def auth_code_page():
    return 'https://secure05c.chase.com/web/auth/#/logon/recognizeUser/provideAuthenticationCode'

def landing_page():
    return 'https://secure09ea.chase.com/web/auth/dashboard#/dashboard/overview'

def account_info():
    return 'https://secure.chase.com/svc/rl/accounts/secure/v1/dashboard/data/list'

def account_holdings(account_id):
    return f'https://secure.chase.com/web/auth/dashboard#/dashboard/oi-portfolio/positions/render;ai={account_id}'

def all_account_holdings():
    return 'https://secure.chase.com/web/auth/dashboard#/dashboard/oi-portfolio/positions/render;ai=group-cwm-investment-'

def order_endpoint(account_id):
    return f'https://secure.chase.com/web/auth/dashboard#/dashboard/trade/equity/entry;ai={account_id};sym='

def quote_endpoint(ticker):
    return f'https://secure.chase.com/svc/wr/dwm/secure/gateway/investments/servicing/inquiry-maintenance/digital-equity-quote/v1/quotes?securitySymbolCode={ticker}&securityValidateIndicator=true'

def get_headers():
    
    headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.5",
    "Connection": "keep-alive",
    "Content-Length": "20",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"
    }
    return headers