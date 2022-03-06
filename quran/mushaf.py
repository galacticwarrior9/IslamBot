import discord
from aiohttp import ClientSession
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from quran.quran_info import QuranReference
from utils.utils import convert_to_arabic_number

ICON = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

INVALID_INPUT = "**Type the command in this format**: `{0}mushaf <surah>:<ayah>`" \
                "\ne.g. `{0}mushaf 112:1` \n\nFor a color-coded mushaf, add `tajweed` to the end " \
                "of the command\ne.g. `{0}mushaf 112:1 tajweed`"

INVALID_VERSE = '**Verse not found**. Please check the verse exists, or try again later.'


class Mushaf(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

    async def _mushaf(self, ctx, ref, show_tajweed):
        reference = QuranReference(ref)
        async with self.session.get(f'https://api.alquran.cloud/ayah/{reference.surah}:{reference.ayat_list}') as resp:
            if resp.status != 200:
                return await ctx.send(INVALID_VERSE)
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
        em.set_author(name=f'Mushaf / مصحف', icon_url=ICON)
        em.set_image(url=url)

        await ctx.send(embed=em)

    @commands.command(name="mushaf")
    async def mushaf(self, ctx, ref: str, tajweed: str = None):
        await ctx.channel.trigger_typing()
        if tajweed is None:
            await self._mushaf(ctx, ref, False)
        elif tajweed.lower() == 'tajweed':
            await self._mushaf(ctx, ref, True)
        else:
            raise MissingRequiredArgument

    @mushaf.error
    async def on_mushaf_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(ctx.prefix))

    @cog_ext.cog_slash(name="mushaf", description="View an ayah on the mushaf.",
                       options=[
                           create_option(
                               name="reference",
                               description="The verse show on the mushaf, e.g. 1:4 or 2:255.",
                               option_type=3,
                               required=True),
                           create_option(
                               name="show_tajweed",
                               description="Should the mushaf highlight where tajweed rules apply?",
                               option_type=5,
                               required=False
                           )])
    async def slash_mushaf(self, ctx: SlashContext, reference: str, show_tajweed: bool = False):
        await ctx.defer()
        await self._mushaf(ctx, reference, show_tajweed)


def setup(bot):
    bot.add_cog(Mushaf(bot))
