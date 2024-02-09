import os
import traceback
import json
from time import sleep

from playwright.sync_api import sync_playwright, TimeoutError
from playwright_stealth import stealth_sync

from .urls import login_page


class ChaseSession:
    """
    A class to manage a session with Chase.

    This class provides methods to initialize a WebDriver with the necessary options, log into Chase, and perform other actions on the Chase website.

    Attributes:
        persistent_session (bool): Whether the session should be persistent across multiple uses of the WebDriver.
        headless (bool): Whether the WebDriver should run in headless mode.
        docker (bool): Whether the session is running in a Docker container.
        profile_path (str): The path to the user profile directory for the WebDriver.
        driver (selenium.webdriver.Chrome): The WebDriver instance used to interact with the Chase website.

    Methods:
        get_browser(): Initializes and returns a WebDriver with the necessary options.
        login(username, password, last_four): Logs into Chase with the provided credentials.
        login_two(code): Logs into Chase with the provided two-factor authentication code.
        save_storage_state(): Saves the storage state of the browser to a file.
        close_browser(): Closes the browser.
    """

    def __init__(self, title=None, persistant_session=True, headless=True, profile_path=None):
        """
        Initializes a new instance of the ChaseSession class.

        Args:
            title (string): Denotes the name of the profile and if populated will make the session persistent.
            headless (bool, optional): Whether the WebDriver should run in headless mode. Defaults to True.
            docker (bool, optional): Whether the session is running in a Docker container. Defaults to False.
            profile_path (str, optional): The path to the user profile directory for the WebDriver. Defaults to None.
        """
        self.title: str = title
        self.persistant_session: bool = persistant_session
        self.headless: bool = headless
        self.profile_path: str = profile_path
        self.password: str = ""
        self.page = None
        self.playwright = sync_playwright().start()
        self.get_browser()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            print("An error occurred in the context manager:")
            traceback.print_exception(exc_type, exc_value, traceback)
        self.close_browser()
    
    def get_browser(self):
        if self.title is not None and self.profile_path is None:
            root = os.path.abspath(os.path.dirname(__file__))
            self.profile_path = os.path.join(root, "Profile", f"Chase_{self.title}.json")
        elif self.title is None and self.profile_path is None:
            root = os.path.abspath(os.path.dirname(__file__))
            self.profile_path = os.path.join(root, "Profile", "Chase.json")
        if not os.path.exists(self.profile_path):
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            with open(self.profile_path, 'w') as f:
                json.dump({}, f)
        if self.headless:
            self.browser = self.playwright.chromium.launch(headless=True)
        else:
            self.browser = self.playwright.chromium.launch(headless=False)
        context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.3",
            viewport={"width": 1920, "height": 1080},
            storage_state=self.profile_path if self.persistant_session else None,
        )
        self.page = context.new_page()
        stealth_sync(self.page)
    
    def save_storage_state(self):
        """
        Saves the storage state of the browser to a file.

        This method saves the storage state of the browser to a file so that it can be restored later.

        Args:
            filename (str): The name of the file to save the storage state to.
        """
        storage_state = self.page.context.storage_state()
        with open(self.profile_path, 'w') as f:
            json.dump(storage_state, f)
                    
    def close_browser(self):
        """Closes the browser."""
        self.save_storage_state()
        self.browser.close()
        self.playwright.stop()
           
    def login(self, username, password, last_four):
        """
        Logs into the website with the provided username and password.

        This method navigates to the login page, enters the provided username and password into the appropriate fields,
        and submits the form. If the login is successful, the WebDriver will be redirected to the user's account page.

        Args:
            username (str): The user's username.
            password (str): The user's password.
            last_four (int): The last four digits of the user's phone number.

        Raises:
            Exception: If there is an error during the login process in step one.
        """
        try:
            self.password = password
            self.page.goto(login_page())
            self.page.wait_for_load_state('load', timeout=30000)
            self.page.wait_for_selector("#signin-button", timeout=30000)
            self.page.fill("#userId-text-input-field", username)
            self.page.fill("#password-text-input-field", password)
            self.page.click('#signin-button')
            try:
                self.page.wait_for_selector("#header-simplerAuth-dropdownoptions-styledselect", timeout=10000)
                dropdown = self.page.query_selector("#header-simplerAuth-dropdownoptions-styledselect")
                dropdown.click()
                options_ls = self.page.query_selector_all('li[role="presentation"]')
                for item in options_ls:                 
                    item_text = self.page.evaluate('(element) => element.textContent', item)
                    if "CALL_ME" not in item_text and str(last_four) in item_text:
                        sleep(2)
                        dropdown.click()
                        item.click()
                        break
                self.page.click('button[type="submit"]')
                self.page.wait_for_load_state('load', timeout=30000)
                return True
            except TimeoutError:
                if self.persistant_session:
                    self.save_storage_state()
                return False
        except Exception as e:
            traceback.print_exc()
            raise Exception(f"Error in first step of login into Chase: {e}")
   
    def login_two(self, code):
        """
        Logs in a user with the provided username and password.

        Args:
            code (str): 2fa code sent to users phone.

        Raises:
            Exception: Failed to login to chase.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        
        try:
            self.page.fill("#otpcode_input-input-field", code)
            self.page.fill("#password_input-input-field", self.password)
            self.page.click('button[type="submit"]')
            sleep(5)
            for _ in range(3):
                    try:
                        self.page.wait_for_selector("#signin-button", timeout=30000)
                        self.page.reload()
                        sleep(5)
                    except TimeoutError:
                        if self.persistant_session:
                            self.save_storage_state()
                        return True
            raise Exception("Failed to login to Chase")
        except Exception as e:
            traceback.print_exc()
            print(f"Error logging into Chase: {e}")
            return False
