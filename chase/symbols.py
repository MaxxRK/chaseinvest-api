from datetime import datetime

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .session import ChaseSession
from .urls import account_holdings, holdings_json, order_page, quote_endpoint


class SymbolQuote:
    """
    A class to manage the quote of a specific symbol associated with a ChaseSession.

    This class provides methods to retrieve and manage information about the quote of a specific symbol associated with a given session.

    Attributes:
        account_id (str): The ID of the account.
        session (ChaseSession): The session associated with the account.
        symbol (str): The symbol for which the quote is retrieved.
        ask_price (float): The ask price of the symbol.
        ask_exchange_code (str): The exchange code of the ask price.
        ask_quantity (int): The quantity of the ask price.
        bid_price (float): The bid price of the symbol.
        bid_exchange_code (str): The exchange code of the bid price.
        bid_quantity (int): The quantity of the bid price.
        change_amount (float): The change amount of the symbol.
        last_trade_price (float): The last trade price of the symbol.
        last_trade_quantity (int): The last trade quantity of the symbol.
        last_exchange_code (str): The exchange code of the last trade.
        change_percentage (float): The change percentage of the symbol.
        as_of_time (datetime): The timestamp of the quote information.
        security_description (str): The description of the security.
        security_symbol (str): The symbol of the security.
        raw_json (dict): The raw JSON response containing the quote information.

    Methods:
        get_symbol_quote(): Retrieves and sets the quote information of the symbol.
    """

    def __init__(self, account_id, session: ChaseSession, symbol: str):
        """
        Initializes a SymbolQuote object with a given account ID, ChaseSession, and symbol.

        Args:
            account_id (str): The ID of the account.
            session (ChaseSession): The session associated with the account.
            symbol (str): The symbol for which the quote is retrieved.
        """
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
        """
        Retrieves and sets the quote information of the symbol.

        This method navigates to the symbol quote page, waits for the quote information to load, and then retrieves the quote information from the page.

        Returns:
            None
        """
        with self.session.page.expect_request(quote_endpoint(self.symbol)) as first:
            self.session.page.goto(order_page(self.account_id))
            self.session.page.wait_for_selector("css=label >> text=Buy")
            self.session.page.wait_for_selector(
                "#equitySymbolLookup-block-autocomplete-validate-input-field"
            )
            self.session.page.fill(
                "#equitySymbolLookup-block-autocomplete-validate-input-field",
                self.symbol,
            )
            self.session.page.press(
                "#equitySymbolLookup-block-autocomplete-validate-input-field", "Enter"
            )
            first_request = first.value
            body = first_request.response().json()
        self.raw_json = body
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
    """
    A class to manage the holdings of a specific account associated with a ChaseSession.

    This class provides methods to retrieve and manage information about the holdings of a specific account associated with a given session.

    Attributes:
        account_id (str): The ID of the account.
        session (ChaseSession): The session associated with the account.
        as_of_time (datetime): The timestamp of the holdings information.
        asset_allocation_tool_eligible_indicator (bool): Whether the account is eligible for the asset allocation tool.
        cash_sweep_position_summary (dict): The summary of the cash sweep position.
        custom_position_allowed_indicator (bool): Whether custom positions are allowed.
        error_responses (list): Any error responses returned when retrieving the holdings information.
        performance_allowed_indicator (bool): Whether performance tracking is allowed.
        positions (list): The positions held in the account.
        positions_summary (dict): The summary of the positions.
        raw_json (dict): The raw JSON response containing the holdings information.

    Methods:
        get_holdings(): Retrieves and sets the holdings information of the account.
    """

    def __init__(self, account_id, session: ChaseSession):
        """
        Initializes a SymbolHoldings object with a given account ID and ChaseSession.

        Args:
            account_id (str): The ID of the account.
            session (ChaseSession): The session associated with the account.
        """
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
        """
        Retrieves and sets the holdings information of the account.

        This method navigates to the account holdings page, waits for the holdings information to load, and then retrieves the holdings information from the page.

        Returns:
            bool: True if the holdings information was successfully retrieved, False otherwise.
        """
        try:
            with self.session.page.expect_request(holdings_json()) as first:
                self.session.page.goto(account_holdings(self.account_id))
                first_request = first.value
                body = first_request.response().json()
            self.raw_json = body
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
            return True
        except PlaywrightTimeoutError:
            return False
