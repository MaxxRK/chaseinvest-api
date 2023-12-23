import os
import traceback
from time import sleep

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from .urls import auth_code_page, login_page


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
        get_driver(): Initializes and returns a WebDriver with the necessary options.
        login(username, password, last_four): Logs into Chase with the provided credentials.
    """

    def __init__(self, persistant_session, headless=True, docker=False):
        """
        Initializes a new instance of the ChaseSession class.

        Args:
            persistent_session (bool): Whether the session should be persistent across multiple uses of the WebDriver.
            headless (bool, optional): Whether the WebDriver should run in headless mode. Defaults to True.
            docker (bool, optional): Whether the session is running in a Docker container. Defaults to False.
        """
        self.persistent_session: bool = persistant_session
        self.headless: bool = headless
        self.docker: bool = docker
        self.profile_path: str = ""
        self.driver = self.get_driver()

    def get_driver(self):
        """
        Gets the correct WebDriver for the operating system and initializes it with the necessary options.

        This method configures a Chromium WebDriver with various options to disable infobars, notifications, and GPU usage,
        and to enable certain experimental options. If the session is persistent, it also sets the user data directory.
        If the session is running in a Docker container, it configures the WebDriver accordingly.

        Returns:
            driver (selenium.webdriver.Chrome): The configured WebDriver instance.

        Raises:
            Exception: If there is an error initializing the WebDriver.
        """
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-notifications")
            if self.headless:
                options.add_argument("--headless")
                options.add_argument("--window-size=1920,1080")
                options.add_argument(
                    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.3"
                )
            if self.persistent_session:
                root = os.path.abspath(os.path.dirname(__file__))
                profile_path = os.path.join(root, "Profile", "Chase")
                options.add_argument("user-data-dir=%s" % profile_path)
            options.add_argument("--disable-gpu")
            options.add_experimental_option("useAutomationExtension", False)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_argument("disable-blink-features=AutomationControlled")
            options.add_argument("--log-level=3")
            if self.docker:
                options.add_argument("--no-sandbox")
                chrome_service = ChromiumService("/usr/bin/chromedriver")
                driver = webdriver.Chrome(service=chrome_service, options=options)
            else:
                driver = webdriver.Chrome(
                    service=ChromiumService(
                        ChromeDriverManager(chrome_type=ChromeType.CHROMIUM).install()
                    ),
                    options=options,
                )
        except Exception as e:
            print(f"Error getting Driver: \n")
            traceback.print_exc(e)
        if not self.headless:
            driver.maximize_window()
        else:
            driver.set_window_size(1920, 1080)
        return driver

    def login(self, username, password, last_four):
        """
        Logs into the website with the provided username and password.

        This method navigates to the login page, enters the provided username and password into the appropriate fields,
        and submits the form. If the login is successful, the WebDriver will be redirected to the user's account page.

        Args:
            username (str): The user's username.
            password (str): The user's password.

        Raises:
            Exception: If there is an error during the login process.
        """
        try:
            self.driver.get(url=login_page())
            WebDriverWait(self.driver, 60).until(
                EC.presence_of_element_located((By.ID, "signin-button"))
            )
            self.driver.find_element(By.ID, "userId-text-input-field").send_keys(
                username
            )
            self.driver.find_element(By.ID, "password-text-input-field").send_keys(
                password
            )
            self.driver.find_element(By.ID, "signin-button").click()
            try:
                WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located(
                        (
                            By.CSS_SELECTOR,
                            "#header-simplerAuth-dropdownoptions-styledselect",
                        )
                    )
                )
                contact_btn = self.driver.find_element(
                    By.CSS_SELECTOR, "#header-simplerAuth-dropdownoptions-styledselect"
                )
                contact_btn.click()
                options_ls = self.driver.find_elements(
                    By.CSS_SELECTOR, 'li[role="presentation"]'
                )
                for item in options_ls:
                    print(item.text)
                    if "CALL_ME" not in item.text:
                        if str(last_four) in item.text:
                            item.click()
                            self.driver.find_element(
                                By.CSS_SELECTOR, 'button[type="submit"]'
                            ).click()

                WebDriverWait(self.driver, 60).until(EC.url_matches(auth_code_page()))
                code = input("Please enter the code sent to your phone: ")
                self.driver.find_element(By.ID, "otpcode_input-input-field").send_keys(
                    code
                )
                self.driver.find_element(By.ID, "password_input-input-field").send_keys(
                    password
                )
                self.driver.find_element(
                    By.CSS_SELECTOR, 'button[type="submit"]'
                ).click()
            except TimeoutException:
                pass
            return True
        except Exception as e:
            traceback.print_exc()
            print(f"Error logging into Chase: {e}")
            return False

    def __getattr__(self, name):
        """
        Forwards unknown attribute access to session object.

        Args:
            name (str): The name of the attribute to be accessed.

        Returns:
            The value of the requested attribute from the session object.
        """
        return getattr(self.session, name)
