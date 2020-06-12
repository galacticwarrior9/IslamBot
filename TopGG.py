import configparser
import dbl
from discord.ext import commands

config = configparser.ConfigParser()
config.read('config.ini')


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = config['APIs']['top.gg']
        self.dblpy = dbl.DBLClient(self.bot, self.token, autopost=True)

    async def on_guild_post(self):
        print("Server count posted successfully")


def setup(bot):
    bot.add_cog(TopGG(bot))
