import os
import traceback
from time import sleep

from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from .urls import auth_code_page, login_page


class FileChange(FileSystemEventHandler):
    def __init__(self, filename):
        self.filename = filename

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith(self.filename):
            self.file_modified = True

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

    def __init__(self, title=None, headless=True, docker=False, external_code=False):
        """
        Initializes a new instance of the ChaseSession class.

        Args:
            title (string): Denotes the name of the profile and if populated will make the session persistent.
            headless (bool, optional): Whether the WebDriver should run in headless mode. Defaults to True.
            docker (bool, optional): Whether the session is running in a Docker container. Defaults to False.
        """
        self.title: str = title
        self.headless: bool = headless
        self.docker: bool = docker
        self.profile_path: str = ""
        self.external_code: bool = external_code
        self.need_code: bool = False
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
            if self.title is not None:
                root = os.path.abspath(os.path.dirname(__file__))
                self.profile_path = os.path.join(root, "Profile", f"Chase_{self.title}")
                options.add_argument("user-data-dir=%s" % self.profile_path)
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
            print("Error getting Driver: \n")
            traceback.print_exc(e)
        if not self.headless:
            driver.maximize_window()
        else:
            driver.set_window_size(1920, 1080)
        return driver

    def get_login_code(self):
        """
        Gets the login code from the user. Either from discord or from the terminal.
        
        Args:
            external_code (bool, optional): Whether the code should be retrieved externally. Defaults to False.
        
        Returns:
            code (str): The login code.
        """
        if not self.external_code:
            code = input("Please enter the code sent to your phone: ")
        else:
            self.need_code = True
            event_handler = FileChange(".code")
            observer = Observer()
            observer.schedule(event_handler, path='.', recursive=False)
            observer.start()

            # Wait for the file to be modified
            for i in range(0, 120):
                sleep(1)
                if event_handler.file_modified:
                    break
                if i == 119:
                    raise Exception("Code not received in time cannot login.")

            observer.stop()
            observer.join()

            with open(".code", "r") as f:
                code = f.read()
        return code
    
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
                    if "CALL_ME" not in item.text and str(last_four) in item.text:
                        item.click()
                        self.driver.find_element(
                            By.CSS_SELECTOR, 'button[type="submit"]'
                        ).click()

                WebDriverWait(self.driver, 60).until(EC.url_matches(auth_code_page()))
                code = self.get_login_code()
                self.driver.find_element(By.ID, "otpcode_input-input-field").send_keys(
                    code
                )
                self.driver.find_element(By.ID, "password_input-input-field").send_keys(
                    password
                )
                self.driver.find_element(
                    By.CSS_SELECTOR, 'button[type="submit"]'
                ).click()
                sleep(5)
            except TimeoutException:
                pass
            for _ in range(3):
                try:
                    self.driver.find_element(By.ID, "signin-button")
                    self.driver.refresh()
                    sleep(5)
                except NoSuchElementException:
                    return True
            raise Exception("Failed to login to Chase")
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
