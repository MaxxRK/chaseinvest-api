import gzip
import json
from enum import Enum

from .session import ChaseSession
from .urls import account_info, landing_page


class AllAccount:
    def __init__(self, session: ChaseSession):
        self.session = session
        self.requestid = None
        self.all_account_info = self.get_all_account_info()
        self.account_connectors = self.get_account_connectors()

    def get_all_account_info(self):
        self.session.driver.get(landing_page())
        for request in self.session.driver.requests:
            if request.response:
                if request.url in account_info():
                    body = request.response.body
                    body = gzip.decompress(body).decode("utf-8")
                    account_json = json.loads(body)
                    for info in account_json["cache"]:
                        if (
                            info["url"]
                            == "/svc/rr/accounts/secure/v1/account/detail/inv/list"
                        ):
                            invest_json = info["response"]["chaseInvestments"]
                    if request.response.status_code == 200:
                        self.total_value = invest_json["investmentSummary"][
                            "accountValue"
                        ]
                        self.total_value_change = invest_json["investmentSummary"][
                            "accountValueChange"
                        ]
                        return invest_json
                    else:
                        return None

    def get_account_connectors(self):
        account_dict = {}
        for item in self.all_account_info["accounts"]:
            account_dict[item["accountId"]] = [item["mask"]]
        return account_dict


class AccountDetails:
    def __init__(self, account_id, all_account: AllAccount):
        self.all_account_info = all_account.all_account_info
        self.account_id: str = account_id
        self.nickname: str = None
        self.mask: str = None
        self.detail_type: str = None
        self.account_value: float = None
        self.account_value_change: float = None
        self.eda: str = None
        self.ira: bool = None
        self.view_balance: bool = None
        self.prior_year_ira: bool = None
        self.show_xfer: bool = None
        self.get_account_details()

    def get_account_details(self):
        for item in self.all_account_info["accounts"]:
            if item["accountId"] == self.account_id:
                self.mask = item["mask"]
                self.nickname = item["nickname"]
                self.detail_type = item["detailType"]
                self.account_value = float(item["accountValue"])
                self.account_value_change = float(item["accountValueChange"])
                self.eda = bool(item["eda"])
                self.ira = bool(item["ira"])
                self.view_balance = bool(item["viewBalance"])
                self.prior_year_ira = bool(item["priorYearIra"])
                self.show_xfer = bool(item["showXfer"])
