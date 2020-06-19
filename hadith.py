import aiohttp
import asyncio
import re
import discord
import html2text
from utils import get_prefix
from discord.ext import commands
from aiohttp import ClientSession
import textwrap

HADITH_BOOK_LIST = ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai',
                    'ibnmajah', 'malik', 'riyadussaliheen', 'adab', 'bulugh',
                    'qudsi', 'nawawi', 'shamail', 'ahmad']

ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'

ERROR = 'The hadith could not be found on sunnah.com.'

PREFIX = get_prefix()

INVALID_INPUT = f'Invalid arguments! Please do `{PREFIX}hadith (book name)' \
                f'[(book number):(hadith number)|(raw hadith number)]` \n' \
                f'Valid book names are `{HADITH_BOOK_LIST}`'

URL_FORMAT = "https://sunnah.com/ajax/{}/{}/{}"


class HadithGrading:
    def __init__(self):
        self.narrator = None
        self.grading = None

        self.book_number = None
        self.hadith_number = None

        self.hadithText = None
        self.chapter_name = None
        self.book_name = None


class HadithSpecifics:
    def __init__(self, collection_name, session, lang, ref, page):
        self.page = page
        self.pages = None
        self.num_pages = None
        self.session = session
        self.collection_name = collection_name.lower()
        self.url = URL_FORMAT
        self.lang = lang

        self.raw_text = None
        self.embedTitle = None
        self.readable_collection_name = None
        self.hadith = HadithGrading()

        if lang == "english":
            self.formatBookName = self.formatEnglishCollectionName

            if ':' in ref:
                self.embedAuthorName = '{readable_collection_name} {book_number}:{hadith_number} - {book_name}'
            else:
                self.embedAuthorName = \
                        '{readable_collection_name}, Hadith {hadith_number}'

        else:
            self.formatBookName = self.formatArabicCollectionName

            if not self.isQudsiNawawi():
                self.embedAuthorName = \
                        '{readable_collection_name} - {book_name}'
            else:
                self.embedAuthorName = \
                        '{hadith_number} {readable_collection_name} , حديث'

        self.processRef(ref)

    def processRef(self, ref):
        if ':' in ref:
            self.hadith.book_number, self.hadith.hadith_number = \
                    [int(arg) for arg in ref.split(':')]
            self.url = self.url.format(self.lang, self.collection_name, \
                    self.hadith.book_number)
        elif self.isQudsiNawawi():
            self.hadith.hadith_number = int(ref)
            self.collection_name = self.collection_name + '40'
            self.url = self.url.format(self.lang, self.collection_name, 1)

    async def getHadith(self):

        json_lst = await self.get_json()

        if not json_lst or len(json_lst) < self.hadith.hadith_number \
                or self.hadith.hadith_number <= 0:
            return

        json = json_lst[self.hadith.hadith_number - 1]

        # Get hadith text.
        self.raw_text = json["hadithText"]

        # Format hadith text.
        self.hadith.hadithText = self.formatHadithText(self.raw_text)

        # Get grading.
        self.hadith.grading = json["grade1"]

        # Get hadith book name.
        self.hadith.book_name = json["bookName"]

        self.readable_collection_name = self.formatBookName( \
                self.collection_name)

        self.pages = textwrap.wrap(self.hadith.hadithText, 1024)

    def makeEmbed(self):
        authorName = self.embedAuthorName \
            .format(readable_collection_name=self.readable_collection_name,
                    book_number=self.hadith.book_number,
                    hadith_number=self.hadith.hadith_number,
                    book_name=self.hadith.book_name)

        page = self.pages[self.page - 1]
        self.num_pages = len(self.pages)

        em = discord.Embed(title=self.embedTitle, colour=0x467f05, \
                description=page)
        em.set_author(name=authorName, icon_url=ICON)

        if self.num_pages > self.page:
            footer = f'Page {self.page}/{self.num_pages}'
        else:
            footer = ''

        if self.hadith.grading:
            em.set_footer(text=footer + "\n" \
                    + ("Grading: " if self.lang == "english" else "") \
                    + f'{self.hadith.grading}')

        elif self.num_pages > self.page:
            em.set_footer(text=f'{footer}')

        return em

    async def get_json(self) -> dict:
        async with aiohttp.ClientSession() as session:
            async with session.get(self.url) as resp:
                return await resp.json(content_type=None)

    @staticmethod
    def formatHadithText(html):
        h = html2text.HTML2Text()
        h.baseurl = "https://sunnah.com/"
        return h.handle(html.replace('`', 'ʿ').replace("</b>", ''))

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
        return self.collection_name in ['qudsi', 'nawawi']


class Hadith(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

    @commands.command(name='hadith')
    async def hadith(self, ctx, collection_name: str = None, ref: str = None, \
            page: int = 1):
        await self.abstract_hadith(ctx, collection_name, ref, "english", page)

    @commands.command(name='ahadith')
    async def ahadith(self, ctx, collection_name: str = None, ref: str = None, \
            page: int = 1):
        await self.abstract_hadith(ctx, collection_name, ref, "arabic", page)

    async def abstract_hadith(self, channel, collection_name, ref, lang, page):
        if collection_name in HADITH_BOOK_LIST:
            spec = HadithSpecifics(collection_name, self.session, lang, ref,
                    page)
        else:
            await channel.send(INVALID_INPUT)
            return

        await spec.getHadith()

        if spec.hadith.hadithText:

            em = spec.makeEmbed()
            msg = await channel.send(embed=em)

            if spec.num_pages > 1:
                await msg.add_reaction(emoji='⬅')
                await msg.add_reaction(emoji='➡')

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", \
                            timeout=120, check=lambda reaction, \
                            user: (reaction.emoji == '➡' \
                                    or reaction.emoji == '⬅') \
                                    and user != self.bot.user \
                                    and reaction.message.id == msg.id)

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
        if url:
            try:
                meta = url.split("/")
                name = meta[3]
                book = meta[4]
                hadith = meta[5]
                ref = f"{book}:{hadith}"
                await self.abstract_hadith(message.channel, name, ref, \
                        "english", 1)
            except:
                return


def setup(bot):
    bot.add_cog(Hadith(bot))
