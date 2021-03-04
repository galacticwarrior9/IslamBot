import re

import discord
from aiohttp import ClientSession
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from utils.utils import get_site_source

ICON = 'https://www.stickpng.com/assets/images/580b585b2edbce24c47b2abb.png'
INVALID_ARGUMENTS = "**Invalid arguments!**\n\n**Type**: `{0}morphology <surah>:<verse>:<word number>`" \
                    "\n\n**Example**: `{0}morphology 1:1:2`"


def has_syntax_image(surah):
    if 1 <= surah <= 8 or 59 <= surah <= 114:
        return True
    else:
        return False


def get_word_image(source):
    image_text = source.find("a", "tokenLink")
    for image in image_text:
        image = (image['src'])
        image_url = f"http://corpus.quran.com{image}"
        return image_url


def get_syntax_image(source, word):
    javascript = str(source.find("div", {"class": "graph"}))
    graph_id = (javascript.split("url('/"))[1].split("')")[0]
    image_url = f'http://corpus.quran.com/{graph_id}&token={word}'
    return image_url


def in_correct_format(ref):
    try:
        ref.split(':')
        return True
    except:
        return False


class QuranMorphology(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop = bot.loop)
        self.morphologyURL = 'http://corpus.quran.com/wordmorphology.jsp?location=({}:{}:{})'
        self.syntaxURL = 'http://corpus.quran.com/treebank.jsp?chapter={}&verse={}&token={}'

    async def _morphology(self, ctx, ref: str):
        if not in_correct_format(ref):
            await ctx.send(INVALID_ARGUMENTS.format(ctx.prefix))
            return

        try:
            surah, verse, word = ref.split(':')
        except:
            await ctx.send(INVALID_ARGUMENTS.format(ctx.prefix))
            return

        word_source = await get_site_source(self.morphologyURL.format(surah, verse, word))
        word_image = get_word_image(word_source)

        paragraph = word_source.find("p", "first")
        raw_morphology = str(word_source.find("td", "morphologyCell").text)
        morphology = re.sub(r'((?<=[a-z])[A-Z]|(?<!\A)[A-Z](?=[a-z]))', r' \n\1', raw_morphology)
        grammar = word_source.find("td", "grammarCell")

        syntax = False
        if has_syntax_image(int(surah)):
            syntax = True
            syntax_source = await get_site_source(self.syntaxURL.format(surah, verse, word))
            syntax_image = get_syntax_image(syntax_source, word)

        em = discord.Embed(colour=0x006400)
        em.set_author(name=f"Qurʾān {surah}:{verse}, Word {word}", icon_url=ICON)
        em.add_field(name='Morphology', value=f'From right to left: \n {morphology} ({grammar.text})', inline=False)
        em.add_field(name='Information', value=f'{paragraph.text}', inline=False)

        if syntax is True:
            em.set_image(url=syntax_image)
            em.set_thumbnail(url=word_image)
        else:
            em.set_image(url=word_image)
        await ctx.send(embed=em)

    @commands.command(name="morphology")
    async def morphology(self, ctx, ref: str):
        await self._morphology(ctx, ref)

    @morphology.error
    async def on_morphology_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_ARGUMENTS.format(ctx.prefix))

    @cog_ext.cog_slash(name="morphology", description="View the morphology of a Quranic word.",
                       options=[
                           create_option(
                               name="surah_num",
                               description="The surah number of the word.",
                               option_type=4,
                               required=True),
                           create_option(
                               name = "verse_num",
                               description = "The ayah number of the word.",
                               option_type=4,
                               required=True),
                           create_option(
                               name="word_num",
                               description="The word number of the word.",
                               option_type=4,
                               required=True)])
    async def slash_morphology(self, ctx: SlashContext, surah_num: int, verse_num: int, word_num: int):
        await ctx.respond()
        ref = f'{surah_num}:{verse_num}:{word_num}'
        await self._morphology(ctx, ref)


def setup(bot):
    bot.add_cog(QuranMorphology(bot))
