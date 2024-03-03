from enum import Enum

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .session import ChaseSession
from .urls import order_info, order_page, order_status


class PriceType(str, Enum):
    """This is an :class: 'enum.Enum' that contains the valid price types for an order."""

    LIMIT = "LIMIT"
    MARKET = "MARKET"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class Duration(str, Enum):
    """This is an :class:'~enum.Enum' that contains the valid durations for an order."""

    DAY = "DAY"
    GTC = "GOOD_TILL_CANCELLED"
    ON_OPEN = "ON_THE_OPEN"
    ON_CLOSE = "ON_THE_CLOSE"
    I_C = "IMMEDIATE_OR_CANCEL"


class OrderSide(str, Enum):
    """
    This is an :class:'~enum.Enum'
    that contains the valid order types for an order.
    """

    BUY = "BUY"
    SELL = "SELL"
    SELL_ALL = "SELL_ALL"


class TypeCode(str, Enum):
    """
    This is an :class:'~enum.Enum'
    that contains the valid order types for an order.
    """

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
        """
        Builds and places an order.
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
        order_messages = {
            "ORDER INVALID": "",
            "WARNING": "",
            "ORDER PREVIEW": "",
            "AFTER HOURS WARNING": "",
            "ORDER CONFIRMATION": "",
        }

        for i in range(0, 4):
            self.session.page.goto(order_page(account_id))
            self.session.page.reload()
            try:
                self.session.page.wait_for_selector(
                    "css=label >> text=Buy", timeout=20000
                )
                quote_box = self.session.page.query_selector(
                    "#equitySymbolLookup-block-autocomplete-validate-input-field"
                )
                quote_box.fill("")
                quote_box.fill(symbol)
                self.session.page.press(
                    "#equitySymbolLookup-block-autocomplete-validate-input-field",
                    "Enter",
                )
                self.session.page.wait_for_selector(".NOTE", timeout=10000)
                self.session.page.wait_for_selector("#element-id", state="hidden")
                order_messages["ORDER INVALID"] = "Order page loaded correctly."
                break
            except PlaywrightTimeoutError:
                order_messages[
                    "ORDER INVALID"
                ] = f"Order page did not load correctly cannot continue. Tried {i + 1} times."
                print(order_messages["ORDER INVALID"])

        if order_messages["ORDER INVALID"] != "Order page loaded correctly.":
            return order_messages

        if order_type == "BUY":
            buy_btn = self.session.page.wait_for_selector("xpath=//label[text()='Buy']")
            buy_btn.click()
        elif order_type == "SELL":
            sell_btn = self.session.page.wait_for_selector(
                "xpath=//label[text()='Sell']"
            )
            sell_btn.click()
        elif order_type == "SELL_ALL":
            sell_all_btn = self.session.page.wait_for_selector(
                "xpath=//label[text()='Sell All']"
            )
            sell_all_btn.click()

        if price_type == "LIMIT":
            limit_btn = self.session.page.wait_for_selector(
                "xpath=//label[text()='Limit']"
            )
            limit_btn.click()
        elif price_type == "MARKET":
            market_btn = self.session.page.wait_for_selector(
                "xpath=//label[text()='Market']"
            )
            market_btn.click()
            if duration not in ["DAY", "ON_THE_CLOSE"]:
                order_messages[
                    "ORDER INVALID"
                ] = "Market orders must be DAY or ON THE CLOSE."
                return order_messages
        elif price_type == "STOP":
            stop_btn = self.session.page.wait_for_selector(
                "xpath=//label[text()='Stop']"
            )
            stop_btn.click()
            if duration not in ["DAY", "GOOD_TILL_CANCELLED"]:
                order_messages[
                    "ORDER INVALID"
                ] = "Stop orders must be DAY or GOOD TILL CANCELLED."
                return order_messages
        elif price_type == "STOP_LIMIT":
            stop_limit_btn = self.session.page.wait_for_selector(
                "xpath=//label[text()='Stop Limit']"
            )
            stop_limit_btn.click()
            if duration not in ["DAY", "GOOD_TILL_CANCELLED"]:
                order_messages[
                    "ORDER INVALID"
                ] = "Stop orders must be DAY or GOOD TILL CANCELLED."
                return order_messages

        if price_type in ["LIMIT", "STOP_LIMIT"]:
            self.session.page.fill(
                "#tradeLimitPrice-text-input-field", str(limit_price)
            )
        if price_type in ["STOP", "STOP_LIMIT"]:
            self.session.page.fill("#tradeStopPrice-text-input-field", str(stop_price))

        quantity_box = self.session.page.wait_for_selector(
            "#tradeQuantity-text-input-field"
        )
        quantity_box.fill("")
        quantity_box.fill(str(quantity))

        if duration == "DAY":
            self.session.page.click("xpath=//label[text()='Day']")
        elif duration == "GOOD_TILL_CANCELLED":
            self.session.page.click("xpath=//label[text()='Good 'til canceled']")
        elif duration == "ON_THE_OPEN":
            self.session.page.click("xpath=//label[text()='On open']")
        elif duration == "ON_THE_CLOSE":
            self.session.page.click("xpath=//label[text()='On close']")
        elif duration == "IMMEDIATE_OR_CANCEL":
            self.session.page.click("#tradeExecutionOptions-iconwrap")
            self.session.page.click("xpath=//label[text()='Immediate or Cancel']")

        try:
            self.session.page.wait_for_selector("#previewOrder", timeout=5000)
            self.session.page.click("#previewOrder")
        except TimeoutError:
            raise Exception(
                "No preview button found or it is not interactable. Cannot continue."
            )

        try:
            warning = self.session.page.wait_for_selector(
                "#entry-trade-wrapper > div > div:nth-child(1) > div > div",
                timeout=5000,
            )
            warning_text = warning.text_content()
            order_messages["ORDER INVALID"] = warning_text
            return order_messages
        except PlaywrightTimeoutError:
            order_messages["ORDER INVALID"] = "No invalid order message found."

        try:
            warning = self.session.page.wait_for_selector(
                "#equityOverlayContent > div > div", timeout=5000
            )
            warning_handle = warning.query_selector("#previewSoftWarning > ul")
            if warning_handle is not None:
                warning_text = warning_handle.text_content()
                order_messages["WARNING"] = warning
                if self.accept_warning:
                    try:
                        accept_btn = warning.wait_for_selector(
                            ".button--primary", timeout=5000
                        )
                        accept_btn.click()
                    except TimeoutError:
                        raise Exception(
                            "No accept button found. Could not dismiss prompt."
                        )
                else:
                    return order_messages
            order_messages["WARNING"] = "No warning page found."
        except PlaywrightTimeoutError:
            order_messages["WARNING"] = "No warning page found."

        try:
            order_preview = self.session.page.wait_for_selector(
                ".trade-wrapper", timeout=5000
            )
            order_preview_text = order_preview.text_content()
            order_messages["ORDER PREVIEW"] = order_preview_text
            if not dry_run:
                try:
                    self.session.page.click("#submitOrder", timeout=10000)
                except PlaywrightTimeoutError:
                    raise Exception("No place order button found cannot continue.")
            else:
                return order_messages
        except PlaywrightTimeoutError:
            order_messages["ORDER PREVIEW"] = "No order preview page found."

        try:
            warning = self.session.page.wait_for_selector(
                "#afterHoursModal > div.markets-message > div", timeout=5000
            )
            warning_text = warning.text_content()
            order_messages["AFTER HOURS WARNING"] = warning
            if after_hours:
                try:
                    self.session.page.click("#confirmAfterHoursOrder", timeout=2000)
                except TimeoutError:
                    raise Exception("No yes button found. Could not dismiss prompt.")
            else:
                return order_messages
        except PlaywrightTimeoutError:
            order_messages["AFTER HOURS WARNING"] = "No after hours warning page found."

        try:
            order_outside_handle = self.session.page.wait_for_selector(
                "#equityConfirmation > div", timeout=5000
            )
            order_handle = order_outside_handle.query_selector(".alert__title-text")
            if order_handle is None:
                order_messages["ORDER CONFIRMATION"] = "Alert Text not found."
                return order_messages
            order_confirmation = order_handle.text_content()
            order_confirmation = order_confirmation.replace("\n", " ")
            order_messages["ORDER CONFIRMATION"] = order_confirmation
            return order_messages
        except PlaywrightTimeoutError:
            order_messages[
                "ORDER CONFIRMATION"
            ] = "No order confirmation page found. Order Failed."
            return order_messages

    def get_order_statuses(self, account_id):
        """
        Retrieves the statuses of all recent orders placed.

        This method navigates to the order status page and scrapes the status of each order.
        It returns a list of dictionaries, where each dictionary represents an order and contains
        the order number and status.

        Returns:
            list[dict]: A list of dictionaries, where each dictionary contains 'order_number' and 'status' keys.

        Raises:
            TimeoutException: If the order status page fails to load within the specified timeout.
            NoSuchElementException: If an expected element on the order status page cannot be found.
        """
        try:
            with self.session.page.expect_request(order_info()) as first:
                self.session.page.goto(order_status(account_id))
                first_request = first.value
                body = first_request.response().json()
            return body
        except PlaywrightTimeoutError:
            return None
