from discord.ext import commands


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ireload')
    async def reload(self, ctx, cog_name: str):
        if cog_name in self.bot.extensions.keys():
            await ctx.send(f":white_check_mark: **Reloaded the cog `{cog_name}`.**")
            await self.bot.reload_extension(cog_name)
        else:
            await ctx.send(f":warning: **Invalid extension**. Valid extensions: `{list(self.bot.extensions.keys())}`")


def setup(bot):
    bot.add_cog(Utility(bot))
