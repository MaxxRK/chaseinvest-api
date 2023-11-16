import gzip
import json

from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from chase.session import ChaseSession
from chase.urls import account_info, get_headers, landing_page


class Account:
    def __init__(self, session: ChaseSession):
        self.session = session
        self.requestid = None

    def print_request_id(self, event):
        self.requestid = event["requestId"]
        print("Request ID: ", event["requestId"])

    def get_account_info(self):
        # log = 'performance'
        # self.session.driver.execute_cdp_cmd("Network.enable", {})
        self.session.driver.get(landing_page())
        for request in self.session.driver.requests:
            if request.response:
                if request.url == account_info():
                    body = request.response.body
                    body = gzip.decompress(body).decode("utf-8")
                    print(request.url, request.response.status_code, body)
        # try:
        # log = json.loads(log["message"])["message"]
        # if ("Network.responseReceived" in log["method"] and "params" in log.keys()):
        # body = self.session.driver.execute_cdp_cmd('Network.getResponseBody', {'requestId': log["params"]["requestId"]})
        # except exceptions.WebDriverException:
        # print('response.body is null')
        # request_id = self.session.driver.execute_script("return window.requestId;")
        # print(request_id)
        # response = self.session.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})
        # print(response)
