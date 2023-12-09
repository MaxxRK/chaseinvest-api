import os
import traceback
from time import sleep

from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    NoSuchWindowException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)
from selenium.webdriver.chrome.service import Service as ChromiumService
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from seleniumwire import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.os_manager import ChromeType

from chase.urls import auth_code_page, landing_page, login_page


class ChaseSession:
    def __init__(self, persistant_session, docker=False):
        self.persistant_session = persistant_session
        self.profile_path = ""
        self.docker = docker
        self.driver = self.get_driver()

    def get_driver(self):
        """Gets the correct driver for os and returns the driver."""
        try:
            options = webdriver.ChromeOptions()
            options.add_argument("--disable-infobars")
            options.add_argument("--disable-notifications")
            if self.persistant_session:
                root = os.path.abspath(os.path.dirname(__file__))
                profile_path = os.path.join(root, "Profile/Chase")
                options.add_argument("user-data-dir=%s" % profile_path)
            options.add_argument("--disable-gpu")
            options.add_experimental_option("useAutomationExtension", False)
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_argument("disable-blink-features=AutomationControlled")
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
            traceback.print_exc()
            print(f"Error getting Driver: {e}")
        driver.maximize_window()
        return driver

    def login(self, username, password, last_four):
        """Logs into Chase."""
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
                WebDriverWait(self.driver, 60).until(
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
        except Exception as e:
            traceback.print_exc()
            print(f"Error logging into Chase: {e}")

    def grab_code():
        """Grabs the code sent to the phone."""
        pass

    def __getattr__(self, name):
        """
        Forwards unknown attribute access to session object.

        Args:
            name (str): The name of the attribute to be accessed.

        Returns:
            The value of the requested attribute from the session object.
        """
        return getattr(self.session, name)
