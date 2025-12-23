import asyncio
import datetime
import json

from curl_cffi import requests

from .session import ChaseSession
from .urls import account_holdings, get_headers, holdings_json, order_page, quote_url


class SymbolQuote:
    """A class to manage the quote of a specific symbol associated with a ChaseSession.

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
        local_tz (ZoneInfo): The local timezone information.
        as_of_time (datetime): The timestamp of the quote information.
        security_description (str): The description of the security.
        security_symbol (str): The symbol of the security.
        raw_json (dict): The raw JSON response containing the quote information.

    Methods:
        get_symbol_quote(): Retrieves and sets the quote information of the symbol.

    """

    def __init__(self, account_id: str, session: ChaseSession, symbol: str) -> None:
        """Initialize a SymbolQuote object with a given account ID, ChaseSession, and symbol.

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
        self.last_trade_price_amount: float = 0
        self.last_trade_quantity: float = 0
        self.last_trade_exchange_code: str = ""
        self.change_percent: float = 0
        self.as_of_timestamp: datetime.datetime | None = None
        self.security_description_text: str = ""
        self.security_symbol_code: str = ""
        self.dollar_based_trading_eligible_indicator: bool = False
        self.security_status_code: str = ""
        self.local_tz: datetime.datetime = datetime.datetime.now().astimezone().tzinfo
        self.session.loop.run_until_complete(self.get_symbol_quote())

    async def get_symbol_quote(self) -> None:
        """Retrieve and set the quote information of the symbol.

        This method navigates to the symbol quote page, waits for the quote information to load, and then retrieves the quote information from the page.
        """
        await self.session.page.get(order_page())
        # Chase is no longer giving the option to switch from the new trading experience to the classic one.
        # This will have to be switched to use the new experience soon.      - 9/14/2025 MAXXRK

        cookies = await self.session.browser.cookies.get_all()
        cookies_dict = {c.name: c.value for c in cookies}

        headers = get_headers()
        url = f"{quote_url()}?security-symbol-code={self.symbol}&security-validate-indicator=true&dollar-based-trading-include-indicator=true"

        try:
            response = requests.get(url, headers=headers, cookies=cookies_dict, impersonate="chrome")
            quote_data = response.json()
        except Exception as e:
            print(f"Quote error: {e}")

        self.ask_price = float(quote_data["askPriceAmount"])
        self.ask_exchange_code = quote_data["askExchangeCode"]
        self.ask_quantity = int(quote_data["askQuantity"])
        self.bid_price = float(quote_data["bidPriceAmount"])
        self.bid_exchange_code = quote_data["bidExchangeCode"]
        self.bid_quantity = int(quote_data["bidQuantity"])
        self.change_amount = float(quote_data["changeAmount"])
        self.last_trade_price_amount = float(quote_data["lastTradePriceAmount"])
        self.last_trade_quantity = float(quote_data["lastTradeQuantity"])
        self.last_trade_exchange_code = quote_data["lastTradeExchangeCode"]
        self.change_percent = float(quote_data["changePercent"])
        self.as_of_timestamp = datetime.datetime.strptime(
            quote_data["asOfTimestamp"], "%Y-%m-%dT%H:%M:%S.%fZ",
        ).replace(tzinfo=self.local_tz)
        self.security_description_text = quote_data["securityDescriptionText"]
        self.security_symbol_code = quote_data["securitySymbolCode"]
        self.dollar_based_trading_eligible_indicator = bool(
            quote_data["dollarBasedTradingEligibleIndicator"],
        )
        self.security_status_code = quote_data["securityStatusCode"]


class SymbolHoldings:
    """A class to manage the holdings of a specific account associated with a ChaseSession.

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

    def __init__(self, account_id: str, session: ChaseSession) -> None:
        """Initialize a SymbolHoldings object with a given account ID and ChaseSession.

        Args:
            account_id (str): The ID of the account.
            session (ChaseSession): The session associated with the account.

        """
        self.account_id = account_id
        self.session = session
        self.as_of_time: datetime.datetime | None = None
        self.local_tz: datetime.datetime = datetime.datetime.now().astimezone().tzinfo
        self.asset_allocation_tool_eligible_indicator: bool = False
        self.custom_position_allowed_indicator: bool = False
        self.error_responses: list = []
        self.performance_allowed_indicator: bool = False
        self.positions: list = []
        self.positions_summary: dict = {}
        self.raw_json: dict = {}

    def get_holdings(self) -> bool:
        """Retrieve and set the holdings information of the account.

        This method navigates to the account holdings page, waits for the holdings information to load, and then retrieves the holdings information from the page.

        Returns:
            bool: True if the holdings information was successfully retrieved, False otherwise.

        """
        return self.session.loop.run_until_complete(self._get_holdings_async())

    async def _get_holdings_async(self) -> bool:
        """Async implementation of get_holdings.

        Returns:
            bool: True if the holdings information was successfully retrieved, False otherwise.

        """
        try:
            await self.session.page.get(account_holdings(self.account_id))
            await self.session.page.sleep(2)
            url = holdings_json()

            async with self.session.page.expect_response(url) as response_info:
                await self.session.page.reload()

                # Wait for the response (with built-in timeout handling)
                await asyncio.wait_for(response_info.value, timeout=10)

                # Get response body directly
                body_str, _ = await response_info.response_body
                body = json.loads(body_str)

            self.raw_json = body
            self.as_of_time = datetime.datetime.strptime(
                self.raw_json["asOfTimestamp"], "%Y-%m-%dT%H:%M:%S.%fZ",
            ).replace(tzinfo=self.local_tz)
            self.asset_allocation_tool_eligible_indicator = bool(
                self.raw_json["assetAllocationToolEligibleIndicator"],
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
        except Exception as e:
            print(f"Error getting holdings: {e}")
            return False
