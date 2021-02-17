import asyncio
import re

import discord
import textwrap
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument

from quranInfo import quranInfo, Surah, InvalidSurah
from utils import get_site_source, get_site_json

icon = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

name_mappings = {
    'ibnkathir': 'Tafsīr Ibn Kathīr',
    'jalalayn': 'Tafsīr al-Jalālayn',
    'tustari': 'Tafsīr al-Tustarī',
    'kashani': 'Tafsīr ʿAbd al-Razzāq al-Kāshānī',
    'qushayri': 'Laṭāʾif al-Ishārāt',
    'wahidi': 'Asbāb al-Nuzūl',
    'kashf': 'Kashf al-Asrār',
    'saddi': "Tafsīr al-Sa'di",
    'zakaria': 'Tafsir Abu Bakr Zakaria',
    "israr": "تفسیر بیان القرآن",
    "ibnkathir.ur": "تفسیر ابنِ کثیر",
    'ibnkathir.bn': 'তাফসীর ইবনে কাছী',
    'mukhtasar': 'Al-Mukhtasar',
    'maarifulquran': 'Maarif-ul-Quran',
    'ahsanul': 'Tafsir Ahsanul Bayaan'
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
                 "\n\n**List of tafasir**: <https://github.com/galacticwarrior9/islambot/blob/master/Tafsir.md>."

INVALID_SURAH = "**There only 114 surahs.** Please choose a surah between 1 and 114."

INVALID_AYAH = "**There are only {0} verses in this surah**."

NO_TEXT = "**Could not find tafsir for this verse.** Please try another tafsir." \
          "\n\n**List of tafasir**: <https://github.com/galacticwarrior9/islambot/blob/master/Tafsir.md>."

altafsir_url = 'https://www.altafsir.com/Tafasir.asp?tMadhNo=0&tTafsirNo={}&tSoraNo={}&tAyahNo={}&tDisplay=yes&Page={}&Size=1&LanguageId=2'

quranCom_url = 'https://api.quran.com/api/v4/quran/tafsirs/{}?verse_key={}'

jalalayn_url = 'https://raw.githubusercontent.com/galacticwarrior9/islambot/master/tafsir_jalalayn.txt'


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


class TafsirReference:
    def __init__(self, ref: str):
        self.ref = ref
        self.surah_num = None
        self.process_ref()
        self.surah = Surah(self.surah_num)

    def process_ref(self):
        try:
            self.surah_num, self.ayah = self.ref.split(':', 1)
            self.surah_num, self.ayah = int(self.surah_num), int(self.ayah)
        except:
            raise InvalidReference

        if not 1 <= self.surah_num <= 114:
            raise InvalidSurah

        self.check_ayat_num()

    def check_ayat_num(self):
        num_ayat = quranInfo['surah'][self.surah_num][1]
        if self.ayah > num_ayat:
            raise InvalidAyah(num_ayat)


class TafsirSpecifics:
    def __init__(self, tafsir, ref, page):
        self.pages = None
        self.num_pages = None
        self.url = None
        self.tafsir_author = None
        self.text = None
        self.embed = None
        self.page = page
        self.tafsir = tafsir.lower()
        if self.tafsir not in name_mappings.keys():
            raise InvalidTafsir
        self.tafsir_name = name_mappings[tafsir]
        self.ref = TafsirReference(ref)
        self.make_url()

    def make_url(self):
        if self.tafsir in altafsir_sources.keys():
            tafsir_id = altafsir_sources[self.tafsir]
            self.url = altafsir_url.format(tafsir_id, self.ref.surah_num, self.ref.ayah, 1)
        elif self.tafsir == 'jalalayn':
            self.url = jalalayn_url
        elif self.tafsir in quranCom_sources.keys():
            tafsir_id = quranCom_sources[self.tafsir]
            self.url = quranCom_url.format(tafsir_id, f'{self.ref.surah_num}:{self.ref.ayah}')

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
            try:
                self.text = source['tafsirs'][0]['text']
                self.tafsir_author = source['meta']['author_name']
            except IndexError:
                raise NoText

            # Replace HTML tags
            cleanr = re.compile('<(.*?)>')
            self.text = re.sub(cleanr, ' ', self.text)
            self.text = self.text.replace('`', "ʿ")

        elif self.tafsir == 'jalalayn':
            source = await get_site_source(self.url)
            source = source.decode('utf-8')
            self.tafsir_author = 'Jalal ad-Din al-Maḥalli and Jalal ad-Din as-Suyuti'

            try:
                char1 = f'[{self.ref.surah_num}:{self.ref.ayah}]'
                next_ayah = self.ref.ayah + 1
                char2 = f'[{self.ref.surah_num}:{next_ayah}]'

                text = source[(source.index(char1) + len(char1)):source.index(char2)]
                self.text = f"{text}".replace('`', '\\`').replace('(s)', '(ﷺ)').rstrip()

            except:
                char1 = f'[{self.ref.surah_num}:{self.ref.ayah}]'
                self.ref.surah_num += 1
                char2 = f'[{self.ref.surah_num}:1]'

                text = source[(source.index(char1) + len(char1)):source.index(char2)]
                self.text = u"{}".format(text).replace('`', '\\`').rstrip()

        self.pages = textwrap.wrap(self.text, 2000, break_long_words=False)
        self.num_pages = len(self.pages)

    async def make_embed(self):
        em = discord.Embed(colour=0x467f05, description=self.pages[self.page - 1])
        em.title = f'Tafsir of Surah {self.ref.surah.name}, Verse {self.ref.ayah}'
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
        msg = await ctx.send(embed=spec.embed)
        if spec.num_pages > 1:
            await msg.add_reaction(emoji='⬅')
            await msg.add_reaction(emoji='➡')

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=300, check=lambda reaction, user:
                (reaction.emoji == '➡' or reaction.emoji == '⬅')
                 and user != self.bot.user
                 and reaction.message.id == msg.id)

            except asyncio.TimeoutError:
                await msg.remove_reaction(emoji='➡', member=self.bot.user)
                await msg.remove_reaction(emoji='⬅', member=self.bot.user)
                break

            if reaction.emoji == '➡' and spec.page:
                spec.page += 1
                if spec.page > spec.num_pages:
                    spec.page = 1

            if reaction.emoji == '⬅':
                spec.page -= 1
                if spec.page < 1:
                    spec.page = spec.num_pages

            await spec.make_embed()
            await msg.edit(embed=spec.embed)
            try:
                await msg.remove_reaction(reaction.emoji, user)
            # The above fails if the bot doesn't have the "Manage Messages" permission, but it can be safely ignored
            # as it is not essential functionality.
            except discord.ext.commands.errors.CommandInvokeError:
                pass

    async def process_request(self, ref: str, tafsir: str, page: int, attempt: int):
        spec = TafsirSpecifics(tafsir, ref, page)
        await spec.get_text()

        if len(spec.text) == 0:
            raise NoText

        await spec.make_embed()
        return spec

    @commands.command(name='tafsir')
    async def tafsir(self, ctx, ref: str, tafsir: str = "maarifulquran", page: int = 1):
        spec = await self.process_request(ref, tafsir, page, -1)
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


def setup(bot):
    bot.add_cog(TafsirEnglish(bot))
