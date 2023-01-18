class BaseError(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None


class DiscordLoginError(BaseError):
    def __str__(self):
        error_msg = 'Account login error'
        return error_msg if self.message is None else f'{error_msg}, {self.message}'


class DiscordEnterLink(BaseError):
    def __str__(self):
        error_msg = 'Error joing with link'
        return error_msg if self.message is None else f'{error_msg}, {self.message}'


class DiscordJoinGuild(BaseError):
    def __str__(self):
        error_msg = 'Error joining in Guild'
        return error_msg if self.message is None else f'{error_msg}, {self.message}'


class WebhookInitializationError(BaseError):
    def __str__(self):
        error_msg = 'Error iniatilizating Webhook'
        return error_msg if self.message is None else f'{error_msg}, {self.message}'
