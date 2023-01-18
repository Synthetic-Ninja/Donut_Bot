import dhooks

import CustomExceptions


class Webhook:
    def __init__(self, url=None):
        match url:
            case None:
                raise CustomExceptions.WebhookInitializationError(f'Webhook url is None')
            case _:
                try:
                    self.__webhook = dhooks.Webhook(url)
                except ValueError:
                    raise CustomExceptions.WebhookInitializationError('Webhook url is not valid')

    def send_embed(self, color, text, tittle) -> None:
        colors = {'blue': 3447003,
                  'green': 3066993,
                  'red': 15158332,
                  'orange': 15105570,
                  'grey': 9807270}
        embed = dhooks.Embed(color=colors[color], timestamp='now', title='DISCORD ASSISTASNCE LOGGER')
        embed.add_field(name=f'LOG TYPE: {tittle}', value=text)
        self.__webhook.send(embed=embed)


