import configparser

import topgg
from discord.ext import commands

config = configparser.ConfigParser()
config.read('config.ini')


class TopGG(commands.Cog):
    """Handles interactions with the top.gg API"""

    def __init__(self, bot):
        self.bot = bot
        self.token = config['APIs']['top.gg']
        self.dblpy = topgg.DBLClient(self.bot, self.token, autopost=True, post_shard_count=True)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):  # when the bot joins a server
        await self.dblpy.post_guild_count()  # post server count

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):  # when the bot leaves a server
        await self.dblpy.post_guild_count()  # post server count


async def setup(bot):
    await bot.add_cog(TopGG(bot))
