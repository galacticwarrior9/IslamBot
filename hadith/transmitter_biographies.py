import asyncio
import textwrap

import discord
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord_slash import cog_ext, SlashContext, ButtonStyle
from discord_slash.utils import manage_components
from discord_slash.utils.manage_commands import create_option

from utils.utils import get_site_source

INVALID_PERSON = "**Error**: Could not find person."
INVALID_ARGUMENTS = "**Error**: Please specify a name (in Arabic)."


class Biographies(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.url = 'http://hadithtransmitters.hawramani.com/?s={}&cat=5563'

    async def _biography(self, ctx, name):
        soup = await get_site_source(self.url.format(name))

        try:
            permalink = soup.find('a', href=True, class_='sectionpermaanchor')['href']
        except TypeError:
            return await ctx.send("**Error**: Person not found.")

        soup = await get_site_source(permalink)

        text = soup.find('div', {"class": "definition"}).text
        title = soup.find('title').text

        pages = textwrap.wrap(text, 2040, break_long_words=False)

        num_pages = len(pages)

        em = discord.Embed(title='الذهبي - سير أعلام النبلاء', color=0x4aa807, description=pages[0])
        em.set_author(name=title)

        if num_pages == 1:
            return await ctx.send(embed=em)

        if num_pages > 1:
            page = 1
            em.set_footer(text=f'Page {page}/{num_pages}')

        # If there are multiple pages, construct buttons for their navigation.
        buttons = [
            manage_components.create_button(style=ButtonStyle.green, label="الصفحة التالية", emoji="⬅",
                                            custom_id="biography_next_page"),
            manage_components.create_button(style=ButtonStyle.red, label="الصفحة السابقة", emoji="➡",
                                            custom_id="biography_previous_page"),
        ]
        action_row = manage_components.create_actionrow(*buttons)
        await ctx.send(embed=em, components=[action_row])
        while True:
            try:
                button_ctx = await manage_components.wait_for_component(self.bot, components=action_row,
                                                                        timeout=600)
                if button_ctx.custom_id == 'biography_previous_page':
                    if page > 1:
                        page -= 1
                    else:
                        page = num_pages
                    em.description = pages[page - 1]
                    em.set_footer(text=f'Page {page}/{num_pages}')
                    await button_ctx.edit_origin(embed=em)
                elif button_ctx.custom_id == 'biography_next_page':
                    if page < num_pages:
                        page += 1
                    else:
                        page = 1
                    em.description = pages[page - 1]
                    em.set_footer(text=f'Page {page}/{num_pages}')
                    await button_ctx.edit_origin(embed=em)

            except asyncio.TimeoutError:
                break

    @commands.command(name="biography")
    async def biography(self, ctx, *, name):
        async with ctx.channel.typing():
            await self._biography(ctx, name)

    @biography.error
    async def biography_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("**Error**: Please type a valid name. For example: ")

    @cog_ext.cog_slash(name="biography", description="View the biography of a hadith transmitter or early Muslim.",
                       options=[
                           create_option(
                               name="name",
                               description="The *Arabic* name of the person to fetch information for, e.g. {}".format("عبد الله بن عباس "),
                               option_type=3,
                               required=True)])
    async def slash_biography(self, ctx: SlashContext, name: str):
        await ctx.defer()
        await self._biography(ctx, name)


def setup(bot):
    bot.add_cog(Biographies(bot))
