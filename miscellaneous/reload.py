import discord
from discord.ext import commands
from fuzzywuzzy import process, fuzz

from utils.slash_utils import generate_choices_from_list


class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _reload(self, interaction: discord.Interaction, cog_name: str):
        if cog_name in self.bot.extensions.keys():
            await interaction.response.send_message(f":white_check_mark: **Reloaded the cog `{cog_name}`.**", ephemeral=True)
            await self.bot.reload_extension(cog_name)
        else:
            await interaction.response.send_message(f":warning: **Invalid extension**. Valid extensions: `{list(self.bot.extensions.keys())}`", ephemeral=True)

    @discord.app_commands.command(name="reload", description="🔒 Bot owner only command. Reloads an extension.")
    @discord.app_commands.describe(extension="The extension to reload.")
    async def reload(self, interaction: discord.Interaction, extension: str):
        app = await self.bot.application_info()
        if interaction.user.id == app.owner.id:
            await self._reload(interaction, extension)
        else:
            await interaction.response.send_message("🔒 **You do not have permission to use this command**.", ephemeral=True)

    @reload.autocomplete('extension')
    async def autocomplete_extensions(self, interaction: discord.Interaction, current: str):
        closest_matches = [match[0] for match in process.extract(current, self.bot.extensions.keys(), scorer=fuzz.token_sort_ratio, limit=5)]
        choices = [discord.app_commands.Choice(name=match, value=match) for match in closest_matches]
        return choices


async def setup(bot):
    await bot.add_cog(Reload(bot), guild=discord.Object(308241121165967362))
