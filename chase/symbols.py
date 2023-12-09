import gzip
import json
from time import sleep

from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from chase.account import AccountDetails, AllAccount
from chase.session import ChaseSession
from chase.urls import (account_holdings, holdings_json, order_page,
                        quote_endpoint)


class Symbols:
    
    def __init__(self, account_id, session: ChaseSession):
        self.account_id = account_id
        self.session = session

        
    def get_holdings(self):
        self.session.driver.get(account_holdings(self.account_id))
        WebDriverWait(self.session.driver, 60).until(EC.presence_of_element_located((By.XPATH, "//*[@id='positions-tabs']")))
        for request in self.session.driver.requests:
            if request.response:
                if request.url == holdings_json():
                    body = request.response.body
                    body = gzip.decompress(body).decode('utf-8')
                    account_json = json.loads(body)
                    print(account_json)
    
    def get_symbol_quote(self, symbol):
        self.session.driver.get(order_page(self.account_id))
        WebDriverWait(self.session.driver, 60).until(EC.presence_of_element_located((By.XPATH, "//label[text()='Buy']")))
        quote_box = self.session.driver.find_element(By.CSS_SELECTOR, "#equitySymbolLookup-block-autocomplete-validate-input-field")
        quote_box.send_keys(symbol)
        quote_box.send_keys(Keys.ENTER)
        WebDriverWait(self.session.driver, 60).until(EC.presence_of_element_located((By.CSS_SELECTOR, ".NOTE")))
        for request in self.session.driver.requests:
            if request.response:
                if request.url == quote_endpoint(symbol):
                    body = request.response.body
                    body = gzip.decompress(body).decode('utf-8')
                    quote_json = json.loads(body)
                    print(quote_json)
                    