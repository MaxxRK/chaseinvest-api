import os
import traceback
import requests
from time import sleep


from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from .urls import auth_code_page, login_page


class FileChange(FileSystemEventHandler):
    """
    A class that inherits from FileSystemEventHandler to handle file change events.

    This class overrides the `on_modified` method from FileSystemEventHandler to set a flag when a specific file is modified.

    Attributes:
        filename (str): The name of the file to watch for modifications.
        file_modified (bool): A flag that indicates whether the file has been modified.
    """

    def __init__(self, filename):
        self.filename = filename
        self.file_modified = False

    def on_modified(self, event):
        """
        Called when a file or directory is modified.

        If the modified file is not a directory and its name ends with the filename this instance is watching,
        the `file_modified` flag is set to True.

        Args:
            event (FileSystemEvent): The event object representing the file system event.
        """
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

    def __init__(self, external_code=False):
        """
        Initializes a new instance of the ChaseSession class.

        Args:
            title (string): Denotes the name of the profile and if populated will make the session persistent.
            headless (bool, optional): Whether the WebDriver should run in headless mode. Defaults to True.
            docker (bool, optional): Whether the session is running in a Docker container. Defaults to False.
        """
        self.external_code: bool = external_code
        self.need_code: bool = False
        self.session = requests.Session()


    def get_login_code(self, queue):
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
            queue.put((self.need_code, "code"))
            event_handler = FileChange(".code")
            observer = Observer()
            observer.schedule(event_handler, path=".", recursive=False)
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
            os.remove(".code")
        return code

    def login(self, username, password, last_four, queue=None):
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
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                + "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
            }
        )
        response = self.session.get("https://www.chase.com/ruxitagentjs_ICA27NQVfhqrux_10269230920162641.js")
        print(response.status_code)
        self.session.headers.update(response.headers)
        print(self.session.headers)
        print(self.session.cookies.get_dict())
        response = self.session.get("https://www.chase.com/ruxitagentjs_D_10269230920162641.js")
        print(response.status_code)
        print(response.headers)
        print(self.session.cookies.get_dict())
        
    def __getattr__(self, name):
        """
        Forwards unknown attribute access to session object.

        Args:
            name (str): The name of the attribute to be accessed.

        Returns:
            The value of the requested attribute from the session object.
        """
        return getattr(self.session, name)
