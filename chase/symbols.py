import gzip
import json

from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from chase.account import AccountDetails, AllAccount
from chase.urls import account_holdings, quote_endpoint


class Symbols:
    def __init__(self, account_id, session: ChaseSession):
        self.account_id = account_id
        self.session = session
        self.holdings = self.get_holdings()

    def get_holdings(self):
        self.session.driver.get(account_holdings(self.account_id))
        for request in self.session.driver.requests:
            if request.response:
                if request.url == account_holdings():
                    body = request.response.body
                    body = gzip.decompress(body).decode("utf-8")
                    account_json = json.loads(body)
                    print(account_json)

    def get_symbol_quote(self, symbol):
        self.session.driver.get(quote_endpoint(symbol))
        for request in self.session.driver.requests:
            if request.response:
                if request.url == quote_endpoint(symbol):
                    body = request.response.body
                    body = gzip.decompress(body).decode("utf-8")
                    quote_json = json.loads(body)
                    print(quote_json)
