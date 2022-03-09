import discord
from aiohttp import ClientSession
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from quran.quran_info import QuranReference
from utils.utils import convert_to_arabic_number, get_site_json

ICON = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

INVALID_INPUT = "**Type the command in this format**: `{0}mushaf <surah>:<ayah>`" \
                "\ne.g. `{0}mushaf 112:1` \n\nFor a color-coded mushaf, add `tajweed` to the end " \
                "of the command\ne.g. `{0}mushaf 112:1 tajweed`"

INVALID_VERSE = '**Verse not found**. Please check the verse exists, or try again later.'


class Mushaf(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

    async def _mushaf(self, ctx, ref, show_tajweed: bool, reveal_order: bool = False):
        reference = QuranReference(ref=ref, reveal_order=reveal_order)
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
        em.set_author(name='Mushaf / مصحف', icon_url=ICON)
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

    @commands.command(name="rmushaf")
    async def rmushaf(self, ctx, tajweed: str = None):
        await ctx.channel.trigger_typing()
        json = await get_site_json("https://api.quran.com/api/v4/verses/random?language=en&words=false")
        ref = json["verse"]["verse_key"]
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
                               name="surah_num",
                               description="The surah number to show on the mushaf, e.g. 112.",
                               option_type=4,
                               required=True),
                           create_option(
                               name="verse_num",
                               description="The verse number to show on the mushaf, e.g. 255.",
                               option_type=4,
                               required=True),
                           create_option(
                               name="show_tajweed",
                               description="Should the mushaf highlight where tajweed rules apply?",
                               option_type=5,
                               required=False),
                           create_option(
                               name="reveal_order",
                               description="Is the surah referenced the revelation order number?",
                               option_type=5,
                               required=False)])
    async def slash_mushaf(self, ctx: SlashContext, surah_num: int, verse_num: int, show_tajweed: bool = False,
                           reveal_order: bool = False):
        await ctx.defer()
        await self._mushaf(ctx=ctx, ref=f'{surah_num}:{verse_num}', show_tajweed=show_tajweed,
                           reveal_order=reveal_order)

    @cog_ext.cog_slash(name="rmushaf", description="View a random page of the mushaf.",
                       options=[
                           create_option(
                               name="show_tajweed",
                               description="Should the mushaf highlight where tajweed rules apply?",
                               option_type=5,
                               required=False)]
        )
    async def slash_rmushaf(self, ctx: SlashContext, show_tajweed: bool = False):
        await ctx.defer()
        json = await get_site_json("https://api.quran.com/api/v4/verses/random?language=en&words=false")
        ref = json["verse"]["verse_key"]
        await self._mushaf(ctx=ctx, ref=ref, show_tajweed=show_tajweed)


def setup(bot):
    bot.add_cog(Mushaf(bot))
