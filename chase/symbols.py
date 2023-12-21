import gzip
import json
from datetime import datetime
from time import sleep

from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .account import AccountDetails, AllAccount
from .session import ChaseSession
from .urls import account_holdings, holdings_json, order_page, quote_endpoint


class SymbolQuote:
    def __init__(self, account_id, session: ChaseSession, symbol: str):
        self.account_id = account_id
        self.session = session
        self.symbol = symbol
        self.ask_price: float = 0
        self.ask_exchange_code: str = ""
        self.ask_quantity: int = 0
        self.bid_price: float = 0
        self.bid_exchange_code: str = ""
        self.bid_quantity: int = 0
        self.change_amount: float = 0
        self.last_trade_price: float = 0
        self.last_trade_quantity: int = 0
        self.last_exchange_code: str = ""
        self.change_percentage: float = 0
        self.as_of_time: datetime = None
        self.security_description: str = ""
        self.security_symbol: str = ""
        self.raw_json: dict = {}
        self.get_symbol_quote()

    def get_symbol_quote(self):
        self.session.driver.get(order_page(self.account_id))
        WebDriverWait(self.session.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//label[text()='Buy']"))
        )
        quote_box = self.session.driver.find_element(
            By.CSS_SELECTOR,
            "#equitySymbolLookup-block-autocomplete-validate-input-field",
        )
        quote_box.send_keys(self.symbol)
        quote_box.send_keys(Keys.ENTER)
        WebDriverWait(self.session.driver, 60).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, ".NOTE"))
        )
        for request in self.session.driver.requests:
            if request.response:
                if request.url == quote_endpoint(self.symbol):
                    body = request.response.body
                    body = gzip.decompress(body).decode("utf-8")
                    self.raw_json = json.loads(body)
        self.ask_price = float(self.raw_json["askPriceAmount"])
        self.ask_exchange_code = self.raw_json["askExchangeCode"]
        self.ask_quantity = int(self.raw_json["askQuantity"])
        self.bid_price = float(self.raw_json["bidPriceAmount"])
        self.bid_exchange_code = self.raw_json["bidExchangeCode"]
        self.bid_quantity = int(self.raw_json["bidQuantity"])
        self.change_amount = float(self.raw_json["changeAmount"])
        self.last_trade_price = float(self.raw_json["lastTradePriceAmount"])
        self.last_trade_quantity = int(self.raw_json["lastTradeQuantity"])
        self.last_exchange_code = self.raw_json["lastTradeExchangeCode"]
        self.change_percentage = float(self.raw_json["changePercent"])
        self.as_of_time = datetime.strptime(
            self.raw_json["asOfTimestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.security_description = self.raw_json["securityDescriptionText"]
        self.security_symbol = self.raw_json["securitySymbolCode"]


class SymbolHoldings:
    def __init__(self, account_id, session: ChaseSession):
        self.account_id = account_id
        self.session = session
        self.as_of_time: datetime = None
        self.asset_allocation_tool_eligible_indicator: bool = None
        self.cash_sweep_position_summary: dict = {}
        self.custom_position_allowed_indicator: bool = None
        self.error_responses: list = []
        self.performance_allowed_indicator: bool = None
        self.positions: list = []
        self.positions_summary: dict = {}
        self.raw_json: dict = {}

    def get_holdings(self):
        self.session.driver.get(account_holdings(self.account_id))
        WebDriverWait(self.session.driver, 60).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='positions-tabs']"))
        )
        sleep(5)
        for request in self.session.driver.requests:
            if request.response:
                if request.url == holdings_json():
                    body = request.response.body
                    body = gzip.decompress(body).decode("utf-8")
                    self.raw_json = json.loads(body)
        self.as_of_time = datetime.strptime(
            self.raw_json["asOfTimestamp"], "%Y-%m-%dT%H:%M:%S.%fZ"
        )
        self.asset_allocation_tool_eligible_indicator = bool(
            self.raw_json["assetAllocationToolEligibleIndicator"]
        )
        self.cash_sweep_position_summary = self.raw_json["cashSweepPositionSummary"]
        self.custom_position_allowed_indicator = bool(
            self.raw_json["customPositionAllowedIndicator"]
        )
        self.error_responses = self.raw_json["errorResponses"]
        self.performance_allowed_indicator = bool(
            self.raw_json["performanceAllowedIndicator"]
        )
        self.positions = self.raw_json["positions"]
        self.positions_summary = self.raw_json["positionsSummary"]


class PositionData:
    def __init__(self, positions: SymbolHoldings):
        self.positions = positions.positions
        pass
