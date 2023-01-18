from loguru import logger as _logger
import tweepy


class Twitter:
    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 access_token: str,
                 access_token_secret: str
                 ):
        auth = tweepy.OAuthHandler(api_key, api_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)

    def get_api(self) -> tweepy.api:
        # print(self.api)
        return self.api


class Listener(tweepy.Stream):
    tweet = []

    def on_status(self, status) -> None:
        self.tweet.append(status)
        _logger.debug(status)
        self.disconnect()

    def on_request_error(self, status_code) -> None:
        _logger.error(f'Connection to Twitter error with statuscode: {status_code}')
        self.disconnect()

    def add_users_in_filter(self, filtered_users: list) -> None:
        user_ids = [Twitter(self.consumer_key,
                            self.consumer_secret,
                            self.access_token,
                            self.access_token_secret
                            ).get_api().get_user(screen_name=user).id for user in filtered_users]
        self.filter(follow=user_ids)
