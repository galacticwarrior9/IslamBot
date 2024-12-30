import random

import discord
from discord.ext import commands

from quran.quran_info import QuranReference, SurahNameTransformer
from utils.errors import respond_to_interaction_error
from utils.utils import convert_to_arabic_number

ICON_URL = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'


class Mushaf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_mushaf_image(page: int, show_tajweed: bool = False) -> discord.Embed:
        formatted_page = str(page).zfill(3)
        if show_tajweed:
            url = f'https://www.searchtruth.org/quran/images1/{formatted_page}.jpg'
        else:
            url = f'https://www.searchtruth.org/quran/images2/large/page-{formatted_page}.jpeg'

        arabic_page_number = convert_to_arabic_number(str(page))
        em = discord.Embed(title=f'Page {page}'
                                 f'\n  الصفحة{arabic_page_number}', colour=0x006400)
        em.set_author(name='Mushaf / مصحف', icon_url=ICON_URL)
        em.set_image(url=url)
        return em

    async def _mushaf_from_ref(self, interaction: discord.Interaction, ref, show_tajweed: bool = False,
                               reveal_order: bool = False) -> discord.Embed:
        reference = QuranReference(ref=ref, reveal_order=reveal_order)
        async with self.bot.session.get(f'https://api.alquran.cloud/ayah/{reference.surah}:{reference.ayat_list}') as resp:
            if resp.status != 200:
                return await interaction.followup.send(
                    "**Could not retrieve the mushaf image**. Please try again later.")
            data = await resp.json()
            page = int(data['data']['page'])

        em = self.get_mushaf_image(page, show_tajweed)
        mushaf_ui_view = MushafNavigator(page, show_tajweed, interaction)
        await interaction.followup.send(embed=em, view=mushaf_ui_view)

    group = discord.app_commands.Group(name="mushaf", description="View a specific page of verse on the mushaf.")

    @group.command(name="by_ayah", description="Displays an ayah on its page on the mushaf.")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @discord.app_commands.describe(
        surah="The name or number of the ayah's surah, e.g. Al-Ikhlaas or 112",
        verse="The ayah within the surah to display, e.g. 225. Defaults to the first ayah.",
        show_tajweed="Should the mushaf highlight where tajweed rules apply?",
        reveal_order="If you specified a number for the surah, whether the number is the surah's revelation order."
    )
    async def by_ayah(self, interaction: discord.Interaction, surah: discord.app_commands.Transform[int, SurahNameTransformer], verse: int = 1,
                      show_tajweed: bool = False, reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        await self._mushaf_from_ref(interaction=interaction, ref=f'{surah}:{verse}', show_tajweed=show_tajweed,
                                    reveal_order=reveal_order)

    @group.command(name="by_page", description="Displays a page on the mushaf.")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @discord.app_commands.describe(
        page="The page to display on the mushaf. Must be between 1 and 604.",
        show_tajweed="Should the mushaf highlight where tajweed rules apply?",
    )
    async def by_page(self, interaction: discord.Interaction, page: discord.app_commands.Range[int, 1, 604], show_tajweed: bool = False):
        await interaction.response.defer(thinking=True)
        em = self.get_mushaf_image(page=page, show_tajweed=show_tajweed)
        mushaf_ui_view = MushafNavigator(page, show_tajweed, interaction)
        await interaction.followup.send(embed=em, view=mushaf_ui_view)

    @discord.app_commands.command(name="rmushaf", description="Sends a random page from the mushaf.")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @discord.app_commands.describe(show_tajweed="Should the mushaf highlight where tajweed rules apply?")
    async def rmushaf(self, interaction: discord.Interaction, show_tajweed: bool = False):
        await interaction.response.defer(thinking=True)
        page = random.randint(1, 604)
        em = self.get_mushaf_image(page=page, show_tajweed=show_tajweed)
        mushaf_ui_view = MushafNavigator(page, show_tajweed, interaction)
        await interaction.followup.send(embed=em, view=mushaf_ui_view)

    @by_ayah.error
    @by_page.error
    @rmushaf.error
    async def on_mushaf_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await respond_to_interaction_error(interaction, error)


class MushafNavigator(discord.ui.View):
    def __init__(self, page: int, show_tajweed: bool, interaction: discord.Interaction):
        super().__init__()
        self.page = page
        self.show_tajweed = show_tajweed
        self.original_interaction = interaction

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.original_interaction.edit_original_response(view=self, content=":warning: This message has timed out.")

    @discord.ui.button(label='Previous Page', style=discord.ButtonStyle.grey, emoji='⬅')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.original_interaction.user.id:
            return await interaction.response.send_message(content="Only the sender of the command can change the page.", ephemeral=True)

        if self.page > 1:
            self.page -= 1
        else:
            self.page = 604
        em = Mushaf.get_mushaf_image(self.page, self.show_tajweed)
        await interaction.response.edit_message(embed=em)

    @discord.ui.button(label='Next Page', style=discord.ButtonStyle.green, emoji='➡')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.original_interaction.user.id:
            return await interaction.response.send_message(content="Only the sender of the command can change the page.", ephemeral=True)

        if self.page < 604:
            self.page += 1
        else:
            self.page = 1
        em = Mushaf.get_mushaf_image(self.page, self.show_tajweed)
        await interaction.response.edit_message(embed=em)


async def setup(bot):
    await bot.add_cog(Mushaf(bot))
