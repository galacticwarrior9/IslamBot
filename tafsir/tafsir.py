import asyncio
import re
import textwrap

import discord
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord_slash import cog_ext, SlashContext, ButtonStyle
from discord_slash.utils import manage_components
from discord_slash.utils.manage_commands import create_option

from quran.quran_info import Surah, InvalidSurah, QuranReference
from utils.slash_utils import generate_choices_from_dict
from utils.utils import get_site_source, get_site_json

icon = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

name_mappings = {
    'maarifulquran': 'Maarif-ul-Quran',
    'ibnkathir': 'Tafsīr Ibn Kathīr',
    'jalalayn': 'Tafsīr al-Jalālayn',
    'tustari': 'Tafsīr al-Tustarī',
    'kashani': 'Tafsīr ʿAbd al-Razzāq al-Kāshānī',
    'qushayri': 'Laṭāʾif al-Ishārāt',
    'wahidi': 'Asbāb al-Nuzūl',
    'kashf': 'Kashf al-Asrār',
    'saddi': "Tafsīr al-Sa'di (Russian)",
    'zakaria': 'Tafsir Abu Bakr Zakaria (Bengali)',
    "israr": "تفسیر بیان القرآن",
    "ibnkathir.ur": "تفسیر ابنِ کثیر",
    'ibnkathir.bn': 'তাফসীর ইবনে কাছী',
    'mukhtasar': 'Al-Mukhtasar',
    'ahsanul': 'Tafsir Ahsanul Bayaan'
}

name_alias = {
    "saadi": "saddi",  # saadi is more correct ( السعدي )
    "jalalain": "jalalayn",  # jalalaIn is AlTafsir's spelling
    "asbabalnuzul": "wahidi",  # better known name
    "asbab": "wahidi",  # better known name, shortened
}

altafsir_sources = {
    'tustari': 93,
    'kashani': 107,
    'qushayri': 108,
    'wahidi': 86,
    'kashf': 109,
}

quranCom_sources = {
    'ibnkathir': 169,
    'ibnkathir.ur': 160,
    'ibnkathir.bn': 164,
    'maarifulquran': 168,
    'saddi': 170,
    'mukhtasar': 171,
    'ahsanul': 165,
    'zakaria': 166,
    'israr': 159,
}

INVALID_ARGUMENTS = '**Invalid arguments.** Type the command in this format: `{0}tafsir <surah>:<ayah> <tafsir name>`.' \
                    '\n\n**Example**: `{0}tafsir 1:1 ibnkathir`'

INVALID_TAFSIR = "**Couldn't find tafsir!** " \
                 "\n\n**List of tafasir**: <https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List>."

INVALID_SURAH = "**There only 114 surahs.** Please choose a surah between 1 and 114."

INVALID_AYAH = "**There are only {0} verses in this surah**."

NO_TEXT = "**Could not find tafsir for this verse.** Please try another tafsir." \
          "\n\n**List of tafasir**: <https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List>."

BAD_ALIAS = "This is normally unreachable error! Developer, please check aliases for tafsir!"

altafsir_url = 'https://www.altafsir.com/Tafasir.asp?tMadhNo=0&tTafsirNo={}&tSoraNo={}&tAyahNo={}&tDisplay=yes&Page={}&Size=1&LanguageId=2'

quranCom_url = 'https://api.quran.com/api/v4/quran/tafsirs/{}?verse_key={}'

jalalayn_url = 'https://raw.githubusercontent.com/galacticwarrior9/islambot/master/tafsir/tafsir_jalalayn.txt'


class InvalidReference(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InvalidAyah(commands.CommandError):
    def __init__(self, num_verses, *args, **kwargs):
        self.num_verses = num_verses
        super().__init__(*args, **kwargs)


class InvalidTafsir(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class NoText(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class BadAlias(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class TafsirSpecifics:
    def __init__(self, tafsir, ref, page):
        self.pages = None
        self.num_pages = None
        self.url = None
        self.tafsir_author = None
        self.text = None
        self.embed = None
        self.page = page

        self.query_tafsir(tafsir)

        self.ref = QuranReference(ref)
        self.make_url()

    # this is the function to implement better tafsir retrieval
    def query_tafsir(self, t):
        try:
            assert (len(t) > 0)
        except:
            raise InvalidTafsir

        t = t.lower()

        # 95% of tafsirs should be found here
        if t in name_mappings.keys():
            self.tafsir = t
            self.tafsir_name = name_mappings[t]
            return

            # if not, try aliases
        if t in name_alias.keys():
            buf = name_alias[t]
            # I assume aliases are set up correctly, if not raise normally unreachable error
            if buf not in name_mappings.keys():
                raise BadAlias

            self.tafsir = buf
            self.tafsir_name = name_mappings[buf]
            return

        # IF all failed, raise an error
        raise InvalidTafsir

    def make_url(self):
        if self.tafsir in altafsir_sources.keys():
            tafsir_id = altafsir_sources[self.tafsir]
            self.url = altafsir_url.format(tafsir_id, self.ref.surah, self.ref.ayat_list, 1)
        elif self.tafsir == 'jalalayn':
            self.url = jalalayn_url
        elif self.tafsir in quranCom_sources.keys():
            tafsir_id = quranCom_sources[self.tafsir]
            self.url = quranCom_url.format(tafsir_id, f'{self.ref.surah}:{self.ref.ayat_list}')

    async def get_text(self):
        if self.tafsir in altafsir_sources.keys():
            source = await get_site_source(self.url)
            tags = []
            for tag in source.findAll('font', attrs={'class': 'TextResultEnglish'}):
                tags.append(f' {tag.getText()}')
            for tag in source.findAll('font', attrs={'class': 'TextArabic'}):
                tags.append(tag.getText())
            self.text = ''.join(tags)

        elif self.tafsir in quranCom_sources.keys():
            source = await get_site_json(self.url)
            self.text = source['tafsirs'][0]['text']
            self.tafsir_author = source['meta']['author_name']

            # Replace HTML tags
            cleanr = re.compile('<(.*?)>')
            self.text = re.sub(cleanr, ' ', self.text)
            self.text = self.text.replace('`', "ʿ")

        elif self.tafsir == 'jalalayn':
            source = await get_site_source(self.url)
            source = source.decode('utf-8')
            self.tafsir_author = 'Jalal ad-Din al-Maḥalli and Jalal ad-Din as-Suyuti'

            try:
                char1 = f'[{self.ref.surah}:{self.ref.ayat_list}]'
                next_ayah = self.ref.ayat_list + 1
                char2 = f'[{self.ref.surah}:{next_ayah}]'

                text = source[(source.index(char1) + len(char1)):source.index(char2)]
                self.text = f"{text}".replace('`', '\\`').replace('(s)', '(ﷺ)').rstrip()

            except:
                char1 = f'[{self.ref.surah}:{self.ref.surah}]'
                self.ref.surah += 1
                char2 = f'[{self.ref.surah}:1]'

                text = source[(source.index(char1) + len(char1)):source.index(char2)]
                self.text = u"{}".format(text).replace('`', '\\`').rstrip()

        self.pages = textwrap.wrap(self.text, 2000, break_long_words=False)
        self.num_pages = len(self.pages)

    async def make_embed(self):
        em = discord.Embed(colour=0x467f05, description=self.pages[self.page - 1])
        em.title = f'Tafsir of Surah {Surah(self.ref.surah).name}, Verse {self.ref.ayat_list}'
        em.set_author(name=self.tafsir_name, icon_url=icon)

        if self.num_pages > 1:
            if self.tafsir_author is None:
                em.set_footer(text=f'Page: {self.page}/{self.num_pages}')
            else:
                em.set_footer(text=f'Author: {self.tafsir_author}\nPage: {self.page}/{self.num_pages}')
        elif self.tafsir_author is not None:
            em.set_footer(text=f'Author: {self.tafsir_author}')

        self.embed = em


class TafsirEnglish(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def send_embed(self, ctx, spec):
        if spec.num_pages == 1:
            return await ctx.send(embed=spec.embed)

        # If there are multiple pages, construct buttons for their navigation.
        buttons = [
            manage_components.create_button(style=ButtonStyle.grey, label="Previous Page", emoji="⬅",
                                            custom_id="tafsir_previous_page"),
            manage_components.create_button(style=ButtonStyle.green, label="Next Page", emoji="➡",
                                            custom_id="tafsir_next_page")
        ]
        action_row = manage_components.create_actionrow(*buttons)
        await ctx.send(embed=spec.embed, components=[action_row])

        while True:
            try:
                button_ctx = await manage_components.wait_for_component(self.bot, components=action_row, timeout=600)
                if button_ctx.custom_id == 'tafsir_previous_page':
                    if spec.page > 1:
                        spec.page -= 1
                    else:
                        spec.page = spec.num_pages
                    await spec.make_embed()
                    await button_ctx.edit_origin(embed=spec.embed)
                elif button_ctx.custom_id == 'tafsir_next_page':
                    if spec.page < spec.num_pages:
                        spec.page += 1
                    else:
                        spec.page = 1
                    await spec.make_embed()
                    await button_ctx.edit_origin(embed=spec.embed)

            except asyncio.TimeoutError:
                break

    async def process_request(self, ref: str, tafsir: str, page: int):
        spec = TafsirSpecifics(tafsir, ref, page)
        try:
            await spec.get_text()
        except IndexError:
            # If no entry was found in the default tafsir (Maarif-ul-Quran), fall back to Tafsir al-Jalalayn.
            if tafsir == 'maarifulquran':
                return await self.process_request(ref, 'jalalayn', page)
            else:
                raise NoText

        if len(spec.text) == 0:
            raise NoText

        await spec.make_embed()
        return spec

    @commands.command(name='tafsir')
    async def tafsir(self, ctx, ref: str, tafsir: str = "maarifulquran", page: int = 1):
        spec = await self.process_request(ref, tafsir, page)
        await self.send_embed(ctx, spec)

    @cog_ext.cog_slash(name="tafsir", description="Get the tafsir of a verse.",
                       options=[
                           create_option(
                               name="reference",
                               description="The verse to get the tafsir of, e.g. 1:4 or 2:255.",
                               option_type=3,
                               required=True),
                           create_option(
                               name="tafsir",
                               description="The name of the tafsir.",
                               option_type=3,
                               required=False,
                               choices=generate_choices_from_dict(name_mappings))])
    async def slash_tafsir(self, ctx: SlashContext, ref: str, tafsir: str = "maarifulquran"):
        spec = await self.process_request(ref, tafsir, 1)
        await self.send_embed(ctx, spec)

    @tafsir.error
    async def on_tafsir_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_ARGUMENTS.format(ctx.prefix))
        elif isinstance(error, InvalidReference):
            await ctx.send(INVALID_ARGUMENTS.format(ctx.prefix))
        elif isinstance(error, InvalidAyah):
            await ctx.send(INVALID_AYAH.format(error.num_verses))
        elif isinstance(error, InvalidSurah):
            await ctx.send(INVALID_SURAH)
        elif isinstance(error, InvalidTafsir):
            await ctx.send(INVALID_TAFSIR)
        elif isinstance(error, NoText):
            await ctx.send(NO_TEXT)
        elif isinstance(error, BadAlias):
            await ctx.send(BAD_ALIAS)


def setup(bot):
    bot.add_cog(TafsirEnglish(bot))
