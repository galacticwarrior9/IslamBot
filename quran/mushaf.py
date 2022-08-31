import random

import discord
from aiohttp import ClientSession
from discord.ext import commands

from quran.quran_info import QuranReference, quranInfo
from utils.errors import respond_to_interaction_error
from utils.utils import convert_to_arabic_number

ICON = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

INVALID_INPUT = "**Type the command in this format**: `{0}mushaf <surah>:<ayah>`" \
                "\ne.g. `{0}mushaf 112:1` \n\nFor a color-coded mushaf, add `tajweed` to the end " \
                "of the command\ne.g. `{0}mushaf 112:1 tajweed`"

INVALID_SURAH_NAME = "**Invalid Surah name!** Try the number instead."


class Mushaf(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

    async def _mushaf(self, interaction: discord.Interaction, page: int, show_tajweed: bool = False) -> discord.Embed:
        formatted_page = str(page).zfill(3)
        if show_tajweed:
            url = f'https://www.searchtruth.org/quran/images1/{formatted_page}.jpg'
        else:
            url = f'https://www.searchtruth.org/quran/images2/large/page-{formatted_page}.jpeg'

        arabic_page_number = convert_to_arabic_number(str(page))
        em = discord.Embed(title=f'Page {page}'
                                 f'\n  الصفحة{arabic_page_number}', colour=0x006400)
        em.set_author(name='Mushaf / مصحف', icon_url=ICON)
        em.set_image(url=url)
        return em

    async def _mushaf_from_ref(self, interaction: discord.Interaction, ref, show_tajweed: bool = False,
                               reveal_order: bool = False) -> None:
        reference = QuranReference(ref=ref, reveal_order=reveal_order)
        async with self.session.get(f'https://api.alquran.cloud/ayah/{reference.surah}:{reference.ayat_list}') as resp:
            if resp.status != 200:
                return await interaction.followup.send(
                    "**Could not retrieve the mushaf image**. Please try again later.")
            data = await resp.json()
            page = int(data['data']['page'])
        em = await self._mushaf(interaction, page, show_tajweed)
        await interaction.followup.send(embed=em)

    group = discord.app_commands.Group(name="mushaf", description="View a specific page of verse on the mushaf.")

    @group.command(name="by_ayah", description="Displays an ayah on its page on the mushaf.")
    @discord.app_commands.describe(
        surah="The name or number of the ayah's surah, e.g. Al-Ikhlaas or 112",
        verse="The ayah within the surah to display, e.g. 225. Defaults to the first ayah.",
        show_tajweed="Should the mushaf highlight where tajweed rules apply?",
        reveal_order="If you specified a number for the surah, whether the number is the surah's revelation order."
    )
    async def by_ayah(self, interaction: discord.Interaction, surah: str, verse: int = 1,
                      show_tajweed: bool = False, reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        surah_number = QuranReference.parse_surah_number(surah)
        await self._mushaf_from_ref(interaction=interaction, ref=f'{surah_number}:{verse}', show_tajweed=show_tajweed,
                                    reveal_order=reveal_order)

    @group.command(name="by_page", description="Displays a page on the mushaf.")
    @discord.app_commands.describe(
        page="The page to display on the mushaf. Must be between 1 and 604.",
        show_tajweed="Should the mushaf highlight where tajweed rules apply?",
    )
    async def by_page(self, interaction: discord.Interaction, page: int, show_tajweed: bool = False):
        if page < 1 or page > 604:
            return await interaction.response.send_message("The page must be between 1 and 604.", ephemeral=True)

        await interaction.response.defer(thinking=True)
        em = await self._mushaf(interaction=interaction, page=page, show_tajweed=show_tajweed)
        await interaction.followup.send(embed=em)

    @discord.app_commands.command(name="rmushaf", description="Sends a random page from the mushaf.")
    @discord.app_commands.describe(show_tajweed="Should the mushaf highlight where tajweed rules apply?")
    async def rmushaf(self, interaction: discord.Interaction, show_tajweed: bool = False):
        await interaction.response.defer(thinking=True)
        page = random.randint(1, 604)
        em = await self._mushaf(interaction=interaction, page=page, show_tajweed=show_tajweed)
        await interaction.followup.send(embed=em)

    @by_ayah.error
    @by_page.error
    @rmushaf.error
    async def on_mushaf_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await respond_to_interaction_error(interaction, error)


async def setup(bot):
    await bot.add_cog(Mushaf(bot))
