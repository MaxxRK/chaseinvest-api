from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

from .session import ChaseSession
from .urls import account_info


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

        This method initializes an AllAccount object, sets the session attribute to the given ChaseSession,
        and retrieves the account information and connectors for all accounts associated with the session.

        Args:
            session (ChaseSession): The session associated with the accounts.
        """
        self.session = session
        self.total_value = None
        self.total_value_change = None
        self.all_account_info = self.get_all_account_info()
        self.account_connectors = self.get_account_connectors()

    def get_all_account_info(self):
        """
        Retrieves and returns information about all accounts associated with the session.

        This method navigates to the landing page, waits for the account information to load,
        and then retrieves the account information from the page.

        Returns:
            dict: A dictionary containing the account information, or None if the information could not be retrieved.
        """
        try:
            urls = account_info()
            invest_json = self.get_investment_json(urls[0])
            if invest_json is None:
                invest_json = self.get_investment_json(urls[1])
        except PlaywrightTimeoutError:
            print("Timed out waiting for page to load")
            invest_json = None

        return invest_json

    def get_account_connectors(self):
        """
        Retrieves and returns connectors for all accounts associated with the session.

        This method iterates over all accounts in the all_account_info attribute and creates a dictionary
        where the keys are account IDs and the values are lists containing the corresponding account masks.

        Returns:
            dict: A dictionary containing the account connectors, or None if the all_account_info attribute is None.
        """
        if self.all_account_info is None:
            return None
        account_dict = {}
        for item in self.all_account_info["accounts"]:
            account_dict[item["accountId"]] = [item["mask"]]
        return account_dict

    def get_investment_json(self, url):
        """
        Fetches investment data from a given URL.

        This method sends a request to the provided URL and expects a JSON response.
        The response is expected to contain a "cache" key, which is a list of information.
        It iterates over this list and checks if the "url" key of each item matches a specific string.
        If a match is found, it extracts the "chaseInvestments" data from the "response" key.
        If the status of the request is 200, it sets the total_value and total_value_change attributes of the instance
        and returns the "chaseInvestments" data.

        The method retries the request up to 3 times in case of a PlaywrightTimeoutError or RuntimeError.

        Args:
            url (str): The URL to fetch the investment data from.

        Returns:
            dict: The "chaseInvestments" data if the request is successful and the required data is found.
            None: If the request fails after 3 attempts or if the required data is not found in the response.
        """
        for i in range(3):
            try:
                with self.session.page.expect_request(url) as request_context:
                    self.session.page.reload()
                    request = request_context.value
                    body = request.response().json()
                    for info in body["cache"]:
                        if (
                            info["url"]
                            == "/svc/rr/accounts/secure/v1/account/detail/inv/list"
                        ):
                            invest_json = info["response"]["chaseInvestments"]
                            if request.response().status == 200:
                                self.total_value = invest_json["investmentSummary"][
                                    "accountValue"
                                ]
                                self.total_value_change = invest_json[
                                    "investmentSummary"
                                ]["accountValueChange"]
                                return invest_json
                    return None
            except (PlaywrightTimeoutError, RuntimeError):
                if i == 2:
                    return None


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
