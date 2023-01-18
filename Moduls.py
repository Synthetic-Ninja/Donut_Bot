import sys
import time
import re
import asyncio

import tweepy.errors
from loguru import logger as _logger
import discord
import emoji

# from DiscordBrowserBot import ChromeBot
import CustomExceptions
from TweeterHandler import Listener
from DiscordApiBot import Discord


class InviteMonitor:
    def __init__(self,
                 discord_token: str,
                 twitter_api: str,
                 twitter_api_secret: str,
                 twitter_access: str,
                 twitter_access_secret: str,
                 monitoring_users: list,
                 communicator):
        self.communicator = communicator
        self.discord_token = discord_token
        self.twittter_api = twitter_api
        self.twittter_api_secret = twitter_api_secret
        self.twitter_access = twitter_access
        self.twitter_access_secret = twitter_access_secret
        self.monitoring_users = monitoring_users
        self.discord_client = Discord()

    def start_module(self) -> None:
        try:
            self.discord_client.authentication(self.discord_token)
            _logger.success(f'Successful login with token as "{self.discord_client.client}"')
        except CustomExceptions.DiscordLoginError:
            _logger.error(f'Error login as {self.discord_token}')
            raise RuntimeError
        self.communicator.unlockDeleteButton.emit()
        while True:
            _logger.success(f'Monitoring twitter accounts "{self.monitoring_users}" for invite_code')
            try:
                stream_tweet = Listener(self.twittter_api,
                                        self.twittter_api_secret,
                                        self.twitter_access,
                                        self.twitter_access_secret)
                stream_tweet.add_users_in_filter(filtered_users=self.monitoring_users)
            except tweepy.errors.TweepyException as e:
                _logger.error(
                    f'Connection reset with message {e}. If connection reset by peer please use VPN for connection')
                raise RuntimeError
            except tweepy.errors.Unauthorized:
                _logger.error(f'Error twitter authentication')
                raise RuntimeError
            try:
                encrypted_message = stream_tweet.tweet[0]
            except IndexError:
                raise RuntimeError
            text = re.sub('\n', ' ', encrypted_message._json['text']).split()
            messages = [word for word in text if len(word) >= 7 and ':' in emoji.demojize(word)]
            decrypted_code = list(map(lambda message: re.sub("[^A-Za-z0-9]", "", message), messages))
            for code in decrypted_code:
                try:
                    self.discord_client.join_in_guild(code)
                    _logger.success('Successful accept invite')
                    break
                except CustomExceptions.DiscordJoinGuild:
                    continue
            else:
                _logger.error("Can't accept invite")
                continue

    def stop_module(self):
        del self


class EventJoiner(discord.Client):
    def __init__(self,
                 discord_token: str,
                 channel: int,
                 author_id: int,
                 embed: bool,
                 keyword: str,
                 reaction_emoji: str,
                 loop,
                 communicator
                 ):
        super().__init__()
        self.case = dict()[channel] = {'author_id': author_id,
                                       'embed': embed,
                                       'keyword': keyword.lower(),
                                       'reaction_emoji': reaction_emoji,
                                       }
        self.discord_token = discord_token
        self.loop = loop

        # task = loop.create_task()
        loop.run_until_complete(self.run(self.discord_token))

    async def on_ready(self) -> None:
        _logger.success(f'Successful logged on as {self.user}!')

    async def on_message(self, message) -> None:
        _logger.debug(message)
        if message.channel.id in self.case:
            if message.author.id == self.case[message.channel.id]['author_id']:
                if self.case[message.channel.id]['embed'] is True:
                    try:
                        message_content = message.embeds[0].title
                    except IndexError:
                        message_content = ''
                else:
                    message_content = message.content
                _logger.debug(message_content)
                if self.case[message.channel.id]['keyword'] in message_content.lower():
                    _logger.debug(f'Giveaway message by {message.author} recived')
                    await asyncio.sleep(2)
                    try:
                        await message.add_reaction(self.case[message.channel.id]['reaction_emoji'])
                        _logger.success(
                            f'Successful join in event from "{message.guild}[{message.channel}]" by {self.user}')
                    except discord.errors.HTTPException:
                        _logger.debug('Emoji not found on message')

    # def add_case(self,
    #              channel: int,
    #              author_id: int,
    #              embed: bool,
    #              keyword: str,
    #              reaction_emoji: str) -> None:
    #     _logger.debug(f'Adding case {channel} with parameters {(author_id, embed, keyword, reaction_emoji)}')
    #     self.case[channel] = {'author_id': author_id,
    #                           'embed': embed,
    #                           'keyword': keyword.lower(),
    #                           'reaction_emoji': reaction_emoji,
    #                           }

    # def remove_case(self, case_id: int) -> None:
    #     _logger.debug(f'Deleting case {case_id}')
    #     del self.case[case_id]

    def start_module(self) -> None:

        #self.loop.run_until_complete()
        time.sleep(100)

    def stop_module(self):
        _logger.success('Browser closing')

class Shazam:
    def __init__(self, **args):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(discord.Client().run('OTAwMzQwNDYxNzQxNDE2NTI4.YhcwYA.UlFbqSQQebrOYRteX89_pJ73RhA'))

        #EventJoiner(*args).run('OTAwMzQwNDYxNzQxNDE2NTI4.YhcwYA.UlFbqSQQebrOYRteX89_pJ73RhA')

    def start_module(self):
        print('ok')

    def stop_module(self):
        print('ok')