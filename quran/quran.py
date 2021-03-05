import re

import discord
import pymysql
from discord.ext.commands import CheckFailure, MissingRequiredArgument
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from utils.database_utils import DBHandler
from quran.quran_info import *
from utils.utils import convert_to_arabic_number, get_site_json

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

TOO_LONG = "This passage was too long to send."

ICON = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'


class InvalidReference(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InvalidAyah(commands.CommandError):
    def __init__(self, num_verses, *args, **kwargs):
        self.num_verses = num_verses
        super().__init__(*args, **kwargs)


class InvalidTranslation(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Translation:
    def __init__(self, key):
        self.id = self.get_translation_id(key)

    @staticmethod
    def get_translation_id(key):
        translation_list = {
            'khattab': 131,  # English
            'bridges': 149,  # English
            'sahih':  20,  # English
            'maarifulquran': 167,  # English
            'jalandhari': 234,  # Urdu
            'suhel': 82,  # Hindi
            'awqaf': 78,  # Russian
            'musayev': 75, # Azeri
            'uyghur': 76, # Uyghur
            'haleem': 85, # English
            'abuadel': 79,  # Russian
            'karakunnu': 80,  # Malayalam
            'isagarcia': 83,  # Spanish
            'divehi': 86,  # Maldivian
            'burhan': 81,  # Kurdish
            'taqiusmani': 84,  # English
            'ghali': 17, # English
            'hilali': 18, # English
            'maududi.en': 95, # English
            'transliteration': 57,
            'pickthall': 19,  # English
            'yusufali': 22, # English
            'ruwwad': 206, # English
            'muhammadhijab': 207, # English
            'junagarri': 54, # Urdu
            'sayyidqutb': 156, # Urdu
            'mahmudhasan': 151, # Urdu
            'israrahmad': 158, # Urdu
            'maududi': 97, # Urdu
            'montada': 136, # French
            'khawaja': 139, # Tajik
            'ryoichi': 35, # Japanese
            'fahad.in': 134, # Indonesian
            'piccardo':  153, # Italian
            'taisirulquran': 161, # Bengali
            'mujibur': 163, # Bengali
            'rawai': 162, # Bengali
            'tagalog': 211, # Tagalog
            'ukrainian': 217, # Ukrainian
            'omar': 229, # Tamil
            'serbian': 215, # Serbian
            'bamoki': 143, # Kurdish
            'sabiq': 141, # German
            'telegu': 227, # Telugu
            'marathi': 226, # Marathi
            'hebrew': 233, # Hebrew
            'gujarati': 225, # Gujarati
            'abdulislam': 235, # Dutch
            'ganda': 232, # Ganda
            'khamis': 231, # Swahili
            'thai': 230, # Thai
            'kazakh': 222, # Kazakh
            'vietnamese': 220, # Vietnamese
            'siregar': 144, # Dutch
            'hasanefendi': 88, # Albanian
            'amharic': 87, # Amharic
            'jantrust': 50, # Tamil
            'barwani': 49, # Somali
            'swedish': 48, # Swedish
            'khmer': 128, # Khmer (Cambodian)
            'kuliev': 45, # Russian
            'diyanet': 77, # Turkish
            'turkish': 77,  # Turkish
            'basmeih': 39, # Malay
            'malay': 39, # Malay
            'korean': 219, # Korean (Hamed Choi)
            'finnish': 30, # Finnish
            'czech': 26, # Czech
            'nasr': 103, # Portuguese
            'ayati': 74, # Tajik
            'mansour': 101, # Uzbek
            'tatar': 53, # Tatar
            'romanian': 44, # Romanian
            'polish': 42, # Polish
            'norwegian': 41, # Norwegian
            'amazigh': 236, # Amazigh
            'sindhi': 238, # Sindhi
            'chechen': 106, # Chechen
            'bulgarian': 237, # Bulgarian
            'yoruba': 125, # Yoruba
            'shahin': 124, # Turkish
            'abduh': 46, # Somali
            'britch': 112, # Turkish
            'maranao': 38, # Maranao
            'ahmeti': 89, # Albanian
            'majian': 56, # Chinese
            'hausa': 32, # Hausa
            'nepali': 108, # Nepali
            'hameed': 37, # Malayalam
            'elhayek': 43, # Portuguese
            'cortes': 28, # Spanish
            'oromo': 111, # Oromo
            'french': 31, # French
            'hamidullah': 31, # French
            'persian': 29, # Persian
            'farsi': 29, # Persian
            'aburida': 208, # German
            'othman': 209, # Italian
            'georgian': 212, # Georgian
            'baqavi': 133, # Tamil
            'mehanovic': 25, # Bosnian
            'yazir': 52, # Turkish
            'zakaria': 213, # Bengali
            'noor': 199, # Spanish
            'sato': 218, # Japanese
            'sinhalese': 228, # Sinhala/Sinhalese
            'korkut': 126, # Bosnian
            'umari': 122, # Hindi
            'assamese': 120, # Assamese
            'sodik': 127, # Uzbek
            'pashto': 118, # Pashto
            'makin': 109, # Chinese
            'bubenheim': 27, # German
            'indonesian': 33, # Indonesian
        }
        if key in translation_list.keys():
            return translation_list[key]
        else:
            raise InvalidTranslation

    @staticmethod
    async def get_guild_translation(guild_id):
        translation_key = await DBHandler.get_guild_translation(guild_id)
        # Ensure we are not somehow retrieving an invalid translation
        try:
            Translation.get_translation_id(translation_key)
            return translation_key
        except InvalidTranslation:
            await DBHandler.delete_guild_translation(guild_id)
            return 'haleem'


class QuranRequest:
    def __init__(self, ctx, ref: str, is_arabic: bool, translation_key: str = None):
        self.ctx = ctx
        self.ref = QuranReference(ref, True)
        self.is_arabic = is_arabic
        if translation_key is not None:
            self.translation = Translation(translation_key)

        self.regular_url = 'https://api.quran.com/api/v4/quran/translations/{}?verse_key={}:{}'
        self.arabic_url = 'https://api.quran.com/api/v4/quran/verses/uthmani?verse_key={}'
        self.verse_ayah_dict = {}

    async def get_verses(self):
        for ayah in self.ref.ayat_list:
            json = await get_site_json(self.regular_url.format(self.translation.id, self.ref.surah, ayah))
            text = json['translations'][0]['text']

            # Clear footnotes
            cleanr = re.compile('<sup\s+foot_note=\d+>\d+<\/sup>')
            text = re.sub(cleanr, '', text)

            # Truncate verses longer than 1024 characters
            if len(text) > 1024:
                text = text[0:1018] + " [...]"

            self.verse_ayah_dict[f'{self.ref.surah}:{ayah}'] = text

            # TODO: Don't fetch the translation name every time we fetch a verse.
            self.translation_name = json['meta']['translation_name']

    async def get_arabic_verses(self):
        for ayah in self.ref.ayat_list:
            json = await get_site_json(self.arabic_url.format(f'{self.ref.surah}:{ayah}'))
            text = json['verses'][0]['text_uthmani']

            # Truncate verses longer than 1024 characters
            if len(text) > 1024:
                text = text[0:1018] + " [...]"

            self.verse_ayah_dict[f'{convert_to_arabic_number(str(self.ref.surah))}:{convert_to_arabic_number(str(ayah))}'] = text

    def construct_embed(self):
        surah = Surah(self.ref.surah)
        if self.is_arabic:
            em = discord.Embed(colour=0x048c28)
            em.set_author(name=f" سورة {surah.arabic_name}", icon_url=ICON)
        else:
            em = discord.Embed(colour=0x048c28)
            em.set_author(name=f"Surah {surah.name} ({surah.translated_name})", icon_url=ICON)
            em.set_footer(text=f"Translation: {self.translation_name} | {surah.revelation_location}")

        for key, text in self.verse_ayah_dict.items():
            em.add_field(name=key, value=text, inline=False)

        return em

    async def process_request(self):
        if self.is_arabic:
            await self.get_arabic_verses()
        else:
            await self.get_verses()

        em = self.construct_embed()
        if len(em) > 6000:
            await self.ctx.send(TOO_LONG)
        else:
            await self.ctx.send(embed=em)


class Quran(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="quran")
    async def quran(self, ctx, ref: str, translation_key: str = None):
        async with ctx.channel.typing():
            if translation_key is None:
                translation_key = await Translation.get_guild_translation(ctx.guild.id)
            await QuranRequest(ctx=ctx, is_arabic=False, ref=ref, translation_key=translation_key).process_request()

    @commands.command(name="aquran")
    async def aquran(self, ctx, ref: str):
        async with ctx.channel.typing():
            await QuranRequest(ctx=ctx, is_arabic=True, ref=ref).process_request()

    @quran.error
    async def quran_command_error(self, ctx, error):
        if isinstance(error, InvalidSurah):
            await ctx.send(INVALID_SURAH)
        if isinstance(error, InvalidAyah):
            await ctx.send(INVALID_AYAH.format(error.num_verses))
        if isinstance(error, InvalidTranslation) or isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_TRANSLATION)
        if isinstance(error, InvalidReference):
            await ctx.send(INVALID_ARGUMENTS_ENGLISH.format(ctx.prefix))
        if isinstance(error, BadArgument):
            await ctx.send(INVALID_ARGUMENTS_ENGLISH.format(ctx.prefix))

    @aquran.error
    async def aquran_command_error(self, ctx, error):
        if isinstance(error, InvalidSurah):
            await ctx.send(INVALID_SURAH)
        if isinstance(error, InvalidAyah):
            await ctx.send(INVALID_AYAH.format(error.num_verses))
        if isinstance(error, InvalidTranslation) or isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_TRANSLATION)
        if isinstance(error, InvalidReference):
            await ctx.send(INVALID_ARGUMENTS_ARABIC.format(ctx.prefix))
        if isinstance(error, BadArgument):
            await ctx.send(INVALID_ARGUMENTS_ARABIC.format(ctx.prefix))

    @cog_ext.cog_slash(name="quran", description="Send verses from the Qurʼān.",
                       options=[
                           create_option(
                               name="reference",
                               description="The verse(s) to fetch, e.g. 1:1, 2:255, 1:1-7, 2:255-260",
                               option_type=3,
                               required=True),
                           create_option(
                               name = "translation_key",
                               description="The translation to use.",
                               option_type=3,
                               required=False)])
    async def slash_quran(self, ctx: SlashContext, reference: str, translation_key: str = None):
        await ctx.respond()
        if translation_key is None:
            translation_key = await Translation.get_guild_translation(ctx.guild.id)
        await QuranRequest(ctx=ctx, is_arabic=False, ref=reference, translation_key=translation_key).process_request()

    @cog_ext.cog_slash(name="aquran",
                       description="تبعث آيات قرآنية في الشات",
                       options=[
                           create_option(
                               name="ayat",
                               description="اكتب رقم السورة:رقم الآية. اذا اردت ان تبعث اكثر من اية, اكتب  رقم السورة:أول آية-اخر آية",
                               option_type=3,
                               required=True)])
    async def slash_aquran(self, ctx: SlashContext, reference: str):
        await ctx.respond()
        await QuranRequest(ctx=ctx, is_arabic=True, ref=reference).process_request()

    async def _settranslation(self, ctx, translation):
        Translation.get_translation_id(translation)
        await DBHandler.create_connection()
        await DBHandler.update_guild_translation(ctx.guild.id, translation)
        await ctx.send(f"**Successfully updated default translation to `{translation}`!**")

    @commands.command(name="settranslation")
    @commands.has_permissions(administrator=True)
    async def settranslation(self, ctx, translation: str):
        await self._settranslation(ctx, translation)

    @settranslation.error
    async def settranslation_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.send("🔒 You need the **Administrator** permission to use this command.")
        if isinstance(error, MissingRequiredArgument) or isinstance(error, InvalidTranslation):
            await ctx.send(INVALID_TRANSLATION)
        if isinstance(error, pymysql.err.OperationalError):
            print(error)
            await ctx.send(DATABASE_UNREACHABLE)

    @cog_ext.cog_slash(name="settranslation",
                       description="🔒 Administrator only command. Changes the default translation for /quran.",
                       options=[
                           create_option(
                               name="translation",
                               description="The translation to use. See /help quran for a list.",
                               option_type=3,
                               required=True)])
    @commands.has_permissions(administrator=True)
    async def slash_settranslation(self, ctx: SlashContext, translation: str):
        await ctx.respond()
        await self._settranslation(ctx, translation)

    @commands.command(name="surah")
    async def surah(self, ctx, surah_num: int):
        async with ctx.channel.typing():
            surah = Surah(surah_num)
            em = discord.Embed(colour=0x048c28)
            em.set_author(name=f'Surah {surah.name} ({surah.translated_name}) |  سورة {surah.arabic_name}', icon_url=ICON)
            em.description = (f'\n• **Number of verses**: {surah.verses_count}'
                              f'\n• **Revelation location**: {surah.revelation_location}'
                              f'\n• **Revelation order**: {surah.revelation_order} ')
            await ctx.send(embed=em)

    @surah.error
    async def surah_error(self, ctx, error):
        if isinstance(error, BadArgument):
            await ctx.send("**Error**: Invalid surah number.")
        if isinstance(error, MissingRequiredArgument):
            await ctx.send("**Error**: You typed the command wrongly. Type `-surah <surah number>`.")
        if isinstance(error, InvalidSurah):
            await ctx.send(INVALID_SURAH)


def setup(bot):
    bot.add_cog(Quran(bot))
