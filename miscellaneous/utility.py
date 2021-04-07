from discord.ext import commands
from discord.ext.commands import CheckFailure


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.is_owner()
    @commands.command(name='ireload')
    async def reload(self, ctx, cog_name: str):
        if cog_name in self.bot.extensions.keys():
            await ctx.send(f":white_check_mark: **Reloaded the cog `{cog_name}`.**")
            await self.bot.reload_extension(cog_name)
        else:
            await ctx.send(f":warning: **Invalid extension**. Valid extensions: `{list(self.bot.extensions.keys())}`")

    @reload.error
    async def settranslation_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.send("🔒 **You do not have permission to use this command**.")


def setup(bot):
    bot.add_cog(Utility(bot))
