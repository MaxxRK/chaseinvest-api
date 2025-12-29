import asyncio
import json
import secrets
import traceback
from typing import TYPE_CHECKING

import anyio
import zendriver as uc

if TYPE_CHECKING:
    from zendriver import Browser, Tab

from .urls import landing_page, login_page, opt_out_verification_page


class ChaseSession:
    """A class to manage a session with Chase.

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

    def __init__(self, *, docker: bool = False, headless: bool = True, title: str | None = None, profile_path: str = ".", debug: bool = False) -> None:
        """Initialize a new instance of the ChaseSession class.

        Args:
            docker (bool, optional): Whether the browser is running in a Docker environment. Defaults to False.
            headless (bool, optional): Whether the browser should run in headless mode. Defaults to True.
            title (string): Denotes the name of the profile and if populated will make the session persistent.
            profile_path (str, optional): The path to the user profile directory for the browser. Defaults to None.
            debug (bool, optional): Enable debug mode. Defaults to False.

        """
        self.docker: bool = docker
        self.headless: bool = headless
        self.title: str | None = title
        self.profile_path: str = profile_path
        self.password: str = ""
        self.browser: Browser
        self.page: Tab
        self.debug: bool = debug
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.get_browser())

    async def get_browser(self) -> None:
        """Initialize a browser instance using zendriver."""
        profile = await anyio.Path(self.profile_path).resolve() / "ZenChase"

        # keep self.profile_path as a string for backward compatibility with other code
        self.profile_path = str(profile)

        if not await profile.exists():
            await profile.parent.mkdir(parents=True, exist_ok=True)

        browser_args = []

        if self.docker:
            browser_args.extend(["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--window-size=1920,1080"])
        elif self.headless:
            browser_args.extend(["--headless=new", "--window-size=1920,1080",
            "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
            "--disable-site-isolation-trials",
            "--disable-features=IsolateOrigins,site-per-process",
            "--disable-session-crashed-bubble",
            "--disable-infobars",
            "--disable-features=TranslateUI,VizDisplayCompositor",
            "--no-first-run",
            "--disable-default-apps",
            "--disable-extensions",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu",
            "--window-size=1920,1080"])
        else:
            browser_args.extend([
                "--start-maximized",
                "--disable-session-crashed-bubble",
                "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36",
                "--disable-infobars",
                "--disable-features=TranslateUI,VizDisplayCompositor",
                "--no-first-run",
                "--disable-default-apps",
                "--disable-extensions",
            ])
        # zendriver has built-in stealth and anti-detection
        self.browser = await uc.start(
            browser_args=browser_args,
            user_data_dir=str(self.profile_path) if self.title else None,
        )
        self.page = await self.browser.get()

    def close_browser(self) -> None:
        """Close the browser.

        Raises:
            RuntimeError: If an unexpected runtime error occurs during browser closure.

        """
        try:
            return self.loop.run_until_complete(self._close_browser_async())
        except RuntimeError as e:
            if "This event loop is already running" in str(e):
                # We're in an async context, schedule the task
                return asyncio.create_task(self._close_browser_async())
            # Some other RuntimeError, re-raise it
            raise

    async def _close_browser_async(self) -> None:
        """Async implementation of close browser."""
        if self.browser:
            await self.browser.stop()

    def login(self, username: str, password: str, last_four: int) -> bool:
        """Log into the website with the provided username and password.

        Args:
            username (str): The user's username.
            password (str): The user's password.
            last_four (int): The last four digits of the user's phone number.

        Returns:
            bool: True if 2FA is required, False otherwise.

        """
        return self.loop.run_until_complete(
            self._login_async(username, password, last_four),
        )

    async def _login_async(self, username: str, password: str, last_four: int) -> bool:
        """Async implementation of login.

        Args:
            username (str): The user's username.
            password (str): The user's password.
            last_four (int): The last four digits of the user's phone number.

        Returns:
            bool: True if 2FA is required, False otherwise.

        Raises:
            Exception: If an unexpected error occurs during the login process.

        """
        try:
            self.password = r"" + password
            await self.page.get(login_page())
            await self.page.sleep(2)

            username_box = await self.page.find("#userId-input-field-input", timeout=30)
            password_box = await self.page.find("#password-input-field-input", timeout=30)

            if not username_box or not password_box:
                raise Exception("Could not find username or password fields.")

            # Scroll to help defeat bot detection?
            await self.page.scroll_down(int(secrets.SystemRandom().uniform(0, 40)), int(secrets.SystemRandom().uniform(900, 1500)))
            for letter in r"" + username:
                await username_box.send_keys(letter)
                await self.page.sleep(secrets.SystemRandom().uniform(0.05, 0.50))
            # Random mouse click to help defeat bot detection?
            await self.page.mouse_click(x=int(secrets.SystemRandom().uniform(0, 400)), y=int(secrets.SystemRandom().uniform(0, 400)), modifiers=0)
            # Scroll to help defeat bot detection?
            await self.page.scroll_up(int(secrets.SystemRandom().uniform(0, 40)), int(secrets.SystemRandom().uniform(900, 1500)))
            for letter in self.password:
                await password_box.send_keys(letter)
                await self.page.sleep(secrets.SystemRandom().uniform(0.05, 0.50))
            # Random mouse click to help defeat bot detection?
            await self.page.mouse_click(x=int(secrets.SystemRandom().uniform(0, 400)), y=int(secrets.SystemRandom().uniform(0, 400)), modifiers=0)
            signin_button = await self.page.find("#signin-button", timeout=5)
            await signin_button.click()
            await self.page.sleep(3)

            # Check if we are on the landing page (successful login without 2FA)
            if landing_page() in self.page.url:  # type: operator
                return False  # No 2FA needed

            # Check for 2FA options
            try:
                options_list = await self.page.find("#optionsList", timeout=15)
                if options_list:
                    # Handle shadow DOM
                    shadow_elements = await self.page.select_all(
                        "#optionsList *", timeout=5,
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
                    try:
                        approve_text = await self.page.find("text=approve", timeout=2)
                        if approve_text:
                            print(
                                "Chase is asking for 2FA from the phone app. You have 120 seconds to approve it.",
                            )
                            # Wait for redirect to landing page
                            for _ in range(120):
                                await self.page.sleep(1)
                                if landing_page() in self.page.url:
                                    return False
                    except TimeoutError:
                        # Timed out waiting for push notification moving on to text message flow
                        pass
                    try:
                        # Text message flow
                        radio_group = await self.page.find("mds-radio-group", timeout=15)
                        if radio_group:
                            attrs = radio_group.attrs
                            radio_buttons_json = attrs.get("radio-buttons") if attrs else None
                            if radio_buttons_json:
                                radio_buttons = json.loads(radio_buttons_json)
                                # Find the index of the button matching last_four
                                for index, button in enumerate(radio_buttons):
                                    if f"xxx-xxx-{last_four}" in button.get("label", ""):
                                        # Set the selected-index attribute using JavaScript
                                        await radio_group.apply(f"""
                                            el => {{
                                                el.setAttribute('selected-index', '{index}');
                                                el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                            }}
                                        """)
                                        await self.page.sleep(0.5)
                                        print(f"Selected radio button: {button['label']}")
                                        break
                            next_btn = await self.page.find("#next-content", timeout=5)
                            await next_btn.click()
                            return True  # 2FA code will be needed
                    except TimeoutError:
                        # Timed out waiting for text message option moving on to old 2fa flow.
                        pass

            except TimeoutError:
                # New 2FA options not found, proceed to old 2FA flow
                try:
                    dropdown = await self.page.find(
                        "#header-simplerAuth-dropdownoptions-styledselect", timeout=5,
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
                # Trying to verify with xpath. This is untested in zendriver.
                skip_btn = await self.page.find("//button[contains(., 'Skip this step next time')]", timeout=5)
                await skip_btn.click()

                save_btn = await self.page.find("//button[contains(., 'Save and go to account')]", timeout=5)
                await save_btn.click()

            # Final check
            if landing_page() in self.page.url:
                return False

            raise Exception("Login failed due to an unknown page state.")

        except Exception as e:
            await self.close_browser()
            traceback.print_exc()
            raise Exception(f"Error in first step of login into Chase: {e}")

    def login_two(self, code: str) -> bool:
        """Perform the second step of login if 2FA needed.

        Args:
            code (str): 2FA code sent to users phone.

        Returns:
            bool: True if login is successful, False otherwise.

        """
        return self.loop.run_until_complete(self._login_two_async(code))

    async def _login_two_async(self, code: str) -> bool:
        """Async perform the second step of login if 2FA needed.

        Returns:
            bool: True if login is successful, False otherwise.

        Raises:
            TimeoutError: If landing page is not reached within 60 seconds.

        """
        try:
            code = str(code)
            await self.page.sleep(2)

            try:
                code_entry = await self.page.find("#otpInput", timeout=15)
                if code_entry:
                    await code_entry.send_keys(code)
                    next_btn = await self.page.find("#next-content", timeout=5)
                    await next_btn.click()
            except TimeoutError:
                pass

            try:
                # This is an old 2fa login flow untested in zendriver and probably obsolete
                otp_field = await self.page.find("#otpcode_input-input-field", timeout=15)
                await otp_field.send_keys(code)
                pwd_field = await self.page.find("#password_input-input-field", timeout=5)
                await pwd_field.send_keys(self.password)
                submit_btn = await self.page.find('button[type="submit"]', timeout=5)
                await submit_btn.click()
            except TimeoutError:
                pass

            try:
                await self.page.sleep(2)
                # Check for opt-out page
                if opt_out_verification_page() in self.page.url:
                    # Trying to verify with xpath. This is untested in zendriver.
                    skip_btn = await self.page.find("//button[contains(., 'Skip this step next time')]", timeout=5)
                    await skip_btn.click()

                    save_btn = await self.page.find("//button[contains(., 'Save and go to account')]", timeout=5)
                    await save_btn.click()
            except TimeoutError:
                pass

            # Wait for landing page
            for _ in range(60):
                await self.page.sleep(1)
                if landing_page() in self.page.url:
                    return True

            error_msg = "Failed to login to Chase. Landing page not reached after 60 seconds."
            raise TimeoutError(error_msg)

        except Exception as e:
            await self.close_browser()
            traceback.print_exc()
            print(f"Error logging into Chase: {e}")
            return False
