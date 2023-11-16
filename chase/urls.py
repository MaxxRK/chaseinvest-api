def login_page():
    return "https://secure05c.chase.com/web/auth/#/logon/logon/chaseOnline"


def auth_page():
    return


def auth_code_page():
    return "https://secure05c.chase.com/web/auth/#/logon/recognizeUser/provideAuthenticationCode"


def landing_page():
    return "https://secure09ea.chase.com/web/auth/dashboard#/dashboard/overview"


def account_info():
    return "https://secure.chase.com/svc/rl/accounts/secure/v1/dashboard/data/list"


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
