from discord.ext import commands
from utils import PrefixHandler, get_prefix
import discord


class Settings(commands.Cog):

    def __init__(self,bot):
        self.bot = bot



    @commands.group()
    async def prefix(self,ctx):
        if ctx.invoked_subcommand is None:
            prefix = PrefixHandler.get_prefix(ctx.guild.id)
            embed = discord.Embed(title="Setting a custom prefix",color=0x467f05)
            if not prefix:
                prefix = get_prefix()
                embed.description = f"`{prefix}set <prefix>`"
    @prefix.command()
    @commands.has_permissions(administrator=True)
    async def set(self,ctx,new_prefix):
        """
        This command is used to set a custom prefix for your server
        It takes one argument and that is the prefix that you want to set

        🔒 You will require **administrator** permissions to use this
        """

        PrefixHandler.add_prefix(author=ctx.author, guild_id=ctx.guild.id, prefix=new_prefix)
        await ctx.send(
            f"✅ | the prefix for **{ctx.guild.name}** has been to set to {new_prefix}")

    @prefix.command(name="remove", cooldown_after_parsing=True)
    @commands.has_permissions(administrator = True)
    async def remove_(self, ctx):
        """
        Used to remove a custom prefix of a server
        No args are required

        🔒 You will require **administrator** permissions to use this
        """

        if PrefixHandler.has_custom_prefix(ctx.guild.id):
            PrefixHandler.remove_prefix(guild_id=ctx.guild.id)
            await ctx.send(
                f"✅ | the prefix for **{ctx.guild.name}** has been removed")
        else:
            await ctx.send("Your server does not have a custom prefix to remove")



