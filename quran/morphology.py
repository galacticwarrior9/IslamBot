import re

import discord
from aiohttp import ClientSession
from discord.ext import commands

from quran.quran_info import QuranReference
from utils.errors import respond_to_interaction_error
from utils.utils import get_site_source

ICON = 'https://www.stickpng.com/assets/images/580b585b2edbce24c47b2abb.png'
INVALID_ARGUMENTS = "**Invalid arguments!**\n\n**Type**: `{0}morphology <surah>:<verse>:<word number>`" \
                    "\n\n**Example**: `{0}morphology 1:1:2`"
INVALID_SURAH_NAME = "**Invalid Surah name!** Try the number instead."


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


class QuranMorphology(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)
        self.morphologyURL = 'http://corpus.quran.com/wordmorphology.jsp?location=({}:{}:{})'
        self.syntaxURL = 'http://corpus.quran.com/treebank.jsp?chapter={}&verse={}&token={}'

    async def _morphology(self, interaction: discord.Interaction, ref: str):
        surah, verse, word = ref.split(':')

        # Check if the surah and ayah are valid
        QuranReference(f"{surah}:{verse}")

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
        await interaction.followup.send(embed=em)

    @discord.app_commands.command(name="morphology", description="View the morphology of a word in the Qur'an.")
    @discord.app_commands.describe(
        surah="The name/number of the word's surah, e.g. Al-Ikhlas or 112",
        verse="The verse in the surah that the word appears in, e.g. 100 for the 100th verse",
        word_number="The order in which this word appears in the verse, e.g. 2 for the second word."
    )
    async def morphology(self, interaction: discord.Interaction, surah: str, verse: int, word_number: int):
        await interaction.response.defer(thinking=True)
        surah_number = QuranReference.parse_surah_number(surah)
        ref = f'{surah_number}:{verse}:{word_number}'
        await self._morphology(interaction, ref)

    @morphology.error
    async def on_morphology_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await respond_to_interaction_error(interaction, error)


async def setup(bot):
    await bot.add_cog(QuranMorphology(bot))
