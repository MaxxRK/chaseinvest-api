import json
import os
import traceback
import asyncio

import zendriver as uc

from .urls import landing_page, login_page, opt_out_verification_page


class ChaseSession:
    """
    A class to manage a session with Chase.

    This class provides methods to initialize a browser with the necessary options, log into Chase, and perform other actions on the Chase website.

    Attributes:
        title (str): Denotes the name of the profile and if populated will make the session persistent.
        headless (bool): Whether the browser should run in headless mode.
        profile_path (str): The path to the user profile directory for the browser.
        driver: The browser instance used to interact with the Chase website.

    Methods:
        get_browser(): Initializes and returns a browser with the necessary options.
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
            headless (bool, optional): Whether the browser should run in headless mode. Defaults to True.
            profile_path (str, optional): The path to the user profile directory for the browser. Defaults to None.
            debug (bool, optional): Enable debug mode. Defaults to False.
        """
        self.headless: bool = headless
        self.title: str = title
        self.profile_path: str = profile_path
        self.password: str = ""
        self.browser = None
        self.page = None
        self.debug: bool = debug
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.get_browser())

    def __enter__(self):
        """
        Enter the runtime context related to this object.

        Returns:
            self: Returns the instance of the class.
        """
        return self

    def __exit__(self, exc_type, exc_value, tb):
        """
        Exit the runtime context related to this object.

        Args:
            exc_type (Type[BaseException]): The type of the exception.
            exc_value (BaseException): The instance of the exception.
            tb (TracebackType): A traceback object encapsulating the call stack.
        """
        if exc_type is not None:
            print("An error occurred in the context manager:")
            traceback.print_exception(exc_type, exc_value, tb)
        self.loop.run_until_complete(self.close_browser())
        self.loop.close()

    async def get_browser(self):
        """
        Initializes and returns a browser instance using zendriver.

        Returns:
            None
        """
        self.profile_path = os.path.join(os.path.abspath(self.profile_path), "ZenChase")
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

        browser_args = []
        if self.headless:
            browser_args.append("--headless=new")
            browser_args.append("--window-size=1920,1080")
            browser_args.append("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36")
        else:
            browser_args.append("--start-maximized")
        # zendriver has built-in stealth and anti-detection
        self.browser = await uc.start(
            browser_args=browser_args,
            user_data_dir=os.path.dirname(self.profile_path) if self.title else None,
        )
        self.page = await self.browser.get()

    def save_storage_state(self):
        """
        Saves the storage state of the browser to a file.
        """
        # Note: zendriver uses user_data_dir for persistence
        # Additional state can be saved if needed
        pass

    async def close_browser(self):
        """Closes the browser."""
        if self.browser:
            await self.browser.stop()

    def login(self, username, password, last_four):
        """
        Logs into the website with the provided username and password.

        Args:
            username (str): The user's username.
            password (str): The user's password.
            last_four (int): The last four digits of the user's phone number.

        Returns:
            bool: True if 2FA is required, False otherwise.
        """
        return self.loop.run_until_complete(
            self._login_async(username, password, last_four)
        )

    async def _login_async(self, username, password, last_four):
        """Async implementation of login."""
        try:
            self.password = r"" + password
            await self.page.get(login_page())
            await self.page.sleep(2)

            username_box = await self.page.find("#userId-input-field-input", timeout=30)
            password_box = await self.page.find("#password-input-field-input", timeout=30)

            if not username_box or not password_box:
                raise Exception("Could not find username or password fields.")

            await username_box.send_keys(r"" + username)
            await password_box.send_keys(self.password)
            
            signin_button = await self.page.find("#signin-button", timeout=5)
            await signin_button.click()
            await self.page.sleep(3)

            # Check if we are on the landing page (successful login without 2FA)
            if landing_page() in self.page.url:
                return False  # No 2FA needed

            # Check for 2FA options
            try:
                options_list = await self.page.find("#optionsList", timeout=15)
                if options_list:
                    # Handle shadow DOM
                    shadow_elements = await self.page.select_all(
                        "#optionsList *", timeout=5
                    )
                    for element in shadow_elements:
                        attrs = element.attrs
                        text = attrs.get("label") if attrs else None
                        if text and ("Get a text" in text or "push notification" in text):
                            # Use JavaScript to click instead of element.click()
                            await element.apply("el => el.click()")
                            break
                    await self.page.sleep(1)

                    # Check for push notification
                    input("before first here")
                    try:
                        print("here")
                        approve_text = await self.page.find("text=approve", timeout=2)
                        if approve_text:
                            print(
                                "Chase is asking for 2FA from the phone app. You have 120 seconds to approve it."
                            )
                            # Wait for redirect to landing page
                            for _ in range(120):
                                await self.page.sleep(1)
                                if landing_page() in self.page.url:
                                    return False
                    except asyncio.TimeoutError:
                        # Timed out waiting for push notification moving on to text message flow
                        pass
                    try:
                            input()
                            #Text message flow
                            radio_elements = await self.page.find("mds-radio-group", timeout=15)
                            print(f"Radio elements: {radio_elements}")
                            if radio_elements:
                                #Handle shadow DOM
                                shadow_elements = await self.page.select_all(
                                    "mds-radio-group *", timeout=5
                                )
                                print(f"Shadow elements: {shadow_elements}")
                                for element in shadow_elements:
                                    attrs = element.attrs
                                    text = attrs.get("label") if attrs else None
                                    print(f"Element text: {text}")
                                    if text and f"xxx-xxx-{last_four}" in text:
                                        #Use JavaScript to click instead of element.click()
                                        await element.apply("el => el.click()")
                                        break
                                #radio_label = await self.page.find(
                                    #f"mds-radio-group >> label:has-text('xxx-xxx-{last_four}')", timeout=5
                                #)
                            #print(f"Radio label: {radio_label}")
                            #await radio_label.click()
                            next_btn = await self.page.find("button[name='Next']", timeout=5)
                            await next_btn.click()
                    except asyncio.TimeoutError:
                        #Timed out waiting for text message option moving on to old 2fa flow.
                        pass

            except asyncio.TimeoutError:
                # New 2FA options not found, proceed to old 2FA flow
                try:
                    dropdown = await self.page.find(
                        "#header-simplerAuth-dropdownoptions-styledselect", timeout=5
                    )
                    await dropdown.click()
                    options = await self.page.query_selector_all('li[role="presentation"]')
                    for item in options:
                        text = await item.text
                        if str(last_four) in text:
                            await item.click()
                            break
                    submit_btn = await self.page.find('button[type="submit"]', timeout=5)
                    await submit_btn.click()
                    return True
                except asyncio.TimeoutError:
                    pass

            # Check for opt-out page
            if opt_out_verification_page() in self.page.url:
                skip_btn = await self.page.find("text=Skip this step next time", timeout=5)
                await skip_btn.click()
                save_btn = await self.page.find("button[name='Save and go to account']", timeout=5)
                await save_btn.click()

            # Final check
            if landing_page() in self.page.url:
                return False

            raise Exception("Login failed due to an unknown page state.")

        except Exception as e:
            await self.close_browser()
            traceback.print_exc()
            raise Exception(f"Error in first step of login into Chase: {e}")

    def login_two(self, code):
        """
        Performs the second step of login if 2FA needed.

        Args:
            code (str): 2FA code sent to users phone.

        Returns:
            bool: True if login is successful, False otherwise.
        """
        return self.loop.run_until_complete(self._login_two_async(code))

    async def _login_two_async(self, code):
        """Async implementation of login_two."""
        try:
            code = str(code)
            await self.page.sleep(2)

            try:
                code_entries = await self.page.query_selector_all("[aria-label='Enter your code']")
                if code_entries:
                    await code_entries[0].send_keys(code)
                    next_btn = await self.page.find("button[name='Next']", timeout=15)
                    await next_btn.click()
            except:
                pass

            try:
                otp_field = await self.page.find("#otpcode_input-input-field", timeout=15)
                await otp_field.send_keys(code)
                pwd_field = await self.page.find("#password_input-input-field", timeout=5)
                await pwd_field.send_keys(self.password)
                submit_btn = await self.page.find('button[type="submit"]', timeout=5)
                await submit_btn.click()
            except:
                pass

            try:
                await self.page.sleep(2)
                if opt_out_verification_page() in self.page.url:
                    skip_btn = await self.page.find("text=Skip this step next time", timeout=5)
                    await skip_btn.click()
                    save_btn = await self.page.find("button[name='Save and go to account']", timeout=5)
                    await save_btn.click()
            except:
                pass

            # Wait for landing page
            for _ in range(60):
                await self.page.sleep(1)
                if landing_page() in self.page.url:
                    return True

            raise Exception("Failed to login to Chase")

        except Exception as e:
            await self.close_browser()
            traceback.print_exc()
            print(f"Error logging into Chase: {e}")
            return False
