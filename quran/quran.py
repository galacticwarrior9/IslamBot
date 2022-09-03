import random
import re

import discord
import pymysql
from discord.ext import commands
from discord.ext.commands import CheckFailure

from quran.quran_info import *
from utils.database_utils import DBHandler
from utils.errors import InvalidTranslation, respond_to_interaction_error
from utils.utils import convert_to_arabic_number, get_site_json

INVALID_TRANSLATION = "**Invalid translation**. List of translations: <https://github.com/galacticwarrior9/IslamBot/wiki/Qur%27an-Translation-List>"

DATABASE_UNREACHABLE = "Could not contact database. Please report this on the support server!"

TOO_LONG = "This passage was too long to send."

ICON = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

CLEAN_HTML_REGEX = re.compile('<[^<]+?>\d*')

translation_list = {
    'khattab': 131,  # English
    'bridges': 149,  # English
    'sahih': 20,  # English
    'maarifulquran': 167,  # English
    'jalandhari': 234,  # Urdu
    'suhel': 82,  # Hindi
    'awqaf': 78,  # Russian
    'musayev': 75,  # Azeri
    'uyghur': 76,  # Uyghur
    'haleem': 85,  # English
    'abuadel': 79,  # Russian
    'karakunnu': 80,  # Malayalam
    'isagarcia': 83,  # Spanish
    'divehi': 86,  # Maldivian
    'burhan': 81,  # Kurdish
    'taqiusmani': 84,  # English
    'ghali': 17,  # English
    'hilali': 203,  # English
    'maududi.en': 95,  # English
    'transliteration': 57,
    'pickthall': 19,  # English
    'yusufali': 22,  # English
    'ruwwad': 206,  # English
    'muhammadhijab': 207,  # English
    'junagarri': 54,  # Urdu
    'sayyidqutb': 156,  # Urdu
    'mahmudhasan': 151,  # Urdu
    'israrahmad': 158,  # Urdu
    'maududi': 97,  # Urdu
    'montada': 136,  # French
    'khawaja': 139,  # Tajik
    'ryoichi': 35,  # Japanese
    'fahad.in': 134,  # Indonesian
    'piccardo': 153,  # Italian
    'taisirulquran': 161,  # Bengali
    'mujibur': 163,  # Bengali
    'rawai': 162,  # Bengali
    'tagalog': 211,  # Tagalog
    'ukrainian': 217,  # Ukrainian
    'omar': 229,  # Tamil
    'serbian': 215,  # Serbian
    'bamoki': 143,  # Kurdish
    'sabiq': 141,  # Indonesian
    'telegu': 227,  # Telugu
    'marathi': 226,  # Marathi
    'hebrew': 233,  # Hebrew
    'gujarati': 225,  # Gujarati
    'abdulislam': 235,  # Dutch
    'ganda': 232,  # Ganda
    'khamis': 231,  # Swahili
    'thai': 230,  # Thai
    'kazakh': 222,  # Kazakh
    'vietnamese': 220,  # Vietnamese
    'siregar': 144,  # Dutch
    'hasanefendi': 88,  # Albanian
    'amharic': 87,  # Amharic
    'jantrust': 50,  # Tamil
    'barwani': 49,  # Somali
    'swedish': 48,  # Swedish
    'khmer': 128,  # Khmer (Cambodian)
    'kuliev': 45,  # Russian
    'diyanet': 77,  # Turkish
    'turkish': 77,  # Turkish
    'basmeih': 39,  # Malay
    'malay': 39,  # Malay
    'korean': 219,  # Korean (Hamed Choi)
    'finnish': 30,  # Finnish
    'czech': 26,  # Czech
    'nasr': 103,  # Portuguese
    'ayati': 74,  # Tajik
    'mansour': 101,  # Uzbek
    'tatar': 53,  # Tatar
    'romanian': 44,  # Romanian
    'polish': 42,  # Polish
    'norwegian': 41,  # Norwegian
    'amazigh': 236,  # Amazigh
    'sindhi': 238,  # Sindhi
    'chechen': 106,  # Chechen
    'bulgarian': 237,  # Bulgarian
    'yoruba': 125,  # Yoruba
    'shahin': 124,  # Turkish
    'abduh': 46,  # Somali
    'britch': 112,  # Turkish
    'maranao': 38,  # Maranao
    'ahmeti': 89,  # Albanian
    'majian': 56,  # Chinese
    'hausa': 32,  # Hausa
    'nepali': 108,  # Nepali
    'hameed': 37,  # Malayalam
    'elhayek': 43,  # Portuguese
    'cortes': 28,  # Spanish
    'oromo': 111,  # Oromo
    'french': 31,  # French
    'hamidullah': 31,  # French
    'persian': 29,  # Persian
    'farsi': 29,  # Persian
    'aburida': 208,  # German
    'othman': 209,  # Italian
    'georgian': 212,  # Georgian
    'baqavi': 133,  # Tamil
    'mehanovic': 25,  # Bosnian
    'yazir': 52,  # Turkish
    'zakaria': 213,  # Bengali
    'noor': 199,  # Spanish
    'sato': 218,  # Japanese
    'sinhalese': 228,  # Sinhala/Sinhalese
    'korkut': 126,  # Bosnian
    'umari': 122,  # Hindi
    'assamese': 120,  # Assamese
    'sodik': 127,  # Uzbek
    'pashto': 118,  # Pashto
    'makin': 109,  # Chinese
    'bubenheim': 27,  # German
    'indonesian': 33,  # Indonesian
}


class Translation:
    def __init__(self, key):
        self.id = self.get_translation_id(key)

    @staticmethod
    def get_translation_id(key):
        if key in translation_list:
            return translation_list[key]

        translation = process.extract(key, translation_list.keys(), scorer=fuzz.partial_ratio, limit=1)
        if translation is None:
            raise InvalidTranslation

        return translation_list[translation[0][0]]

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
    def __init__(self, interaction: discord.Interaction, ref: str, is_arabic: bool, translation_key: str = None, reveal_order: bool = False):
        self.webhook = interaction.followup
        self.ref = QuranReference(ref=ref, allow_multiple_verses=True, reveal_order=reveal_order)
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

            # Clear HTML tags
            text = re.sub(CLEAN_HTML_REGEX, ' ', text)

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

            self.verse_ayah_dict[
                f'{convert_to_arabic_number(str(self.ref.surah))}:{convert_to_arabic_number(str(ayah))}'] = text

    def construct_embed(self):
        surah = Surah(self.ref.surah)
        if self.is_arabic:
            em = discord.Embed(colour=0x048c28)
            em.set_author(name=f" سورة {surah.arabic_name}", icon_url=ICON)
        else:
            em = discord.Embed(colour=0x048c28)
            em.set_author(name=f"Surah {surah.name} ({surah.translated_name})", icon_url=ICON)
            em.set_footer(text=f"Translation: {self.translation_name} | {surah.revelation_location}")

        if len(self.verse_ayah_dict) > 1:
            for key, text in self.verse_ayah_dict.items():
                em.add_field(name=key, value=text, inline=False)

            return em

        em.title = list(self.verse_ayah_dict)[0]
        em.description = list(self.verse_ayah_dict.values())[0]

        return em

    async def process_request(self):
        if self.is_arabic:
            await self.get_arabic_verses()
        else:
            await self.get_verses()

        em = self.construct_embed()
        if len(em) > 6000:
            await self.webhook.send(TOO_LONG)
        else:
            await self.webhook.send(embed=em)


class Quran(commands.Cog):

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @discord.app_commands.command(name="quran", description="Send verses from the Qurʼān.")
    @discord.app_commands.describe(
        surah="The name or number of the surah to fetch, e.g. Al-Ikhlaas or 112",
        start_verse="The first verse to fetch, e.g. 255.",
        end_verse="The last verse to fetch if you want to send multiple verses, e.g. 260",
        translation="The translation to use",
        reveal_order="If you specified a number for the surah, whether the number is the surah's revelation order."
    )
    async def quran(self, interaction: discord.Interaction, surah: str, start_verse: int, end_verse: int = None,
                          translation: str = None, reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        ref = start_verse if end_verse is None else f'{start_verse}-{end_verse}'
        if translation is None:
            translation = await Translation.get_guild_translation(interaction.guild_id)

        surah_number = QuranReference.parse_surah_number(surah)
        await QuranRequest(interaction=interaction, is_arabic=False, ref=f'{surah_number}:{ref}', translation_key=translation,
                           reveal_order=reveal_order).process_request()

    @discord.app_commands.command(name="aquran", description="تبعث آيات قرآنية في الشات")
    @discord.app_commands.describe(
        surah="اكتب رقم أو اسم السورة",
        start_verse="اكتب رقم أول آية",
        end_verse="اذا اردت ان تبعث اكثر من اية اكتب رقم اخر آية",
        reveal_order="هل السورة تشير إلى رقم أمر الوحي؟"
    )
    async def aquran(self, interaction: discord.Interaction, surah: str, start_verse: int, end_verse: int = None,
                           reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        ref = start_verse if end_verse is None else f'{start_verse}-{end_verse}'
        surah_number = QuranReference.parse_surah_number(surah)
        await QuranRequest(interaction=interaction, is_arabic=True, ref=f'{surah_number}:{ref}',
                           reveal_order=reveal_order).process_request()

    @discord.app_commands.command(name="rquran", description="Retrieve a random verse from the Qur'ān.")
    @discord.app_commands.describe(translation="The translation to use.")
    async def rquran(self, interaction: discord.Interaction, translation: str = None) -> None:
        await interaction.response.defer(thinking=True)
        surah = random.randint(1, 114)
        verse = random.randint(1, quranInfo['surah'][surah][1])

        if translation is None:
            translation = await Translation.get_guild_translation(interaction.guild_id)

        await QuranRequest(interaction=interaction, is_arabic=False, ref=f'{surah}:{verse}',
                           translation_key=translation).process_request()

    @quran.autocomplete('translation')
    @rquran.autocomplete('translation')
    async def translation_autocomplete_callback(self, interaction: discord.Interaction, current: int):
        closest_matches = [match[0] for match in process.extract(current, translation_list.keys(), scorer=fuzz.partial_ratio, limit=5)]
        choices = [discord.app_commands.Choice(name=match, value=match) for match in closest_matches]
        return choices

    @discord.app_commands.command(name="raquran", description="Retrieve a random verse from the Qur'ān.")
    async def raquran(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        surah = random.randint(1, 114)
        verse = random.randint(1, quranInfo['surah'][surah][1])

        await QuranRequest(interaction=interaction, is_arabic=True, ref=f'{surah}:{verse}').process_request()

    @discord.app_commands.command(name="settranslation",
                                  description="Changes the default Qur'an translation for this server.")
    @discord.app_commands.describe(translation="The translation to use. See /help quran for a list.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.guild_only()
    async def set_translation(self, interaction: discord.Interaction, translation: str):
        await interaction.response.defer(thinking=True, ephemeral=True)

        translation_id = Translation.get_translation_id(translation)
        # this is so when giving success message, it says it sets it to the actual translation instead of user's typos
        # e.g user gives `khatab` but it will set it to `khattab` and tell the user the bot set it to `khattab`
        translation = list(translation_list.keys())[list(translation_list.values()).index(translation_id)]
        await DBHandler.update_guild_translation(interaction.guild_id, translation)
        await interaction.followup.send(f":white_check_mark: **Successfully updated default translation to `{translation}`!**")

    @set_translation.error
    async def set_translation_error(self, interaction: discord.Interaction, error):
        if isinstance(error, CheckFailure):
            await interaction.followup.send("🔒 You need the **Administrator** permission to use this command.")
        if isinstance(error, InvalidTranslation):
            await interaction.followup.send(INVALID_TRANSLATION)
        if isinstance(error, pymysql.err.OperationalError):
            print(error)
            await interaction.followup.send(DATABASE_UNREACHABLE)

    @discord.app_commands.command(name="surah", description="View information about a surah.")
    @discord.app_commands.describe(
        surah="The name or number of the surah, e.g. Al-Baqarah or 2.",
        reveal_order="If you specified a number for the surah, whether the number is the surah's revelation order."
    )
    async def surah(self, interaction: discord.Interaction, surah: str, reveal_order: bool = False):
        await interaction.response.defer(thinking=True)
        surah_num = QuranReference.parse_surah_number(surah)
        surah = Surah(num=surah_num, reveal_order=reveal_order)
        em = discord.Embed(colour=0x048c28)
        em.set_author(name=f'Surah {surah.name} ({surah.translated_name}) |  سورة {surah.arabic_name}', icon_url=ICON)
        em.description = (f'\n• **Surah number**: {surah.num}'
                          f'\n• **Number of verses**: {surah.verses_count}'
                          f'\n• **Revelation location**: {surah.revelation_location}'
                          f'\n• **Revelation order**: {surah.revelation_order} ')
        await interaction.followup.send(embed=em)

    @quran.error
    @aquran.error
    @rquran.error
    @raquran.error
    @surah.error
    async def on_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await respond_to_interaction_error(interaction, error)


async def setup(bot):
    await bot.add_cog(Quran(bot))

