from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from aiohttp import ClientSession
from utils import convert_to_arabic_number
import discord

ICON = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

INVALID_INPUT = "**Type the command in this format**: `{0}mushaf <surah>:<ayah>`" \
        "\ne.g. `{0}mushaf 112:1` \n\nFor a color-coded mushaf, added 'tajweed' to the end " \
        "of the command\ne.g. `{0}mushaf 112:1 tajweed`"

INVALID_VERSE = '**Verse not found**. Please check the verse exists, or try again later.'


class Mushaf(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

    @commands.command(name="mushaf")
    async def mushaf(self, ctx, ref: str, tajweed : str = 'none'):

        try:
            surah, ayah = ref.split(':')
        except ValueError:
            return await ctx.send(INVALID_INPUT.format(ctx.prefix))

        async with self.session.get(f'https://api.alquran.cloud/ayah/{surah}:{ayah}') as resp:
            if resp.status != 200:
                return await ctx.send(INVALID_VERSE)
            data = await resp.json()
            page = data['data']['page']

        formatted_page = str(page).zfill(3)

        if tajweed == 'none':
            url = f'https://www.searchtruth.org/quran/images2/large/page-{formatted_page}.jpeg'
        else:
            url = f'https://www.searchtruth.org/quran/images1/{formatted_page}.jpg'

        arabic_page_number = convert_to_arabic_number(str(page))
        em = discord.Embed(title=f'Page {page}'
                                 f'\n  الصفحة{arabic_page_number}', colour=0x006400)
        em.set_author(name=f'Mushaf / مصحف', icon_url=ICON)
        em.set_image(url=url)
        await ctx.send(embed=em)

    @mushaf.error
    async def on_mushaf_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(ctx.prefix))


def setup(bot):
    bot.add_cog(Mushaf(bot))
