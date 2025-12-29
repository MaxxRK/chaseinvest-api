import asyncio
import json
import traceback

from .session import ChaseSession
from .urls import account_info


class AllAccount:
    """A class to manage all accounts associated with a ChaseSession.

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

    def __init__(self, session: ChaseSession) -> None:
        """Initialize the AllAccount object with the given ChaseSession.

        This method initializes an AllAccount object, sets the session attribute to the given ChaseSession,
        and retrieves the account information and connectors for all accounts associated with the session.

        Args:
            session (ChaseSession): The session associated with the accounts.

        """
        self.session = session
        self.total_value = None
        self.total_value_change = None
        self.all_account_info = self.session.loop.run_until_complete(
            self.get_all_account_info(),
        )
        self.account_connectors = self.get_account_connectors()

    async def get_all_account_info(self) -> dict | None:
        """Retrieve and return information about all accounts associated with the session.

        This method navigates to the landing page, waits for the account information to load,
        and then retrieves the account information from the page.

        Returns:
            dict: A dictionary containing the account information, or None if the information could not be retrieved.

        """
        try:
            invest_json = await self.get_investment_json(account_info())
        except Exception as e:
            print(f"Timed out waiting for page to load: {e}")
            invest_json = None

        return invest_json

    def get_account_connectors(self) -> dict | None:
        """Retrieve and return connectors for all accounts associated with the session.

        This method iterates over all accounts in the all_account_info attribute and creates a dictionary
        where the keys are account IDs and the values are lists containing the corresponding account masks.

        Returns:
            dict: A dictionary containing the account connectors, or None if the all_account_info attribute is None.

        """
        account_dict = {}
        if self.all_account_info is None:
            return None
        if type(self.all_account_info) is list:
            for item in self.all_account_info:
                account_dict[item["accountId"]] = [item["mask"]]
        else:
            info = self.all_account_info["investmentAccountDetails"]
            for item in info:
                account_dict[item["accountId"]] = [item["mask"]]

        return account_dict

    async def get_investment_json(self, url: str) -> dict | None:
        """Fetch investment data from a given URL using zendriver.

        Returns:
            dict | None: A dictionary containing the parsed investment JSON on success,
            or None if the request timed out or an error occurred while parsing.

        """
        try:
            async with self.session.page.expect_response(url) as response_info:
                await self.session.page.reload()

                # Wait for the response (with built-in timeout handling)
                await asyncio.wait_for(response_info.value, timeout=10)

                # Get response body directly
                body_str, _ = await response_info.response_body
                data = json.loads(body_str)

                for info in data.get("cache", []):
                    if info.get("url") == "/svc/rr/accounts/secure/overview/investment/v1/list":
                        invest_json = info["response"]["investmentAccountOverviews"][0]
                        self.total_value = invest_json["totalValue"]
                        self.total_value_change = invest_json["totalValueChange"]
                        return invest_json

        except TimeoutError:
            print("Timed out waiting for network response.")
            return None
        except Exception as e:
            print(f"Error parsing response body: {e}")
            traceback.print_exc()
            return None

        return None


class AccountDetails:
    """A class to manage the details of a specific account associated with a ChaseSession.

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

    def __init__(self, account_id: str, all_account: AllAccount) -> None:
        """Initialize an AccountDetails object with a given account ID and AllAccount object.

        Args:
            account_id (str): The ID of the account.
            all_account (AllAccount): The AllAccount object associated with the session.

        """
        self.all_account_info = all_account.all_account_info
        self.account_id: str = account_id
        self.nickname: str = ""
        self.mask: str = ""
        self.detail_type: str = ""
        self.account_value: float = -1
        self.account_value_change: float = -1
        self.eda: str = ""
        self.ira: bool = False
        self.view_balance: bool = False
        self.prior_year_ira: bool = False
        self.show_xfer: bool = False
        self.get_account_details()

    def get_account_details(self) -> None:
        """Retrieve and set the details of the account.

        This method iterates over all accounts in the all_account_info attribute and sets the attributes of the AccountDetails object to the details of the account with the matching account ID.

        """
        info = self.all_account_info if type(self.all_account_info) is list else self.all_account_info["investmentAccountDetails"]
        for item in info:
            if item.get("accountId") is None:
                item = item[0]
            if item["accountId"] == self.account_id:
                self.mask = item.get("mask", "")
                self.nickname = item.get("nickname", "")
                self.detail_type = item.get("detailType", "")
                self.account_value = float(item.get("accountValue", -1))
                self.account_value_change = float(item.get("accountValueChange", -1))
                self.eda = bool(item.get("eda", False))
                self.ira = bool(item.get("ira", False))
                self.view_balance = bool(item.get("viewBalance", False))
                self.prior_year_ira = bool(item.get("priorYearIra", False))
                self.show_xfer = bool(item.get("showXfer", False))
