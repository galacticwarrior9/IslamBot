import configparser
import textwrap

import aiohttp
import discord
import html2text

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['APIs']['sunnah.com']

ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'


class InvalidCollection(Exception):
    pass


class NoResponse(Exception):
    pass


class Hadith:
    def __init__(self, collection_name: str, hadith_number: str, is_arabic: bool):
        self.is_arabic = is_arabic
        self.collection_name = collection_name
        self.formatted_collection_name = self.get_formatted_collection_name()
        self.hadith_number = hadith_number

        self.pages = None
        self.page = 1

        self.text = None
        self.chapter_name = None
        self.grading = None
        self.graded_by = None

    def format_english_collection_name(self):
        english_hadith_collections = {
            'ahmad': 'Musnad Ahmad ibn Hanbal',
            'bukhari': 'Sahīh al-Bukhārī',
            'muslim': 'Sahīh Muslim',
            'tirmidhi': 'Jamiʿ at-Tirmidhī',
            'abudawud': 'Sunan Abī Dāwūd',
            'nasai': "Sunan an-Nāsaʿī",
            'ibnmajah': 'Sunan Ibn Mājah',
            'malik': 'Muwatta Mālik',
            'riyadussalihin': 'Riyadh as-Salihīn',
            'adab': "Al-Adab al-Mufrad",
            'bulugh': 'Bulugh al-Maram',
            'shamail': "Shamā'il Muhammadiyyah",
            'mishkat': 'Mishkat al-Masabih',
            'qudsi40': 'Al-Arbaʿīn al-Qudsiyyah',
            'nawawi40': 'Al-Arbaʿīn al-Nawawiyyah',
            'hisn': 'Fortress of the Muslim (Hisn al-Muslim)'
        }

        if self.collection_name in english_hadith_collections:
            return english_hadith_collections[self.collection_name]
        else:
            print("error " + self.collection_name)
            raise InvalidCollection

    def format_arabic_collection_name(self):
        arabic_hadith_collections = {
            'ahmad': 'مسند أحمد بن حنبل',
            'bukhari': 'صحيح البخاري',
            'muslim': 'صحيح مسلم',
            'tirmidhi': 'جامع الترمذي',
            'abudawud': 'سنن أبي داود',
            'nasai': "سنن النسائي",
            'ibnmajah': 'سنن ابن ماجه',
            'malik': 'موطأ مالك',
            'riyadussalihin': 'رياض الصالحين',
            'adab': "الأدب المفرد",
            'bulugh': 'بلوغ المرام',
            'shamail': 'الشمائل المحمدية',
            'mishkat': 'مشكاة المصابيح',
            'qudsi40': 'الأربعون القدسية',
            'nawawi40': 'الأربعون النووية',
            'hisn': 'حصن المسلم'
        }

        if self.collection_name in arabic_hadith_collections:
            return arabic_hadith_collections[self.collection_name]
        else:
            raise InvalidCollection

    def get_formatted_collection_name(self):
        if self.is_arabic:
            return self.format_arabic_collection_name()
        else:
            return self.format_english_collection_name()

    async def fetch(self):
        url = f'https://api.sunnah.com/v1/collections/{self.collection_name}/hadiths/{self.hadith_number}'
        headers = {"X-API-Key": API_KEY}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    hadith_response = await resp.json()
                    self.process_hadith(hadith_response)
                else:
                    raise NoResponse

    @staticmethod
    def format_hadith_text(html):
        h = html2text.HTML2Text()
        h.baseurl = "https://sunnah.com/"
        return h.handle(html.replace('`', 'ʿ').replace("</b>", '').replace("<i>", '*').replace("</i>", '*'))

    def process_hadith(self, response):
        if self.is_arabic:
            lang_code = 'ar'
        else:
            lang_code = 'en'
        hadith = None
        for possibleHadith in response['hadith']:
            if possibleHadith['lang'] == lang_code:
                hadith = possibleHadith

        self.pages = textwrap.wrap(self.format_hadith_text(hadith['body']), 1024)
        self.chapter_name = hadith['chapterTitle']

        try:
            self.grading = hadith["grades"][0]["grade"]
            self.graded_by = hadith["grades"][0]["graded_by"]
        except IndexError:
            pass

    async def get_embed(self):
        # Don't fetch the hadith text if we have already done so:
        if self.pages is None:
            await self.fetch()

        page = self.pages[self.page - 1]

        em = discord.Embed(title=self.chapter_name, colour=0x467f05, description=page)
        em.set_author(name=f'{self.formatted_collection_name}', icon_url=ICON)

        footer = f'Reference: {self.formatted_collection_name} {self.hadith_number}'
        if self.grading is not None:
            footer = footer + f'\nGrading: {self.grading}'
            if self.graded_by is not None:
                footer = footer + f' ({self.graded_by})'

        em.set_footer(text=footer)
        return em
