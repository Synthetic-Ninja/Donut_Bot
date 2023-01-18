import re
from base64 import b64encode
import json

from urllib.parse import quote as _uriquote

import requests
from loguru import logger as _logger

import CustomExceptions


class Utils:
    def json_or_text(self, response):
        text = response.text(encoding='utf-8')
        try:
            if response.headers['content-type'] == 'application/json':
                return json.loads(text)
        except KeyError:
            pass

        return text

    def get_build_number(self, session):
        """Fetches client build number"""
        try:
            login_page_request = session.get('https://discord.com/login', headers={'Accept-Encoding': 'gzip, deflate'})
            login_page = login_page_request.text
            build_url = 'https://discord.com/assets/' + re.compile(r'assets/+([a-z0-9]+)\.js').findall(login_page)[
                -2] + '.js'
            build_request = session.get(build_url, headers={'Accept-Encoding': 'gzip, deflate'})
            build_file = build_request.text
            build_index = build_file.find('buildNumber') + 24
            return int(build_file[build_index:build_index + 6])
        except Exception as e:
            _logger.warning(f'Could not fetch client build number. With exception {e}')
            return 88863


class Route:
    BASE = 'https://discord.com/api/v7'

    def __init__(self, method, path, **parameters):
        self.path = path
        self.method = method
        url = (self.BASE + self.path)
        if parameters:
            self.url = url.format(**{k: _uriquote(v) if isinstance(v, str) else v for k, v in parameters.items()})
        else:
            self.url = url

        # major parameters:
        self.channel_id = parameters.get('channel_id')
        self.guild_id = parameters.get('guild_id')

    @property
    def bucket(self):
        # the bucket is just method + path w/ major parameters
        return '{0.channel_id}:{0.guild_id}:{0.path}'.format(self)


class HTTPClient:
    """Represents an HTTP client sending HTTP requests to the Discord API."""
    def __init__(self):
        self.__session = None
        self.utils = Utils()

    def startup_tasks(self):
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36"
        self.client_build_number = self.utils.get_build_number(self.__session)
        self.browser_version = '91.0.4472.77'
        self.super_properties = {
            'os': 'Windows',
            'browser': 'Chrome',
            'device': '',
            'browser_user_agent': user_agent,
            'browser_version': self.browser_version,
            'os_version': '10',
            'referrer': '',
            'referring_domain': '',
            'referrer_current': '',
            'referring_domain_current': '',
            'release_channel': 'stable',
            'system_locale': 'en-US',
            'client_build_number': self.client_build_number,
            'client_event_source': None
        }
        self.encoded_super_properties = b64encode(json.dumps(self.super_properties).encode()).decode('utf-8')

    def request(self, route, *, files=None, form=None, **kwargs):
        bucket = route.bucket
        methods = {'GET': self.__session.get,
                   'POST': self.__session.post
                   }

        method = route.method
        url = route.url

        # header creation
        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'en-US',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Origin': 'https://discord.com',
            'Pragma': 'no-cache',
            'Referer': 'https://discord.com/channels/@me',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'User-Agent': self.user_agent,
            'X-Super-Properties': self.encoded_super_properties
        }

        if self.token is not None:
            headers['Authorization'] = self.token

        resp = methods[method](url=url, headers=headers)
        return resp

    def static_login(self, token):
        self.__session = requests.session()
        self._token(token)
        self.startup_tasks()
        _logger.debug('Try to send login request')
        data = self.request(Route('GET', '/users/@me'))
        if data.status_code == 200:
            return data.json()
        else:
            _logger.error('Error sending login request')
            return None

    def accept_invite(self, invite_code):
        url = f'/invites/{invite_code}'
        _logger.debug('Try to send invite request')
        response = self.request(Route('POST', url))
        _logger.debug(response.status_code)
        _logger.debug(response.text)
        if response.status_code == 200:
            return response
        else:
            _logger.error('Error sending invite request')
            return None

    def _token(self, token):
        self.token = token
        self._ack_token = None


class Discord:
    def __init__(self):
        self.__client = HTTPClient()
        self.client = None
        self.client_nickname = None
        self.discriminator = None

    def authentication(self, token):
        _logger.debug(f'Try to send authentication request with token: "{token}"')
        if (login_response := self.__client.static_login(token=token)) is not None:
            _logger.debug(login_response)
            self.client_nickname = login_response['username']
            self.discriminator = login_response['discriminator']
            self.client = f'{self.client_nickname}#{self.discriminator}'

        else:
            _logger.warning('Account login problem')
            raise CustomExceptions.DiscordLoginError

    def join_in_guild(self, invite_code):
        join_responce = self.__client.accept_invite(invite_code=invite_code)
        if join_responce is not None:
            _logger.success('Successful joining')
        else:
            raise CustomExceptions.DiscordJoinGuild

