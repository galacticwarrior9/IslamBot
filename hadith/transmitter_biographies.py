import textwrap

import discord
from discord.ext import commands

from utils.errors import respond_to_interaction_error
from utils.utils import get_site_source

INVALID_PERSON = "**Error**: Could not find person."
INVALID_ARGUMENTS = "**Error**: Please specify a name (in Arabic)."
BIOGRAPHY_URL = 'http://hadithtransmitters.hawramani.com/?s={}&cat=5563'


class Biographies(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _biography(self, interaction: discord.Interaction, name: str):
        soup = await get_site_source(BIOGRAPHY_URL.format(name))

        try:
            permalink = soup.find('a', href=True, class_='sectionpermaanchor')['href']
        except TypeError:
            return await interaction.followup.send("**Error**: Person not found.")

        soup = await get_site_source(permalink)

        text = soup.find('div', {"class": "definition"}).text
        title = soup.find('title').text

        pages = textwrap.wrap(text, 2040, break_long_words=False)

        num_pages = len(pages)

        em = discord.Embed(title='الذهبي - سير أعلام النبلاء', color=0x4aa807, description=pages[0])
        em.set_author(name=title)

        if num_pages == 1:
            return await interaction.followup.send(embed=em)
        else:
            # If there are multiple pages, add buttons
            page = 1
            em.set_footer(text=f'Page {page}/{num_pages}')

            biography_ui_view = BiographyNavigator(page, pages, em, interaction)
            await interaction.followup.send(embed=em, view=biography_ui_view)

    @discord.app_commands.command(name="biography", description="View the biography of a hadith transmitter or early Muslim.")
    @discord.app_commands.describe(name="The Arabic name of the person, e.g. {}".format("عبد الله بن عباس"))
    async def biography(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer(thinking=True)
        await self._biography(interaction, name)

    @biography.error
    async def biography_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await respond_to_interaction_error(interaction, error)


class BiographyNavigator(discord.ui.View):
    def __init__(self, page: int, pages: list[str], embed: discord.Embed, interaction: discord.Interaction):
        super().__init__(timeout=600)
        self.page = page
        self.pages = pages
        self.em = embed
        self.num_pages = len(pages)
        self.original_interaction = interaction

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.original_interaction.edit_original_response(view=self, content=":warning: This message has timed out.")

    @discord.ui.button(label='Previous Page', style=discord.ButtonStyle.red, emoji='⬅')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page > 1:
            self.page -= 1
        else:
            self.page = self.num_pages

        self.em.description = self.pages[self.page - 1]
        self.em.set_footer(text=f'Page {self.page}/{self.num_pages}')
        await interaction.response.edit_message(embed=self.em)

    @discord.ui.button(label='Next Page', style=discord.ButtonStyle.green, emoji='➡')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.page < self.num_pages:
            self.page += 1
        else:
            self.page = 1
        self.em.description = self.pages[self.page - 1]
        self.em.set_footer(text=f'Page {self.page}/{self.num_pages}')
        await interaction.response.edit_message(embed=self.em)


async def setup(bot):
    await bot.add_cog(Biographies(bot))
