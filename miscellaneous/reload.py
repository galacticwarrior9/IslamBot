import discord
from discord.app_commands import TransformerError
from discord.ext import commands
from fuzzywuzzy import process, fuzz


class GuildTransformer(discord.app_commands.Transformer):
    async def transform(self, interaction: discord.Interaction, guild_id: str) -> discord.Object:
        return discord.Object(int(guild_id))


class Reload(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _reload(self, interaction: discord.Interaction, cog_name: str):
        if cog_name in self.bot.extensions.keys():
            await interaction.response.send_message(f":white_check_mark: **Reloaded the cog `{cog_name}`.**", ephemeral=True)
            await self.bot.reload_extension(cog_name)
        else:
            await interaction.response.send_message(f":warning: **Invalid extension**. Valid extensions: `{list(self.bot.extensions.keys())}`", ephemeral=True)

    group = discord.app_commands.Group(name="reload", description="🔒 Bot owner only commands.")

    @group.command(name="extension", description="🔒 Bot owner only command. Reloads an extension.")
    @discord.app_commands.describe(extension="The extension to reload.")
    async def reload_extension(self, interaction: discord.Interaction, extension: str):
        app = await self.bot.application_info()
        if interaction.user.id == app.owner.id:
            await self._reload(interaction, extension)
        else:
            await interaction.response.send_message("🔒 **You do not have permission to use this command**.", ephemeral=True)

    @reload_extension.autocomplete('extension')
    async def autocomplete_extensions(self, interaction: discord.Interaction, current: str):
        return [
            discord.app_commands.Choice(name=match, value=match)
            for match in self.bot.extensions.keys() if current.lower() in match.lower()
        ]

    @group.command(name="commands", description="🔒 Bot owner only command. Syncs commands with Discord.")
    @discord.app_commands.describe(guild_id="The guild ID to sync commands for. Leave blank to sync globally.")
    async def reload_commands(self, interaction: discord.Interaction,
                              guild_id: discord.app_commands.Transform[discord.Object, GuildTransformer] = None):
        app = await self.bot.application_info()
        if interaction.user.id == app.owner.id:
            await self.bot.tree.sync(guild=guild_id)
            await interaction.response.send_message(":white_check_mark: Syncing commands.", ephemeral=True)
        else:
            await interaction.response.send_message("🔒 **You do not have permission to use this command**.", ephemeral=True)

    @reload_commands.error
    async def on_transform_failure(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, TransformerError):
            await interaction.response.send_message("Failed to parse guild ID.", ephemeral=True)
        else:
            print(error)


async def setup(bot):
    await bot.add_cog(Reload(bot))
