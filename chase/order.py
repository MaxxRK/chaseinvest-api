import time
from enum import Enum

from bs4 import BeautifulSoup
from selenium.common.exceptions import (ElementNotInteractableException,
                                        NoSuchElementException,
                                        TimeoutException)
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

import chase.urls as urls

from .session import ChaseSession
from .symbols import SymbolQuote


class PriceType(str, Enum):
    """
    This is an :class: 'enum.Enum' that contains the valid price types for an order.
    """

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


class OrderType(str, Enum):
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
        # self.session.driver.request_interceptor = self.post_interceptor
        self.accept_warning = accept_warning
        self.order_number: str = ""
        self.wait_time: int = 30

    def set_wait_time(self, wait_time: int):
        self.wait_time = wait_time

    def place_order(
        self,
        account_id,
        quantity,
        price_type: PriceType,
        symbol,
        duration: Duration,
        order_type: OrderType,
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
            account (str): Account number of the account to place the order in.
            symbol (str): Ticker to place the order for.
            order_type (PriceType): Price Type i.e. LIMIT, MARKET, STOP, etc.
            quantity (float): The number of shares to buy.
            duration (Duration): Duration of the order i.e. DAY, GT90, etc.
            price (float, optional): The price to buy the shares at. Defaults to 0.00.
            dry_run (bool, optional): Whether you want the order to be placed or not.
                                      Defaults to True.

        Returns:
            Order:order_confirmation: Dictionary containing the order confirmation data.
        """

        order_messages = {'ORDER INVALID': '', 'WARNING': '', 'ORDER PREVIEW': '', 'AFTER HOURS WARNING': '', 'ORDER CONFIRMATION': ''}

        for i in range(0, 10):
            self.session.driver.get(urls.order_page(account_id))
            self.session.driver.refresh()
            try:
                WebDriverWait(self.session.driver, self.wait_time).until(EC.presence_of_element_located((By.XPATH, "//label[text()='Buy']")))
                break
            except (TimeoutException, NoSuchElementException):
                order_messages['ORDER INVALID'] = f"Order page did not load correctly cannot continue. Tried {i + 1} times."
                print(order_messages["ORDER INVALID"])

        if order_messages['ORDER INVALID'] != '':
            return order_messages

        quote_box = self.session.driver.find_element(By.CSS_SELECTOR, "#equitySymbolLookup-block-autocomplete-validate-input-field")
        quote_box.clear()
        quote_box.send_keys(symbol)
        quote_box.send_keys(Keys.ENTER)
        WebDriverWait(self.session.driver, self.wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".NOTE")))
        WebDriverWait(self.session.driver, self.wait_time).until(EC.invisibility_of_element((By.ID, "default-spinner_2")))
        if order_type == "BUY":
            WebDriverWait(self.session.driver, self.wait_time).until(EC.element_to_be_clickable((By.XPATH, "//label[text()='Buy']"))).click()
        elif order_type == "SELL":
            self.session.driver.find_element(By.XPATH, "//label[text()='Sell']").click()
        elif order_type == "SELL_ALL":
            self.session.driver.find_element(By.XPATH, "//label[text()='Sell All']").click()

        if price_type == "LIMIT":
            self.session.driver.find_element(By.XPATH, "//label[text()='Limit']").click()
        elif price_type == "MARKET":
            self.session.driver.find_element(By.XPATH, "//label[text()='Market']").click()
        elif price_type == "STOP":
            self.session.driver.find_element(By.XPATH, "//label[text()='Stop']").click()
        elif price_type == "STOP_LIMIT":
            self.session.driver.find_element(By.XPATH, "//label[text()='Stop Limit']").click()

        if price_type in ["LIMIT", "STOP", "STOP_LIMIT"]:
            WebDriverWait(self.session.driver,self.wait_time).until(EC.presence_of_element_located((By.NAME, "tradeLimitPrice"))).send_keys(limit_price)
        if price_type in ["STOP", "STOP_LIMIT"]:
            WebDriverWait(self.session.driver,self.wait_time).until(EC.presence_of_element_located((By.NAME, "tradeStopPrice"))).send_keys(stop_price)

        quantity_box = self.session.driver.find_element(By.NAME, "tradeQuantity")
        quantity_box.clear()
        quantity_box.send_keys(quantity)
        self.session.driver.find_element(By.XPATH, "//label[text()='Day']").click()

        try:
            WebDriverWait(self.session.driver, self.wait_time).until(EC.element_to_be_clickable((By.CSS_SELECTOR , "#previewOrder"))).click()
        except NoSuchElementException:
            raise Exception("No preview button found. Cannot continue.")
        except ElementNotInteractableException:
            raise Exception("Preview button not interactable. Cannot continue.")

        try:
            warning = WebDriverWait(self.session.driver, self.wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#entry-trade-wrapper > div > div:nth-child(1) > div > div"))).text
            order_messages["ORDER INVALID"] = warning
            return(order_messages)
        except (NoSuchElementException, TimeoutException):
            order_messages["ORDER INVALID"] = "No invalid order message found."

        try:
            WebDriverWait(self.session.driver, self.wait_time).until(EC.url_to_be(urls.warning_page(account_id)))
            warning = self.session.driver.find_element(By.CSS_SELECTOR, ".singleWarning").text
            order_messages["WARNING"] =  warning
            if self.accept_warning:
                try:
                    WebDriverWait(self.session.driver, self.wait_time).until(EC.presence_of_element_located((By.CSS_SELECTOR, "#acceptWarnings"))).click()
                except (NoSuchElementException, TimeoutException):
                    raise Exception("No accept button found. Could not dismiss prompt.")
            else:
                return(order_messages)
        except TimeoutException:
            order_messages["WARNING"] = "No warning page found."

        try:
            WebDriverWait(self.session.driver, self.wait_time).until(EC.url_to_be(urls.order_preview_page(account_id)))
            order_preview = self.session.driver.find_element(By.CLASS_NAME, "trade-wrapper").text
            order_messages["ORDER PREVIEW"] = order_preview
            if not dry_run:
                try:
                    self.session.driver.find_element(By.CSS_SELECTOR, "#submitOrder").click()
                except NoSuchElementException:
                    raise Exception("No place order button found cannot continue.")
            else:
                return(order_messages)
        except TimeoutException:
            order_messages["ORDER PREVIEW"] = "No order preview page found."
        
        try:
            WebDriverWait(self.session.driver, self.wait_time).until(EC.url_to_be(urls.after_hours_warning(account_id)))
            warning = self.session.driver.find_element(By.CSS_SELECTOR, "#afterHoursModal > div.markets-message > div").text
            order_messages["AFTER HOURS WARNING"] = warning
            if after_hours:
                try:
                    self.session.driver.find_element(By.CSS_SELECTOR, "#confirmAfterHoursOrder").click()
                except NoSuchElementException:
                    raise Exception("No yes button found. Could not dismiss prompt.")
            else:
                return(order_messages)
        except TimeoutException:
            order_messages["AFTER HOURS WARNING"] = "No after hours warning page found."
        
        try:
            WebDriverWait(self.session.driver, self.wait_time).until(EC.url_to_be(urls.order_confirmation()))
            order_confirmation = self.session.driver.find_element(By.ID, "confirmationHeader").text
            order_confirmation = order_confirmation + " " + self.session.driver.find_element(By.ID, "confirmationAlert").text
            order_confirmation = order_confirmation + " " + self.session.driver.find_element(By.CLASS_NAME, "trade-wrapper").text
            order_confirmation = order_confirmation.replace("\n", " ")
            order_messages["ORDER CONFIRMATION"] = order_confirmation
            return(order_messages)
        except TimeoutException:
            order_messages["ORDER CONFIRMATION"] = "No order confirmation page found. Order Failed."
            return(order_messages)
