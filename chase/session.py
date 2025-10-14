import json
import os
import traceback

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_stealth import StealthConfig, stealth_sync

from .urls import landing_page, login_page, opt_out_verification_page


class ChaseSession:
    """
    A class to manage a session with Chase.

    This class provides methods to initialize a WebDriver with the necessary options, log into Chase, and perform other actions on the Chase website.

    Attributes:
        title (str): Denotes the name of the profile and if populated will make the session persistent.
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

    def __init__(self, headless=True, title=None, profile_path=".", debug=False):
        """
        Initializes a new instance of the ChaseSession class.

        Args:
            title (string): Denotes the name of the profile and if populated will make the session persistent.
            headless (bool, optional): Whether the WebDriver should run in headless mode. Defaults to True.
            docker (bool, optional): Whether the session is running in a Docker container. Defaults to False.
            profile_path (str, optional): The path to the user profile directory for the WebDriver. Defaults to None.
        """
        self.headless: bool = headless
        self.title: str = title
        self.profile_path: str = profile_path
        self.password: str = ""
        self.context = None
        self.page = None
        self.debug: bool = debug
        self.playwright = sync_playwright().start()
        self.stealth_config = StealthConfig(
            navigator_languages=True,
            navigator_user_agent=True,
            navigator_vendor=True,
        )
        self.get_browser()

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        The with statement will bind this method’s return value to the target(s) specified in the as clause of the statement.

        Returns:
            self: Returns the instance of the class.
        """
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """
        Exit the runtime context related to this object.

        The parameters describe the exception that caused the context to be exited.

        Args:
            exc_type (Type[BaseException]): The type of the exception.
            exc_value (BaseException): The instance of the exception.
            traceback (TracebackType): A traceback object encapsulating the call stack at the point where the exception was raised.

        If the context was exited without an exception, all three arguments will be None.
        """
        if exc_type is not None:
            print("An error occurred in the context manager:")
            traceback.print_exception(exc_type, exc_value, tb)
        self.close_browser()

    def get_browser(self):
        """
        Initializes and returns a browser instance.

        This method checks if a profile path exists, creates one if it doesn't,
        and then launches a new browser instance with the specified user agent,
        viewport, and storage state. It also creates a new page in the browser context and applies stealth settings to it.

        Returns:
            None

        Raises:
            FileNotFoundError: If the profile path does not exist and cannot be created.
            Error: If the browser cannot be launched or the page cannot be created.
        """
        self.profile_path = os.path.abspath(self.profile_path)
        if self.title is not None:
            self.profile_path = os.path.join(
                self.profile_path, f"Chase_{self.title}.json"
            )
        else:
            self.profile_path = os.path.join(self.profile_path, "Chase.json")
        if not os.path.exists(self.profile_path):
            os.makedirs(os.path.dirname(self.profile_path), exist_ok=True)
            with open(self.profile_path, "w") as f:
                json.dump({}, f)
        if self.headless:
            self.browser = self.playwright.firefox.launch(
                headless=True,
                args=["--disable-webgl", "--disable-software-rasterizer"],
            )
        else:
            self.browser = self.playwright.firefox.launch(
                headless=False,
                args=["--disable-webgl", "--disable-software-rasterizer"],
            )
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            storage_state=self.profile_path if self.title is not None else None,
        )
        if self.debug:
            self.context.tracing.start(
                name="chase_trace", screenshots=True, snapshots=True
            )
        self.page = self.context.new_page()
        stealth_sync(self.page, self.stealth_config)

    def save_storage_state(self):
        """
        Saves the storage state of the browser to a file.

        This method saves the storage state of the browser to a file so that it can be restored later.

        Args:
            filename (str): The name of the file to save the storage state to.
        """
        storage_state = self.page.context.storage_state()
        with open(self.profile_path, "w") as f:
            json.dump(storage_state, f)

    def close_browser(self):
        """Closes the browser."""
        self.save_storage_state()
        if self.debug:
            self.context.tracing.stop(
                path=f'./chase_trace{self.title if self.title is not None else ""}.zip'
            )
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
            self.password = r"" + password
            self.page.goto(login_page())
            self.page.wait_for_selector("#signin-button", timeout=30000)

            username_box = self.page.query_selector("#userId-input-field-input")
            password_box = self.page.query_selector("#password-input-field-input")

            if not username_box or not password_box:
                raise Exception("Could not find username or password fields.")

            username_box.type(r"" + username)
            password_box.type(self.password)
            self.page.click("#signin-button", timeout=5000)

            # Wait for navigation to complete after login attempt
            self.page.wait_for_load_state("networkidle", timeout=30000)

            # Check if we are on the landing page (successful login without 2FA)
            if self.page.url == landing_page():
                if self.title is not None:
                    self.save_storage_state()
                return False  # No 2FA needed

            # If not on the landing page, check for 2FA options

            try:
                self.page.wait_for_selector("#optionsList", timeout=15000)
                try:
                    options_list = self.page.query_selector("#optionsList")
                    # Login now has a shadw DOM for the 2FA options, so we need to access it
                    shadow_root = options_list.get_property("shadowRoot")
                    if shadow_root:
                        try:
                            auth_elements = shadow_root.query_selector_all("*")
                            for element in auth_elements:
                                try:
                                    text_content = element.text_content()
                                    if text_content and "Get a text" in text_content:
                                        element.click()
                                        print("Clicked 'Get a text' option")
                                        break
                                    elif (
                                        text_content
                                        and "push notification" in text_content
                                    ):
                                        element.click()
                                        print("Clicked 'push notification' option")
                                        break
                                except Exception:
                                    raise Exception(
                                        "Could not find any clickable elements in shadow root"
                                    )
                        except Exception as e3:
                            print(f"Python shadow DOM search failed: {e3}")
                            raise e3
                    else:
                        raise Exception("No shadow root property accessible")

                except Exception as e2:
                    print(f"Direct shadow root access failed: {e2}")

                # Wait for the selection to register
                self.page.wait_for_timeout(1000)

                # Continue with Next button
                self.page.get_by_role("button", name="Next").click()

                # Handle the 2FA flow based on what was selected
                try:
                    # Check if we're on a push notification wait screen
                    if self.page.locator("text=approve").is_visible(timeout=2000):
                        print(
                            "Chase is asking for 2FA from the phone app. You have 120 seconds to approve it."
                        )
                        self.page.wait_for_url(landing_page(), timeout=120000)
                        if self.title is not None:
                            self.save_storage_state()
                        return False
                    else:
                        # Assume text message flow
                        try:
                            radio_button = self.page.get_by_label(
                                f"xxx-xxx-{last_four}"
                            )
                            radio_button.wait_for(state="visible", timeout=5000)
                            radio_button.check()
                            self.page.get_by_role("button", name="Next").click()
                        except PlaywrightTimeoutError:
                            pass
                        return True

                except PlaywrightTimeoutError:
                    return True

            except PlaywrightTimeoutError:
                # If neither 2FA option is found, check for other scenarios
                try:
                    # Fallback for older 2FA UI
                    self.page.wait_for_selector(
                        "#header-simplerAuth-dropdownoptions-styledselect", timeout=5000
                    )
                    dropdown = self.page.query_selector(
                        "#header-simplerAuth-dropdownoptions-styledselect"
                    )
                    dropdown.click()
                    options_ls = self.page.query_selector_all('li[role="presentation"]')
                    for item in options_ls:
                        if str(last_four) in item.text_content():
                            item.click()
                            break
                    self.page.click('button[type="submit"]')
                    return True
                except PlaywrightTimeoutError:
                    # Check for "Skip this step next time"
                    try:
                        self.page.wait_for_url(
                            opt_out_verification_page(), timeout=2000
                        )
                        self.page.get_by_text(
                            "Skip this step next time,", exact=False
                        ).click(timeout=5000)
                        self.page.get_by_role(
                            "button", name="Save and go to account"
                        ).click()
                    except PlaywrightTimeoutError:
                        pass  # Not on the opt-out page

            # Final check to see if we landed on the dashboard
            if self.page.url == landing_page():
                if self.title is not None:
                    self.save_storage_state()
                return False

            # If we reach here, something unexpected happened
            raise Exception("Login failed due to an unknown page state.")

        except Exception as e:
            self.close_browser()
            traceback.print_exc()
            raise Exception(f"Error in first step of login into Chase: {e}")

    def login_two(self, code):
        """
        Performs the second step of login if 2fa needed.

        Args:
            code (str): 2fa code sent to users phone.

        Raises:
            Exception: Failed to login to chase.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        try:
            code = str(code)
            try:
                self.page.wait_for_load_state(state="networkidle", timeout=15000)
            except PlaywrightTimeoutError:
                raise Exception("Timeout loading 2fa page!")
            try:
                # This returns two elements now need to select the first one
                code_entry = self.page.get_by_label("Enter your code").first
                code_entry.type(code, timeout=15000)
                self.page.get_by_role("button", name="Next").click()
            except PlaywrightTimeoutError:
                pass
            try:
                self.page.wait_for_selector("#otpcode_input-input-field", timeout=15000)
                self.page.fill("#otpcode_input-input-field", code)
                self.page.fill("#password_input-input-field", self.password)
                self.page.click('button[type="submit"]')
            except PlaywrightTimeoutError:
                pass
            try:
                self.page.wait_for_load_state(state="load", timeout=15000)
                self.page.wait_for_url(opt_out_verification_page(), timeout=1000)
                self.page.get_by_text("Skip this step next time,", exact=False).click(
                    timeout=5000
                )
                self.page.get_by_role("button", name="Save and go to account").click()
            except PlaywrightTimeoutError:
                pass
            try:
                self.page.wait_for_load_state("load", timeout=30000)
                self.page.wait_for_url(landing_page(), timeout=60000)
                if self.title is not None:
                    self.save_storage_state()
                return True
            except PlaywrightTimeoutError:
                raise Exception("Failed to login to Chase")
        except Exception as e:
            self.close_browser()
            traceback.print_exc()
            print(f"Error logging into Chase: {e}")
            return False
