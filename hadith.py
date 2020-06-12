import asyncio
import re
import discord
from utils import get_prefix, get_site_source
from discord.ext import commands
from aiohttp import ClientSession
import textwrap

HADITH_BOOK_LIST = ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai',
                    'ibnmajah', 'malik', 'riyadussaliheen', 'adab', 'bulugh', 'qudsi',
                    'nawawi', 'shamail', 'ahmad']

ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'

ERROR = 'The hadith could not be found on sunnah.com.'

PREFIX = get_prefix()

INVALID_INPUT = f'Invalid arguments! Please do `{PREFIX}hadith (book name)' \
                f'[(book number):(hadith number)|(raw hadith number)]` \n' \
                f'Valid book names are `{HADITH_BOOK_LIST}`'

URL_FORMAT = "https://sunnah.com/{}/{}"


class HadithGrading:
    def __init__(self):
        self.narrator = None
        self.grading = None
        self.arabicGrading = None

        self.book_number = None
        self.hadith_number = None

        self.hadithText = None
        self.arabic_chapter_name = None
        self.english_chapter_name = None
        self.chapter_name = None
        self.book_name = None


class HadithSpecifics:
    def __init__(self, collection_name, session, isEng, ref, page):
        self.page = page
        self.pages = None
        self.num_pages = None
        self.session = session
        self.collection_name = collection_name.lower()
        self.url = URL_FORMAT

        self.raw_text = None
        self.embedTitle = None
        self.readable_collection_name = None
        self.hadith = HadithGrading()

        if isEng:
            self.hadithTextCSSClass = "text_details"
            self.formatBookName = self.formatEnglishCollectionName

            if ':' in ref:
                self.embedAuthorName = '{readable_collection_name} {book_number}:{hadith_number} - {book_name}'
            else:
                self.embedAuthorName = '{readable_collection_name}, Hadith {hadith_number}'

        else:
            self.hadithTextCSSClass = "arabic_hadith_full arabic"
            self.formatBookName = self.formatArabicCollectionName
            self.embedTitle = self.hadith.arabic_chapter_name

            if not self.isQudsiNawawi():
                self.embedAuthorName = '{readable_collection_name} - {book_name}'
            else:
                self.embedAuthorName = '{hadith_number} {readable_collection_name} , حديث'

        self.processRef(ref)

    def processRef(self, ref):
        if ':' in ref:
            (self.hadith.book_number, self.hadith.hadith_number) = ref.split(":")
            self.url = self.url.format(self.collection_name, self.hadith.book_number) + f'/{self.hadith.hadith_number}'
        else:
            self.hadith.hadith_number = ref
            if self.isQudsiNawawi():
                self.collection_name = self.collection_name + '40'
            self.url = self.url.format(self.collection_name, self.hadith.hadith_number)

    async def getHadith(self, isEng = False, depth=0):

        scanner = await get_site_source(self.url)

        # Get hadith text.
        for hadith in scanner.findAll("div", {"class": self.hadithTextCSSClass}, limit=1):
            self.raw_text = hadith.text

        # If the above fails, restart this process using the 'urn' URL format in case we need to use raw hadith numbers.
        if (self.raw_text is None or self.raw_text == "None") and depth < 1:
            self.url = URL_FORMAT.format("urn", self.hadith.hadith_number)
            if isEng:
                await self.getHadith(isEng=True, depth=1)
            else:
                await self.getHadith(isEng=False, depth=1)
            return

        # Format hadith text.
        self.hadith.hadithText = self.formatHadithText(self.raw_text)

        # Get isnad.
        if isEng:
            for tag in scanner.findAll("div", {"class": "hadith_narrated"}, limit=1):
                self.hadith.narrator = tag.text
                self.hadith.hadithText = '**' + self.hadith.narrator.replace('`', "'") + '**' + self.hadith.hadithText

        # Get grading.
        if isEng:
            for tag in scanner.findAll("td", {"class": "english_grade"}, limit=2):
                self.hadith.grading = tag.text

        else:
            for tag in scanner.findAll("td", {"class": "arabic_grade arabic"}, limit=1):
                self.hadith.arabicGrading = tag.text.replace(')', '').replace('(', '')

        # Get chapter name.
        if not isEng:
            for tag in scanner.findAll("div", {"class": "arabicchapter arabic"}, limit=2):
                self.hadith.arabic_chapter_name = tag.text
                self.embedTitle = self.hadith.arabic_chapter_name
        else:
            for tag in scanner.findAll("div", {"class": "englishchapter"}, limit=2):
                self.hadith.english_chapter_name = tag.text
                self.embedTitle = self.hadith.english_chapter_name

        # Get hadith book name.
        if isEng:
            for hadith in scanner.findAll("div", {"class": "book_page_english_name"}, limit=1):
                self.hadith.book_name = hadith.text.strip()
        else:
            for hadith in scanner.findAll("div", {"class": "book_page_arabic_name arabic"}, limit=1):
                self.hadith.book_name = hadith.text.strip()

        self.readable_collection_name = self.formatBookName(self.collection_name)

        self.pages = textwrap.wrap(self.hadith.hadithText, 1024)

    def makeEmbed(self):
        authorName = self.embedAuthorName \
            .format(readable_collection_name=self.readable_collection_name,
                    book_number=self.hadith.book_number,
                    hadith_number=self.hadith.hadith_number,
                    book_name=self.hadith.book_name)

        page = self.pages[self.page - 1]
        self.num_pages = len(self.pages)

        em = discord.Embed(title=self.embedTitle, colour=0x467f05, description=page)
        em.set_author(name=authorName, icon_url=ICON)

        if self.num_pages > self.page:
            footer = f'Page {self.page}/{self.num_pages}'
        else:
            footer = ''

        if self.hadith.grading:
            em.set_footer(text=footer + f'\nGrading{self.hadith.grading}')

        elif self.hadith.arabicGrading:
            em.set_footer(text=footer + f'\n{self.hadith.arabicGrading}')

        elif self.num_pages > self.page:
            em.set_footer(text=f'{footer}')

        return em

    @staticmethod
    def formatHadithText(text):
        txt = str(text)\
            .replace('`', 'ʿ') \
            .replace('\n', '')
        return re.sub('\s+', ' ', txt)

    @staticmethod
    def formatEnglishCollectionName(collection_name):
        english_hadith_collections = {
            'ahmad': 'Musnad Ahmad ibn Hanbal',
            'bukhari': 'Sahīh al-Bukhārī',
            'muslim': 'Sahīh Muslim',
            'tirmidhi': 'Jamiʿ at-Tirmidhī',
            'abudawud': 'Sunan Abī Dāwūd',
            'nasai': "Sunan an-Nāsaʿī",
            'ibnmajah': 'Sunan Ibn Mājah',
            'malik': 'Muwatta Mālik',
            'riyadussaliheen': 'Riyadh as-Salihīn',
            'adab': "Al-Adab al-Mufrad",
            'bulugh': 'Bulugh al-Maram',
            'shamail': "Shamā'il Muhammadiyyah",
            'qudsi40': 'Al-Arbaʿīn al-Qudsiyyah',
            'nawawi40': 'Al-Arbaʿīn al-Nawawiyyah'
        }

        return english_hadith_collections[collection_name]

    @staticmethod
    def formatArabicCollectionName(collection_name):
        arabic_hadith_collections = {
            'ahmad': 'مسند أحمد بن حنبل',
            'bukhari': 'صحيح البخاري',
            'muslim': 'صحيح مسلم',
            'tirmidhi': 'جامع الترمذي',
            'abudawud': 'سنن أبي داود',
            'nasai': "سنن النسائي",
            'ibnmajah': 'سنن ابن ماجه',
            'malik': 'موطأ مالك',
            'riyadussaliheen': 'رياض الصالحين',
            'adab': "الأدب المفرد",
            'bulugh': 'بلوغ المرام',
            'shamail': 'الشمائل المحمدية',
            'qudsi40': 'الأربعون القدسية',
            'nawawi40': 'الأربعون النووية'
        }

        return arabic_hadith_collections[collection_name]

    def isQudsiNawawi(self):
        return self.collection_name in ['qudsi', 'nawawi', 'qudsi40', 'nawawi40']


class Hadith(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

    @commands.command(name='hadith')
    async def hadith(self, ctx, collection_name: str = None, ref: str = None, page: int = 1):
        await self.abstract_hadith(ctx.channel, collection_name, ref, True, page)

    @commands.command(name='ahadith')
    async def ahadith(self, ctx, collection_name: str = None, ref: str = None, page: int = 1):
        await self.abstract_hadith(ctx, collection_name, ref, False, page)

    async def abstract_hadith(self, channel, collection_name, ref, isEng, page):
        if collection_name in HADITH_BOOK_LIST:
            spec = HadithSpecifics(collection_name, self.session, isEng, ref, page)
        else:
            await channel.send(INVALID_INPUT)
            return
        if isEng:
            await spec.getHadith(isEng=True)
        else:
            await spec.getHadith(isEng=False)

        if spec.hadith.hadithText is not None and spec.hadith.hadithText != "None":

            em = spec.makeEmbed()
            msg = await channel.send(embed=em)

            if spec.num_pages > 1:
                await msg.add_reaction(emoji='⬅')
                await msg.add_reaction(emoji='➡')

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=120,
                                                            check=lambda reaction, user: (reaction.emoji == '➡' or reaction.emoji == '⬅')
                                                            and user != self.bot.user and reaction.message.id == msg.id)
                except asyncio.TimeoutError:
                    await msg.remove_reaction(emoji='➡', member=self.bot.user)
                    await msg.remove_reaction(emoji='⬅', member=self.bot.user)
                    break

                await msg.remove_reaction(reaction.emoji, user)

                if reaction.emoji == '➡' and spec.page < spec.num_pages:
                    spec.page += 1

                if reaction.emoji == '⬅' and spec.page > 1:
                    spec.page -= 1

                em = spec.makeEmbed()
                await msg.edit(embed=em)

        else:
            await channel.send(ERROR)

    def findURL(self, message):
        urls = re.findall(r'(https?://\S+)', message)
        for link in urls:
            if "sunnah.com/" in link:
                return link

    @commands.Cog.listener()
    async def on_message(self, message):
        content = message.content
        url = self.findURL(content)
        if url is not None:
            try:
                meta = url.split("/")
                name = meta[3]
                book = meta[4]
                hadith = meta[5]
                ref = f"{book}:{hadith}"
                await self.abstract_hadith(message.channel, name, ref, True, 1)
            except:
                return


def setup(bot):
    bot.add_cog(Hadith(bot))
