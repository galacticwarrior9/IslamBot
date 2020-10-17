import aiohttp
import discord
from discord.ext import commands
from discord.ext.commands import CheckFailure, MissingRequiredArgument, BadArgument
from utils import convert_to_arabic_number, make_embed
from dbhandler import DBHandler
from quranInfo import *

INVALID_TRANSLATION = "**Invalid translation**. List of translations: <https://github.com/galacticwarrior9/is" \
                      "lambot/blob/master/Translations.md>"

INVALID_ARGUMENTS_ARABIC = "**Invalid arguments!** Type `{0}aquran [surah]:[ayah]`. \n\nExample: `{0}aquran 1:1`" \
                               "\n\nTo send multiple verses, type `{0}quran [surah]:[first ayah]-[last ayah]`" \
                               "\n\nExample: `{0}aquran 1:1-7`"

INVALID_ARGUMENTS_ENGLISH = "**Invalid arguments!** Type `{0}quran [surah]:[ayah]`. \n\nExample: `{0}quran 1:1`" \
                               "\n\nTo send multiple verses, type `{0}quran [surah]:[first ayah]-[last ayah]`" \
                               "\n\nExample: `{0}quran 1:1-7`"

INVALID_SURAH = "**There only 114 surahs.** Please choose a surah between 1 and 114."

INVALID_AYAH = "**There are only {0} verses in this surah**."

DATABASE_UNREACHABLE = "Could not contact database. Please report this on the support server!"

ICON = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'


class InvalidSurah(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InvalidAyah(commands.CommandError):
    def __init__(self, num_verses, *args, **kwargs):
        self.num_verses = num_verses
        super().__init__(*args, **kwargs)

class ConnectionIssue(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class QuranSpecifics:
    def __init__(self, ref, edition):
        self.max_ayah = None
        self.min_ayah = None
        self.edition = edition
        self.edition_name = None
        self.ref = ref
        self.surah, self.offset, self.limit = self.process_ref(ref)
        self.quran_com = self.is_quran_com(edition)

    def return_self(self):
        return self

    def process_ref(self, ref):

        surah = int(ref.split(':')[0])

        if not 0 < surah < 115:
            raise InvalidSurah

        min_ayah = int(ref.split(':')[1].split('-')[0])

        try:
            max_ayah = int(ref.split(':')[1].split('-')[1]) + 1
        except IndexError:
            max_ayah = min_ayah + 1

        # If the min ayah is larger than the max ayah, we assume this is a mistake and swap their values.
        if min_ayah > max_ayah:
            temp = min_ayah
            min_ayah = max_ayah
            max_ayah = temp

        offset = min_ayah - 1
        limit = max_ayah - min_ayah
        if limit > 25:
            limit = 25

        self.max_ayah = max_ayah - 1
        self.min_ayah = min_ayah

        return [surah, offset, limit]

    @staticmethod
    def is_quran_com(edition):
        return True if isinstance(edition, int) else False


class Quran(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.session = aiohttp.ClientSession(loop=bot.loop)
        self.quran_com_url = 'http://api.quran.com:3000/api/v3/chapters/{}/verses?translations={}&language=en&offset={' \
                             '}&limit={}&text_type=words'
        self.alquran_url = 'http://api.alquran.cloud/surah/{}/{}?offset={}&limit={}'
        self.arabic_url = 'http://api.alquran.cloud/surah/{}?offset={}&limit={}'

    @staticmethod
    def format_edition(edition):
        edition_dict = {
            'mammadaliyev': 'az.mammadaliyev',
            'musayev': 'az.musayev',
            'bengali': 'bn.bengali',
            'bulgarian': 'bg.theophanov',
            'bosnian': 25,
            'hrbek': 'cs.hrbek',
            'nykl': "cs.nykl",
            'aburida': 'de.aburida',
            'bubenheim': 'de.bubenheim',
            'khoury': 'de.khoury',
            'zaidan': "de.zaidan",
            'divehi': 'dv.divehi',
            'amharic': 87,
            'haleem': 85,
            'taqiusmani': 84,
            'khattab': 101,
            'ghali': 17,
            'finnish': 30,
            'indonesian': 33,
            'tajik': 74,
            'chechen': 106,
            'czech': 26,
            'sahih': 20,
            'ahmedali': 'en.ahmedali',
            'arberry': 'en.arberry',
            'asad': 'en.asad',
            'daryabadi': 'en.daryabadi',
            'hilali': 18,
            'pickthall': 19,
            'qaribullah': 'en.qaribullah',
            'sarwar': 'en.sarwar',
            'yusufali': 22,
            'shakir': 'en.shakir',
            'transliteration': 'en.transliteration',
            'spanish': 83,
            'ansarian': 'fa.ansarian',
            'ayati': 'fa.ayati',
            'fooladvand': 'fa.fooladvand',
            'ghomshei': 'fa.ghomshei',
            'makarem': 'fa.makarem',
            'french': 31,
            'hausa': 32,
            'hindi': 82,
            'italian': 34,
            'japanese': 'ja.japanese',
            'korean': 'ko.korean',
            'kurdish': 	81,
            'malayalam': 37,
            'dutch': 40,
            'norwegian': 'no.berg',
            'polish': 'pl.bielawskiego',
            'portuguese': 'pt.elhayek',
            'romanian': 'ro.grigore',
            'kuliev': 45,
            'osmanov': 'ru.osmanov',
            'porokhova': 'ru.porokhova',
            'sindhi': 'sd.amroti',
            'somali': 46,
            'ahmeti': 'sq.ahmeti',
            'mehdiu': 'sq.mehdiu',
            'nahi': 'sq.nahi',
            'swedish': 48,
            'swahili': 'sw.barwani',
            'tamil': 'ta.tamil',
            'thai': 'th.thai',
            'ates': 'tr.ates',
            'bulac': 'tr.bulac',
            'diyanet': 77,
            'golpinarli': 'tr.golpinarli',
            'ozturk': 'tr.ozturk',
            'vakfi': 'tr.vakfi',
            'yazir': 'tr.yazir',
            'yildirim': 'tr.yildirim',
            'yuksel': 'tr.yuksel',
            'tatar': 'tt.nugman',
            'uyghur': 'ug.saleh',
            'jalandhry': 'ur.jalandhry',
            'jawadi': 'ur.jawadi',
            'qadri': 'ur.qadri',
            'urdu': 97,
            'maududi': 97,
            'junagarhi': 54,
            'maududi.en': 95,
            'malay': 39,
            'uzbek': 'uz.sodik',
            'chinese': 'zh.jian',
            'ukrainian': 104,
            'abuadel': 79,
            'maranao': 38
        }
        return edition_dict[edition]

    @staticmethod
    def get_language_code(edition):
        language_codes = {
            31: 'fr',  # Hamidullah, French
            97: 'ur',  # Maududi, Urdu
            54: 'ur',  # Junagarhi, Urdu
            'ur.jalandhry': 'ur',
            'ur.jawadi': 'ur',
            'ur.qadri': 'ur',
            83: 'es',  # Isa Garcia, Spanish
            40: 'nl',  # Salomo Keyzar, Dutch
            25: 'bs',  # Bosnian
            33: 'id',  # Indonesian
            45: 'ru',  # Kuliev, Russian
            78: 'ru',  # Ministry of Awqaf, Russian
            79: 'ru',  # Abu Adel, Russian
            48: 'sv',  # Knut Bernström, Swedish
            'ar': 'ar'
        }
        if edition in language_codes:
            return language_codes[edition]
        return None

    @commands.command(name="settranslation")
    @commands.has_permissions(administrator=True)
    async def settranslation(self, ctx, translation: str):

        try:
            self.format_edition(translation)
        except KeyError:
            return await ctx.send(INVALID_TRANSLATION)

        try:
            await DBHandler.create_connection()
        except Exception as e:
            print(e)
            return await ctx.send(DATABASE_UNREACHABLE)

        await DBHandler.update_guild_translation(ctx.guild.id, translation)
        await ctx.send(f"**Successfully updated default translation to `{translation}`!**")

    @settranslation.error
    async def settranslation_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.send("🔒 You need the **Administrator** permission to use this command.")
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_TRANSLATION)

    @commands.command(name="quran")
    async def quran(self, ctx, ref: str, edition: str = None):
        async with ctx.channel.typing():

            # If no translation was specified, find a translation to use.
            if edition is None:
                try:
                    edition = await DBHandler.get_guild_translation(ctx.message.guild.id)
                    edition = self.format_edition(edition)
                except:
                    edition = 85

            # If a translation was specified in the command, check whether it is valid:
            else:
                try:
                    edition = self.format_edition(edition)
                except KeyError:
                    return await ctx.send(INVALID_TRANSLATION)

            # Now fetch the verses:
            spec = self.get_spec(ref, edition)

            try:
                name, _, translated_name, revelation_location, _, num_verses, _, _, _ = await self.get_surah_info(spec)
            except ConnectionIssue:
                name, _, translated_name, revelation_location, _, num_verses, _, _ = self.get_surah_info_local(spec)


            if spec.max_ayah > num_verses or spec.min_ayah < 1:
                raise InvalidAyah(num_verses)

            if revelation_location == "Makkah":
                revelation_location = "Meccan"
            elif revelation_location == 'Madinah':
                revelation_location = "Medinan"

            verses = await self.get_verses(spec)

            em = make_embed(fields=verses, author=f"Surah {name} ({translated_name})", author_icon=ICON, colour=0x048c28
                            , inline=False, footer=f'Translation: {spec.edition_name} | {revelation_location}')

            if len(em) > 6000:
                return await ctx.send("This passage was too long to send.")

            await ctx.send(embed=em)

    @commands.command(name="aquran")
    async def aquran(self, ctx, ref: str):

        spec = self.get_spec(ref)


        try:
            _, name, _, _, _, _, _, _, _ = await self.get_surah_info(spec)
        except ConnectionIssue:
            _, name, _, _, _, _, _, _ = self.get_surah_info_local(spec)
        verses = await self.get_verses(spec)

        em = make_embed(fields=verses, author=f' سورة {name}', author_icon=ICON, colour=0x048c28, inline=False,
                        footer="")

        if len(em) > 6000:
            return await ctx.send("This passage was too long to send.")

        await ctx.send(embed=em)

    @quran.error
    @aquran.error
    async def quran_error(self, ctx, error):
        if isinstance(error, InvalidSurah):
            await ctx.send(INVALID_SURAH)
        if isinstance(error, InvalidAyah):
            await ctx.send(INVALID_AYAH.format(error.num_verses))
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_TRANSLATION)
        if isinstance(error, BadArgument):
            await ctx.send(INVALID_ARGUMENTS_ENGLISH.format(ctx.prefix))

    @commands.command(name="surah")
    async def surah(self, ctx, surah_number: int):

        if not 0 < surah_number < 115:
            return await ctx.send(INVALID_SURAH)

        spec = self.get_spec(f'{surah_number}:1')
        try:
            name, arabic_name, translated_name, revelation_location, revelation_order, verses_count, summary, first_page, \
            final_page = await self.get_surah_info(spec)
        except ConnectionIssue:
            summary = ''
            name, arabic_name, translated_name, revelation_location, revelation_order, verses_count, first_page, \
            final_page = self.get_surah_info_local(spec)

        em = discord.Embed(colour=0x048c28, title=f'Surah {name} ({translated_name}) |  سورة {arabic_name}')
        em.set_author(name="Surah Information", icon_url=ICON)
        em.description = f'{summary}' \
                         f'\n\n• **Number of verses**: {verses_count}' \
                         f'\n• **Revelation location**: {revelation_location}' \
                         f'\n• **Revelation order**: {revelation_order} ' \
                         f'\n• **Pages on mushaf**: {first_page}—{final_page}'
        await ctx.send(embed=em)

    @staticmethod
    def get_spec(ref, edition='ar'):
        return QuranSpecifics(ref, edition)

    async def get_verses(self, spec):
        """Fetches the verses' text. We use the quran.com API or alquran.cloud API depending on the translation used."""
        if spec.quran_com:
            async with self.session.get(self.quran_com_url.format(spec.surah, spec.edition, spec.offset, spec.limit)) as r:
                data = await r.json()
                ayaat = data['verses']
            verses = {f"{spec.surah}:{ayah['verse_number']}": ayah['translations'][0]['text'] for ayah in ayaat}
            spec.edition_name = data['verses'][0]['translations'][0]['resource_name']

        elif spec.edition == 'ar':
            async with self.session.get(self.arabic_url.format(spec.surah, spec.offset, spec.limit)) as r:
                data = await r.json()
                ayaat = data['data']['ayahs']
            verses = {f"{convert_to_arabic_number(str(spec.surah))}:{convert_to_arabic_number(str(ayah['numberInSurah']))}": ayah['text'] for ayah in ayaat}

        else:
            async with self.session.get(self.alquran_url.format(spec.surah, spec.edition, spec.offset, spec.limit)) as r:
                data = await r.json()
                ayaat = data['data']['ayahs']
            verses = {f"{spec.surah}:{ayah['numberInSurah']}": ayah['text'] for ayah in ayaat}
            spec.edition_name = data['data']['edition']['name']

        verses = self.truncate_verses(verses)
        return verses

    @staticmethod
    def truncate_verses(verses):
        """Truncate verses longer than 1024 characters."""
        for key, verse in verses.items():
            if len(verse) > 1024:
                verses.update({key: f"{verse[0:1021]}..."})
        return verses

    async def get_surah_info(self, spec):

        language_code = self.get_language_code(spec.edition)

        async with self.session.get(f'http://api.quran.com/api/v3/chapters/{spec.surah}?language={language_code}') as r:
            if r.status != 200:
                raise ConnectionIssue
            data = await r.json()
            name = data['chapter']['name_simple']
            arabic_name = data['chapter']['name_arabic']
            translated_name = data['chapter']['translated_name']['name']
            revelation_location = data['chapter']['revelation_place'].title()
            revelation_order = data['chapter']['revelation_order']
            verses_count = data['chapter']['verses_count']
            first_page, final_page = [page for page in data['chapter']['pages']]

        async with self.session.get(f'http://api.quran.com/api/v3/chapters/{spec.surah}/info') as r:
            if r.status != 200:
                raise ConnectionIssue
            data = await r.json()
            summary = data['chapter_info']['short_text']

        return name, arabic_name, translated_name, revelation_location, revelation_order, verses_count, summary,\
               first_page, final_page

    def get_surah_info_local(self, spec):
        surahNum = spec.surah
        name = quranInfo['surah'][surahNum][5]
        arabic_name = quranInfo['surah'][surahNum][4]
        translated_name = quranInfo['surah'][surahNum][6]
        revelation_location = quranInfo['surah'][surahNum][7]
        revelation_order = quranInfo['surah'][surahNum][2]
        verses_count = quranInfo['surah'][surahNum][1]
        first_page, final_page = (None, None)
        for i, page in enumerate(quranInfo['page']):
            if first_page is None and page[0] >= surahNum:
                if page[0] == surahNum and page[1] == 1:
                    first_page = i
                else:
                    first_page = i-1
            if final_page is None and page[0] > surahNum:
                final_page = i-1
        return name, arabic_name, translated_name, revelation_location, revelation_order, verses_count,\
               first_page, final_page


def setup(bot):
    bot.add_cog(Quran(bot))
