import asyncio
import json

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
            urls = account_info()
            invest_json = await self.get_investment_json(urls[0])
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

        Args:
            url (str): The URL to fetch the investment data from.

        Returns:
            dict: The investment account overview data if successful.
            None: If the request fails or data is not found.

        """
        print("Trying to get investment json from network events (zendriver).")
        result = {}
        event = asyncio.Event()

        def on_response(evt):
            # evt['response']['url'] for CDP, evt['url'] for some wrappers
            response_url = evt.get('response', {}).get('url') or evt.get('url')
            if response_url and response_url.startswith(url):
                result['requestId'] = evt.get('requestId')
                event.set()

        # Attach network event listener
        self.session.page.cdp.Network.responseReceived(on_response)
        await self.session.page.reload()  # or navigate as needed
        try:
            await asyncio.wait_for(event.wait(), timeout=10)
        except asyncio.TimeoutError:
            print("Timed out waiting for network response.")
            return None

        if 'requestId' in result:
            body = await self.session.page.cdp.Network.getResponseBody(requestId=result['requestId'])
            try:
                data = json.loads(body['body'])
            except Exception as e:
                print(f"Error parsing response body: {e}")
                return None
            for info in data.get("cache", []):
                if info.get("url") == "/svc/rr/accounts/secure/overview/investment/v1/list":
                    invest_json = info["response"]["investmentAccountOverviews"][0]
                    self.total_value = invest_json["totalValue"]
                    self.total_value_change = invest_json["totalValueChange"]
                    return invest_json
        return None
    '''async def get_investment_json(self, url: str) -> dict | None:
        """Fetch investment data from a given URL.

        This method sends a request to the provided URL and expects a JSON response.
        The response is expected to contain a "cache" key, which is a list of information.
        It iterates over this list and checks if the "url" key of each item matches a specific string.
        If a match is found, it extracts the "chaseInvestments" data from the "response" key.
        If the status of the request is 200, it sets the total_value and total_value_change attributes of the instance
        and returns the "chaseInvestments" data.

        Args:
            url (str): The URL to fetch the investment data from.

        Returns:
            dict: The "chaseInvestments" data if the request is successful and the required data is found.
            None: If the request fails or if the required data is not found in the response.

        """
        try:
            with self.session.page.expect_response(url) as request_excpectation:
                # Reload page and intercept network request
                await self.session.page.reload()
                await self.session.page.sleep(3)
                request = await request_excpectation.value
                body = request.response().json()
                for info in body["cache"]:
                    if (
                        info["url"]
                        == "/svc/rr/accounts/secure/overview/investment/v1/list"
                    ):
                        invest_json = info["response"]["investmentAccountOverviews"][0]
                        if request.response().status == 200:
                            self.total_value = invest_json["totalValue"]
                            self.total_value_change = invest_json["totalValueChange"]
                            return invest_json
                return None
        except Exception as e:
            print(f"Error fetching investment json: {e}")
            return None
'''


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
