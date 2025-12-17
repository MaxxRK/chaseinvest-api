import asyncio
import json

from curl_cffi import requests
from enum import StrEnum
from zendriver.core.keys import SpecialKeys

from .session import ChaseSession
from .urls import order_info, order_page, execute_order, validate_order


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
    """
    This class contains information about an order.
    It also contains a method to place an order.
    """

    def __init__(self, session: ChaseSession, accept_warning: bool = True):
        self.session = session
        self.accept_warning = accept_warning
        self.order_number: str = ""

    def place_order(
        self,
        account_id,
        quantity: int,
        price_type: PriceType,
        symbol,
        duration: Duration,
        order_type: OrderSide,
        limit_price: float = 0.00,
        stop_price: float = 0.00,
        after_hours: bool = True,
        dry_run=True,
    ):
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
                limit_price,
                stop_price,
                after_hours,
                dry_run,
            )
        )

    async def _place_order_async(
        self,
        account_id,
        quantity: int,
        price_type: PriceType,
        symbol,
        duration: Duration,
        order_type: OrderSide,
        limit_price: float = 0.00,
        stop_price: float = 0.00,
        after_hours: bool = True,
        dry_run=True,
    ):
        """Async implementation of place_order."""
        await self.session.page.get(order_page())

        order_messages = {
            "ORDER INVALID": "",
            "WARNING": "",
            "ORDER PREVIEW": "",
            "AFTER HOURS WARNING": "",
            "ORDER CONFIRMATION": "",
        }

        # Implement API calls instead of browser interactions where possible.
        # Thanks @OSSY!
        cookies = await self.session.browser.cookies.get_all()
        cookies_dict = {c.name: c.value for c in cookies}
       
        order_payload = {
           "accountIdentifier": int(account_id),
            #"marketPriceAmount": current_price, do i need this for market?
            "orderQuantity": quantity,
            "accountTypeCode": "CASH",
            "timeInForceCode": "DAY",
            "securitySymbolCode": symbol,
            "tradeChannelName": "DESKTOP",
            "dollarBasedTradingEligibleIndicator": False,
            "orderTypeCode": price_type 
        }
        
        url_validate = validate_order(order_type=order_type)
        url_execute = execute_order(order_type=order_type)
        if order_type == "BUY":
            order_payload["tradeActionName"] = "BUY"
        elif order_type =="SELL":
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
        elif price_type in {"STOP", "STOP_LIMIT"}:
            if duration not in {"DAY", "GOOD_TILL_CANCELLED"}:
                order_messages["ORDER INVALID"] = (
                    "Stop orders must be DAY or GOOD TILL CANCELLED."
                )
                return order_messages

        if price_type in ["LIMIT", "STOP_LIMIT"]:
            order_payload["limitPriceAmount"] = limit_price
        if price_type in ["STOP", "STOP_LIMIT"]:
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
            warning = await self.session.page.find(
                "#entry-trade-wrapper > div > div:nth-child(1) > div > div",
                timeout=5,
            )
            warning_text = await warning.text
            order_messages["ORDER INVALID"] = warning_text
            return order_messages
        except Exception:
            order_messages["ORDER INVALID"] = "No invalid order message found."

        try:
            warning = await self.session.page.find(
                "#equityOverlayContent > div > div", timeout=5
            )
            warning_handle = await self.session.page.find("#previewSoftWarning > ul", timeout=2)
            if warning_handle is not None:
                warning_text = await warning_handle.text
                order_messages["WARNING"] = warning_text
                if self.accept_warning:
                    try:
                        accept_btn = await warning.find(".button--primary", timeout=5)
                        await accept_btn.click()
                    except Exception:
                        raise Exception(
                            "No accept button found. Could not dismiss prompt."
                        )
                else:
                    return order_messages
            else:
                order_messages["WARNING"] = "No warning page found."
        except Exception:
            order_messages["WARNING"] = "No warning page found."

        try:
            order_preview = await self.session.page.find(".trade-wrapper", timeout=5)
            order_preview_text = await order_preview.text
            order_messages["ORDER PREVIEW"] = order_preview_text
            if not dry_run:
                try:
                    submit_btn = await self.session.page.find("#submitOrder", timeout=10)
                    await submit_btn.click()
                except Exception:
                    raise Exception("No place order button found cannot continue.")
            else:
                return order_messages
        except Exception:
            order_messages["ORDER PREVIEW"] = "No order preview page found."

        try:
            warning = await self.session.page.find(
                "#afterHoursModal > div.markets-message > div", timeout=5
            )
            warning_text = await warning.text
            order_messages["AFTER HOURS WARNING"] = warning_text
            if after_hours:
                try:
                    confirm_btn = await self.session.page.find("#confirmAfterHoursOrder", timeout=2)
                    await confirm_btn.click()
                except Exception:
                    raise Exception("No yes button found. Could not dismiss prompt.")
            else:
                return order_messages
        except Exception:
            order_messages["AFTER HOURS WARNING"] = "No after hours warning page found."

        try:
            order_outside_handle = await self.session.page.find(
                "#equityConfirmation > div", timeout=5
            )
            order_handle = await self.session.page.find(".alert__title-text", timeout=2)
            if order_handle is None:
                order_messages["ORDER CONFIRMATION"] = "Alert Text not found."
                return order_messages
            order_confirmation = await order_handle.text
            order_confirmation = order_confirmation.replace("\n", " ")
            order_messages["ORDER CONFIRMATION"] = order_confirmation
            return order_messages
        except Exception:
            order_messages["ORDER CONFIRMATION"] = (
                "No order confirmation page found. Order Failed."
            )
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
                body = json.loads(body_str)
            return body
        except Exception as e:
            print(f"Error getting order statuses: {e}")
            return None
