import random

import discord
from aiohttp import ClientSession
from discord.ext import commands

from quran.quran_info import QuranReference, quranInfo, InvalidSurahName
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

    async def _mushaf(self, interaction: discord.Interaction, ref, show_tajweed: bool, reveal_order: bool = False):
        reference = QuranReference(ref=ref, reveal_order=reveal_order)
        async with self.session.get(f'https://api.alquran.cloud/ayah/{reference.surah}:{reference.ayat_list}') as resp:
            if resp.status != 200:
                return await interaction.followup.send("**Could not retrieve the mushaf image**. Please try again later.")
            data = await resp.json()
            page = data['data']['page']

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

        await interaction.followup.send(embed=em)

    @discord.app_commands.command(name="mushaf", description="Displays an ayah on its page on the mushaf.")
    @discord.app_commands.describe(
        surah="The name or number of the surah, e.g. Al-Ikhlaas or 112",
        verse="The verse within the surah to display, e.g. 225.",
        show_tajweed="Should the mushaf highlight where tajweed rules apply?",
        reveal_order="If you specified a number for the surah, whether the number is the surah's revelation order."
    )
    async def mushaf(self, interaction: discord.Interaction, surah: str, verse: int,
                     show_tajweed: bool = False, reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        surah_number = QuranReference.parse_surah_number(surah)
        await self._mushaf(interaction=interaction, ref=f'{surah_number}:{verse}', show_tajweed=show_tajweed,
                           reveal_order=reveal_order)

    @discord.app_commands.command(name="rmushaf", description="Sends a random page from the mushaf.")
    @discord.app_commands.describe(show_tajweed="Should the mushaf highlight where tajweed rules apply?")
    async def rmushaf(self, interaction: discord.Interaction, show_tajweed: bool = False):
        await interaction.response.defer(thinking=True)
        surah = random.randint(1, 114)
        verse = random.randint(1, quranInfo['surah'][surah][1])
        await self._mushaf(interaction=interaction, ref=f'{surah}:{verse}', show_tajweed=show_tajweed)

    @mushaf.error
    @rmushaf.error
    async def on_mushaf_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await respond_to_interaction_error(interaction, error)


async def setup(bot):
    await bot.add_cog(Mushaf(bot), guild=discord.Object(308241121165967362))
