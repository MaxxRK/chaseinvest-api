import gzip
import json

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .session import ChaseSession
from .urls import account_info, landing_page


class AllAccount:
    """
    A class to manage all accounts associated with a ChaseSession.

    This class provides methods to retrieve and manage information about all accounts associated with a given session.

    Attributes:
        session (ChaseSession): The session associated with the accounts.
        all_account_info (dict): Information about all accounts associated with the session.
        account_connectors (dict): Connectors for all accounts associated with the session.
        total_value (float): The total value of all accounts.
        total_value_change (float): The change in total value of all accounts.

    Methods:
        get_all_account_info(): Retrieves information about all accounts associated with the session.
        get_account_connectors(): Retrieves connectors for all accounts associated with the session.
    """

    def __init__(self, session: ChaseSession):
        """
        Initializes an AllAccount object with a given ChaseSession.

        This method initializes an AllAccount object, sets the session attribute to the given ChaseSession, and retrieves the account information and connectors for all accounts associated with the session.

        Args:
            session (ChaseSession): The session associated with the accounts.
        """
        self.session = session
        self.all_account_info = self.get_all_account_info()
        self.account_connectors = self.get_account_connectors()

    def get_all_account_info(self):
        """
        Retrieves and returns information about all accounts associated with the session.

        This method navigates to the landing page, waits for the account information to load, and then retrieves the account information from the page.

        Returns:
            dict: A dictionary containing the account information, or None if the information could not be retrieved.
        """
        try:
            self.session.driver.get(landing_page())
            WebDriverWait(self.session.driver, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "#INV_ACCOUNTS"))
            )
            for request in self.session.driver.requests:
                if request.response and request.url in account_info():
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
                    return None
        except (TimeoutException, NoSuchElementException):
            print("Timed out waiting for page to load")
            return None

    def get_account_connectors(self):
        """
        Retrieves and returns connectors for all accounts associated with the session.

        This method iterates over all accounts in the all_account_info attribute and creates a dictionary where the keys are account IDs and the values are lists containing the corresponding account masks.

        Returns:
            dict: A dictionary containing the account connectors, or None if the all_account_info attribute is None.
        """
        if self.all_account_info is None:
            return None
        account_dict = {}
        for item in self.all_account_info["accounts"]:
            account_dict[item["accountId"]] = [item["mask"]]
        return account_dict


class AccountDetails:
    """
    A class to manage the details of a specific account associated with a ChaseSession.

    This class provides methods to retrieve and manage information about a specific account associated with a given session.

    Attributes:
        all_account_info (dict): Information about all accounts associated with the session.
        account_id (str): The ID of the account.
        nickname (str): The nickname of the account.
        mask (str): The mask of the account.
        detail_type (str): The detail type of the account.
        account_value (float): The value of the account.
        account_value_change (float): The change in value of the account.
        eda (str): The EDA of the account.
        ira (bool): Whether the account is an IRA.
        view_balance (bool): Whether the balance of the account can be viewed.
        prior_year_ira (bool): Whether the account is a prior year IRA.
        show_xfer (bool): Whether the account shows transfers.

    Methods:
        get_account_details(): Retrieves and sets the details of the account.
    """

    def __init__(self, account_id, all_account: AllAccount):
        """
        Initializes an AccountDetails object with a given account ID and AllAccount object.

        Args:
            account_id (str): The ID of the account.
            all_account (AllAccount): The AllAccount object associated with the session.
        """
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
        """
        Retrieves and sets the details of the account.

        This method iterates over all accounts in the all_account_info attribute and sets the attributes of the AccountDetails object to the details of the account with the matching account ID.

        Returns:
            None
        """
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
