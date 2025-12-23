import asyncio
import json
from enum import StrEnum

from curl_cffi import requests

from .session import ChaseSession
from .urls import execute_order, get_headers, order_info, order_page, order_status, validate_order


class PriceType(StrEnum):
    """Contains the valid price types for an order."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class Duration(StrEnum):
    """Contains the valid durations for an order."""

    DAY = "DAY"
    GTC = "GOOD_TILL_CANCELLED"
    ON_OPEN = "ON_THE_OPEN"
    ON_CLOSE = "ON_THE_CLOSE"
    I_C = "IMMEDIATE_OR_CANCEL"


class OrderSide(StrEnum):
    """Contains the valid order types for an order."""

    BUY = "BUY"
    SELL = "SELL"
    SELL_ALL = "SELL_ALL"


class TypeCode(StrEnum):
    """Contains the valid order types for an order."""

    CASH = "CASH"
    MARGIN = "MARGIN"


class Order:
    """Contains information about an order and provides methods to place orders.

    Also contains a method to place an order.
    """

    def __init__(self, session: ChaseSession, accept_warning: bool = True) -> None:  # noqa: FBT001
        """Initialize an Order instance.

        Args:
            session (ChaseSession): The Chase session to use for order operations.
            accept_warning (bool, optional): Whether to accept warnings during order placement.
                                           Defaults to True.

        """
        self.session = session
        self.accept_warning = accept_warning
        self.order_number: str = ""

    def place_order(  # noqa: PLR0913, PLR0917
        self,
        account_id: str,
        quantity: int,
        price_type: PriceType,
        symbol: str,
        duration: Duration,
        order_type: OrderSide,
        limit_price: float = 0.00,
        stop_price: float = 0.00,
        after_hours: bool = True,  # noqa: FBT001, FBT002
        dry_run: bool = True,  # noqa: FBT001, FBT002
    ) -> dict:
        """Build and place an order.

        :attr: 'order_confirmation`
        contains the order confirmation data after order placement.

        Args:
            account_id (str): Account number of the account to place the order in.
            quantity (int): The number of shares to buy.
            price_type (PriceType): Price Type i.e. LIMIT, MARKET, STOP, etc.
            symbol (str): Ticker to place the order for.
            duration (Duration): Duration of the order i.e. DAY, GT90, etc.
            order_type (OrderSide): Type of order i.e. BUY, SELL, SELL_ALL.
            limit_price (float, optional): The price to buy the shares at. Defaults to 0.00.
            stop_price (float, optional): The price to buy the shares at. Defaults to 0.00.
            after_hours (bool, optional): Whether you want to place the order after hours. Defaults to True.
            dry_run (bool, optional): Whether you want the order to be placed or not.
                                      Defaults to True.

        Returns:
            Order:order_confirmation: Dictionary containing the order confirmation data.

        """
        return self.session.loop.run_until_complete(
            self._place_order_async(
                account_id,
                quantity,
                price_type,
                symbol,
                duration,
                order_type,
                limit_price=limit_price,
                stop_price=stop_price,
                after_hours=after_hours,
                dry_run=dry_run,
            ),
        )

    async def _place_order_async(  # noqa: PLR0913, PLR0917
        self,
        account_id: str,
        quantity: int,
        price_type: PriceType,
        symbol: str,
        duration: Duration,
        order_type: OrderSide,
        limit_price: float = 0.00,
        stop_price: float = 0.00,
        after_hours: bool = True,  # noqa: FBT001, FBT002
        dry_run: bool = True, # noqa: FBT001, FBT002
    ) -> dict:
        """Async implementation of place_order.

        Returns:
            dict: Dictionary containing order validation/confirmation data with keys
                  "ORDER INVALID", "ORDER VALIDATION", and "ORDER CONFIRMATION".

        """
        await self.session.page.get(order_page())

        order_messages = {
            "ORDER INVALID": "",
            "ORDER VALIDATION": "",
            "ORDER CONFIRMATION": "",
        }

        # Implement API calls instead of browser interactions where possible.
        # Thanks @OSSY!
        headers = get_headers()
        cookies = await self.session.browser.cookies.get_all()
        cookies_dict = {c.name: c.value for c in cookies}

        order_payload = {
           "accountIdentifier": int(account_id),
            # do i need this for market?
            "marketPriceAmount": limit_price,
            "orderQuantity": quantity,
            "accountTypeCode": "CASH",
            "timeInForceCode": duration,
            "securitySymbolCode": symbol,
            "tradeChannelName": "DESKTOP",
            "dollarBasedTradingEligibleIndicator": False,
            "orderTypeCode": price_type,
        }

        url_validate = validate_order(order_type=order_type)
        url_execute = execute_order(order_type=order_type)

        if order_type == "BUY":
            order_payload["tradeActionName"] = "BUY"
        elif order_type == "SELL":
            order_payload["tradeActionName"] = "SELL"
        elif order_type == "SELL_ALL":
            order_payload["tradeActionName"] = "SELL_ALL"

        if price_type == "LIMIT":
            order_payload["limitPriceAmount"] = limit_price
        elif price_type == "MARKET":
            if duration not in {"DAY", "ON_THE_CLOSE"}:
                order_messages["ORDER INVALID"] = (
                    "Market orders must be DAY or ON THE CLOSE."
                )
                return order_messages
        elif price_type == "MARKET ON CLOSE":
            pass
        elif price_type in {"STOP", "STOP_LIMIT"} and duration not in {"DAY", "GOOD_TILL_CANCELLED"}:
            order_messages["ORDER INVALID"] = (
                "Stop orders must be DAY or GOOD TILL CANCELLED."
            )
            return order_messages

        if price_type in {"LIMIT", "STOP_LIMIT"}:
            order_payload["limitPriceAmount"] = limit_price
        if price_type in {"STOP", "STOP_LIMIT"}:
            order_payload["stopPriceAmount"] = stop_price

        if duration == "DAY":
            order_payload["timeInForceCode"] = "DAY"
        elif duration == "GOOD_TILL_CANCELLED":
            order_payload["timeInForceCode"] = "GOOD_TILL_CANCELLED"
        elif duration == "ON_THE_OPEN":
            order_payload["timeInForceCode"] = "ON_THE_OPEN"
        elif duration == "ON_THE_CLOSE":
            order_payload["timeInForceCode"] = "ON_THE_CLOSE"
        elif duration == "IMMEDIATE_OR_CANCEL":
            order_payload["timeInForceCode"] = "IMMEDIATE_OR_CANCEL"

        try:
            # STEP 1: VALIDATION

            resp_val = requests.post(url_validate, headers=headers, cookies=cookies_dict, json=order_payload, impersonate="chrome")

            if resp_val.status_code != 200:
                order_messages["ORDER INVALID"] = f"Validation Failed ({resp_val.status_code}): {resp_val.text}"

            val_data = resp_val.json()

            print(val_data)
            error_msgs = val_data.get("tradeErrorMessages", [])
            order_messages["ORDER INVALID"] = error_msgs

            if order_messages["ORDER INVALID"]:
                return order_messages

            exchange_id = val_data.get("financialInformationExchangeSystemOrderIdentifier")

            if dry_run:
                order_messages["ORDER VALIDATION"] = val_data
                return order_messages
            if not exchange_id:
                order_messages["ORDER VALIDATION"] = val_data
        except Exception as e:
            order_messages["ORDER INVALID"] = f"Execution Exception: {e}"

        try:
            # STEP 2: EXECUTION
            payload_execute = order_payload.copy()
            payload_execute["financialInformationExchangeSystemOrderIdentifier"] = exchange_id

            resp_exec = requests.post(url_execute, headers=headers, cookies=cookies_dict, json=payload_execute, impersonate="chrome")

            if resp_exec.status_code != 200:
                order_messages["ORDER INVALID"] = f"Execution Failed ({resp_exec.status_code}): {resp_exec.text}"
            elif resp_exec.status_code == 200:
                order_messages["ORDER VALIDATION"] = val_data
            exec_data = resp_exec.json()
            # order_id = exec_data.get("orderIdentifier")
            order_messages["ORDER CONFIRMATION"] = exec_data
        except Exception as e:
            order_messages["ORDER INVALID"] = f"Execution Exception: {e}"
        return order_messages

    def get_order_statuses(self, account_id: str) -> str:
        """Retrieve the statuses of all recent orders placed.

        This method navigates to the order status page and scrapes the status of each order.
        It returns a list of dictionaries, where each dictionary represents an order and contains
        the order number and status.

        Returns:
            list[dict] | None: A list of dictionaries, where each dictionary contains 'order_number'
            and 'status' keys on success, or None if an error occurred while retrieving statuses.

        """
        return self.session.loop.run_until_complete(
            self._get_order_statuses_async(account_id),
        )

    async def _get_order_statuses_async(self, account_id: str) -> str:
        """Async implementation of get_order_statuses.

        Returns:
            dict | None: Parsed JSON body containing order statuses on success,
            or None if an error occurred while retrieving statuses.

        """
        try:
            await self.session.page.get(order_status(account_id))
            await self.session.page.sleep(2)

            url = order_info()

            async with self.session.page.expect_response(url) as response_info:
                await self.session.page.reload()

                # Wait for the response (with built-in timeout handling)
                await asyncio.wait_for(response_info.value, timeout=10)

                # Get response body directly
                body_str, _ = await response_info.response_body
            return json.loads(body_str)
        except Exception as e:
            print(f"Error getting order statuses: {e}")
            return None
