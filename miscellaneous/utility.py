from discord.ext import commands
from discord.ext.commands import CheckFailure
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option

from utils.slash_utils import generate_choices_from_list

cog_list = {'hadith.hadith', 'hijri_calendar.hijri_calendar', 'quran.morphology', 'tafsir.tafsir',
            'tafsir.arabic_tafsir',
            'quran.mushaf', 'dua.dua', 'miscellaneous.help', 'miscellaneous.TopGG', 'miscellaneous.settings',
            'hadith.transmitter_biographies', 'quran.quran', 'salaah.salaah_times', 'miscellaneous.utility'}


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _reload(self, ctx, cog_name: str):
        if cog_name in self.bot.extensions.keys():
            await ctx.send(f":white_check_mark: **Reloaded the cog `{cog_name}`.**")
            await self.bot.reload_extension(cog_name)
        else:
            await ctx.send(f":warning: **Invalid extension**. Valid extensions: `{list(self.bot.extensions.keys())}`")

    @commands.is_owner()
    @commands.command(name='ireload')
    async def reload(self, ctx, cog_name: str):
        await self._reload(ctx, cog_name)

    @cog_ext.cog_slash(name="ireload", description="🔒 Owner only command. Reloads a cog",
                       options=[
                           create_option(
                               name="cog_name",
                               description="The name of the cog.",
                               option_type=3,
                               required=True,
                               choices=generate_choices_from_list(list(cog_list)))])
    async def slash_reload(self, ctx: SlashContext, cog_name: str):
        await ctx.defer()
        app = await self.bot.application_info()
        if ctx.author.id == app.owner.id:
            # hard code this because @commands.is_owner raises exceptions that can't be dealt with
            # probably can be in on_command_error though
            await self._reload(ctx, cog_name)
        else:
            await ctx.send("🔒 **You do not have permission to use this command**.")

    @reload.error
    async def reload_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.send("🔒 **You do not have permission to use this command**.")


def setup(bot):
    bot.add_cog(Utility(bot))
