import pathlib
import random
import time
import abc

from loguru import logger as _logger
from selenium.webdriver import Chrome, ChromeOptions
import selenium.common.exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as ec

import CustomExceptions


class BaseBot(metaclass=abc.ABCMeta):
    def __init__(self, driver):
        self._driver = driver

    def __del__(self):
        self._driver.quit()
        _logger.debug('Browser closed')

    def _find_delayed_element(self, mode: str, element_selector: str, timeout=10):
        mods = {'xpath': By.XPATH,
                'css': By.CSS_SELECTOR,
                'classname': By.CLASS_NAME,
                'tag': By.TAG_NAME,
                'id': By.ID}
        match mode.lower():
            case mode if mode in mods:
                _wait = WebDriverWait(self._driver, timeout)
                _logger.debug(f'Waiting element {element_selector}')
                try:
                    element = _wait.until(ec.element_to_be_clickable((mods[mode], element_selector)))
                    _logger.debug(f'Element "{element_selector}" founded')
                except selenium.common.exceptions.TimeoutException:
                    _logger.warning(f"ELEMENT : {element_selector} - not found")
                    element = None
                return element
            case _:
                _logger.error(f"Invalid Atributes")
                raise AttributeError

    def get_server_enter(self) -> None:
        _logger.debug('Searching circle button "add server"')
        if (btn := self._find_delayed_element(mode='classname',
                                              element_selector='circleIconButton-1VxDrg')) is not None:
            btn.click()
        else:
            _logger.error('Circle button "add server" not found')
            raise RuntimeError
        _logger.debug('Searching rectangular button "connect to server"')
        if (btn_sub := self._find_delayed_element(mode='xpath',
                                                  element_selector="/html//div[@id='app-mount']"
                                                                   "//div[@role='dialog']"
                                                                   "/div/div/div/div/div[3]"
                                                                   "/button[@type='button']")) is not None:
            btn_sub.click()
        else:
            _logger.error('rectangular button "connect to server" not found')
            raise RuntimeError

    def join_in_group(self, invite: str) -> None:
        _logger.info(f'Trying to join in group with code: {invite}')
        _logger.debug('Searching invite code field"')
        if (invite_field := self._find_delayed_element(mode='xpath',
                                                       element_selector="/html//div[@id='app-mount']/div[4]/"
                                                                        "/div[@role='dialog']/div/div"
                                                                        "/div/div/div/div[2]"
                                                                        "/form[@class='inputForm-3RoxXV']"
                                                                        "//input")) is not None:
            _logger.debug('Clearing invite field"')
            invite_field.clear()
            _logger.debug('Entering invite code"')
            invite_field.send_keys(invite)
        else:
            _logger.error('Invite field not found')
            raise RuntimeError

        _logger.debug('Search submit button')
        if (submit_btn := self._find_delayed_element(mode='xpath',
                                                     element_selector="/html//div[@id='app-mount']/div[4]"
                                                                      "//div[@role='dialog']"
                                                                      "/div/div/div/div/div"
                                                                      "/div[3]/button[1]")) is not None:
            submit_btn.click()
        else:
            _logger.error('Submit button in join group not found')
            raise RuntimeError

        if (elem := self._find_delayed_element(mode='xpath',
                                               element_selector="/html//div[@id='app-mount']//div[@role='dialog']"
                                                                "/div/div/div/div/div/div[2]"
                                                                "/form[@class='inputForm-3RoxXV']"
                                                                "//h5/span[@class='errorMessage-1kMqS5']")) is not None:
            _logger.error(f'Error joining in guild with message "{elem.get_attribute("textContent")[1:]}"')
            raise CustomExceptions.DiscordEnterLink(f':{invite}')

    def authentication(self, user_token: str) -> None:
        _logger.info(f'Logining in browser with token: {user_token}')
        _logger.debug('Following to discord.com,/login')
        self._driver.get('https://discord.com/login')
        _logger.debug('Executing script')
        try:
            self._driver.execute_script('document.body.appendChild(document.createElement `iframe`).'
                                        'contentWindow.localStorage.token = `"${"' + user_token + '"}"`')
        except selenium.common.exceptions.JavascriptException:
            _logger.error('Error executing script')
            raise RuntimeError
        time.sleep(0.7)
        _logger.debug('Following to discord.com/app')
        self._driver.get('https://discord.com/app')
        if self._find_delayed_element(mode='xpath',
                                      element_selector="/html//div[@id='app-mount']/div[@class='app-3xd6d0']"
                                                       "/div/div[2]/div//section[@class='panels-3wFtMD']"
                                                       "/div[@class='container-YkUktl']/div[1]"
                                                       "/div[@role='img']") is None:

            raise CustomExceptions.DiscordLoginError(f'with token: {user_token}')

    def easy_join_server(self, invite_link: str) -> None:
        _logger.info(f'Joining in server invite: {invite_link}')
        _logger.debug(f'Following a link : {invite_link}')
        self._driver.get(invite_link)
        _logger.debug('Waiting confirm button')
        if (_button := self._find_delayed_element(mode='xpath',
                                                  element_selector="/html//div[@id='app-mount']"
                                                                   "/div[@class='app-1q1i1E']//"
                                                                   "section[@class='authBox-hW6HRx theme-dark']//"
                                                                   "button[@type='button']", timeout=3)) is not None:
            _logger.debug('Clicking confirm button')
            _button.click()
        else:
            _logger.debug('Confirm button not found')
            raise RuntimeError

    def manually_join_server(self, invite_link: str, attempts=3, timeout=(1, 2)) -> None:
        _logger.info('Joining in server')
        self.get_server_enter()
        for attempt in range(attempts):
            try:
                self.join_in_group(invite=invite_link)
                break
            except CustomExceptions.DiscordEnterLink:
                time.sleep(rand_timeout := random.randint(*timeout))
                _logger.info(f'Timeout {rand_timeout}s.')
                continue
        else:
            raise CustomExceptions.DiscordJoinGuild

    def get(self, link):
        self._driver.get(link)

    def close(self):
        self._driver.quit()

    @abc.abstractmethod
    def initialization(cls, headless_param: bool, path_to_webdriver: str):
        pass


class ChromeBot(BaseBot):
    @classmethod
    def initialization(cls, headless_param: bool, path_to_webdriver: str):
        _logger.info('Initializating Browser')
        path = str(pathlib.Path(path_to_webdriver).absolute())
        _logger.debug(f'Patch to driver: {path}')
        options = ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('window-size=1000,1000')
        if headless_param is True:
            options.add_argument('--headless')
        _logger.debug(f'Starting browser with arguments: {options.arguments}')
        try:
            driver = Chrome(executable_path=path, options=options)
            driver.get_log('driver')
            _logger.success('Driver started')
            return cls(driver)
        except selenium.common.exceptions.WebDriverException:
            _logger.error('Invalid Chromedriver path or chromedriver version')
            raise RuntimeError
