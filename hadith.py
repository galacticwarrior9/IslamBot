import aiohttp
import asyncio
import re
import discord
import html2text
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from aiohttp import ClientSession
import textwrap

HADITH_COLLECTION_LIST = ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai',
                    'ibnmajah', 'malik', 'riyadussaliheen', 'adab', 'bulugh',
                    'qudsi', 'nawawi', 'shamail', 'ahmad', 'mishkat']

ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'

ERROR = 'The hadith could not be found on sunnah.com.'

INVALID_INPUT = '**Invalid arguments!** \n\nType `{0}hadith <collection name> <book number>:<hadith number>`' \
                '\n\nExample: `{0}hadith bukhari 1:1`' \
                f'\n\nValid collection names are `{HADITH_COLLECTION_LIST}`'

URL_FORMAT = "https://sunnah.com/ajax/{}/{}/{}"

NOT_AVAILABLE_URDU = 'Only Sahih al-Bukhari and Sunan Abu Dawud are available in Urdu.'


class HadithGrading:
    def __init__(self):
        self.narrator = None
        self.grading = None
        self.sanad = None

        self.book_number = None
        self.hadith_number = None

        self.hadithText = None
        self.bab_name = None
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
            self.url = self.url.format(self.lang, self.collection_name, self.hadith.book_number)
        elif self.isQudsiNawawi():
            self.hadith.hadith_number = int(ref)
            self.collection_name = self.collection_name + '40'
            self.url = self.url.format(self.lang, self.collection_name, 1)

    async def getHadith(self):

        json_lst = await self.get_json()

        if not json_lst:
            return

        lst = [obj for obj in json_lst if \
                obj["hadithNumber"] == self.hadith.hadith_number \
                or obj["ourHadithNumber"] == self.hadith.hadith_number]

        if not lst:
            return

        json = lst[0]

        # Get hadith text.
        self.raw_text = json["hadithText"]

        # Format hadith text.
        self.hadith.hadithText = self.formatHadithText(self.raw_text)

        # Get grading and Urdu-specific details if needed.
        if self.lang == 'urdu':
            self.hadith.grading = json["grade"]
            self.hadith.hadithText = json['hadithSanad'] + self.hadith.hadithText
        else:
            self.hadith.grading = json["grade1"]

        # Get bab name.
        self.hadith.bab_name = json["babName"]
        if self.hadith.bab_name is not None:
            self.hadith.bab_name = self.hadith.bab_name.title()

        # Get hadith book name.
        self.hadith.book_name = json["bookName"]

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

        em = discord.Embed(title=self.hadith.bab_name, colour=0x467f05, description=page)
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
            'mishkat': 'Mishkat al-Masabih',
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
            'mishkat': 'مشكاة المصابيح',
            'qudsi40': 'الأربعون القدسية',
            'nawawi40': 'الأربعون النووية',
        }

        return arabic_hadith_collections[collection_name]

    def isQudsiNawawi(self):
        return self.collection_name in ['qudsi', 'nawawi']


class Hadith(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.session = ClientSession(loop=bot.loop)

    @commands.command(name='hadith')
    async def hadith(self, ctx, collection_name: str = None, ref: str = None, page: int = 1):
        try:
            await self.abstract_hadith(ctx, collection_name, ref, "english", page)
        except:
            await ctx.send(INVALID_INPUT.format(ctx.prefix))

    @commands.command(name='ahadith')
    async def ahadith(self, ctx, collection_name: str = None, ref: str = None, page: int = 1):
        try:
            await self.abstract_hadith(ctx, collection_name, ref, "arabic", page)
        except:
            await ctx.send(INVALID_INPUT.format(f'{ctx.prefix}a'))

    @commands.command(name='uhadith')
    async def uhadith(self, ctx, collection_name: str = None, ref: str = None, page: int = 1):
        if self.isUrduAvailable(collection_name):
            await self.abstract_hadith(ctx, collection_name, ref, "urdu", page)
        else:
            await ctx.send(NOT_AVAILABLE_URDU)

    @hadith.error
    async def on_hadith_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(ctx.prefix))

    @ahadith.error
    async def on_ahadith_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(f'{ctx.prefix}a'))

    @uhadith.error
    async def on_uhadith_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(f'{ctx.prefix}u'))

    @staticmethod
    def isUrduAvailable(collection_name):
        return collection_name.lower() in ['bukhari', 'abudawud']

    async def abstract_hadith(self, channel, collection_name, ref, lang, page):
        spec = HadithSpecifics(collection_name, self.session, lang, ref, page)

        await spec.getHadith()

        if spec.hadith.hadithText:

            em = spec.makeEmbed()
            msg = await channel.send(embed=em)

            if spec.num_pages > 1:
                await msg.add_reaction(emoji='⬅')
                await msg.add_reaction(emoji='➡')

            while True:
                try:
                    reaction, user = await self.bot.wait_for("reaction_add", timeout=120, check=lambda reaction, user:
                    (reaction.emoji == '➡' or reaction.emoji == '⬅')
                     and user != self.bot.user
                     and reaction.message.id == msg.id)

                except asyncio.TimeoutError:
                    await msg.remove_reaction(emoji='➡', member=self.bot.user)
                    await msg.remove_reaction(emoji='⬅', member=self.bot.user)
                    break

                if reaction.emoji == '➡' and spec.page < spec.num_pages:
                    spec.page += 1

                if reaction.emoji == '⬅' and spec.page > 1:
                    spec.page -= 1

                em = spec.makeEmbed()
                await msg.edit(embed=em)

                try:
                    await msg.remove_reaction(reaction.emoji, user)
                # The above fails if the bot doesn't have the "Manage Messages" permission, but it can be safely ignored
                # as it is not essential functionality.
                except discord.ext.commands.errors.CommandInvokeError:
                    pass

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
                await self.abstract_hadith(message.channel, name, ref, "english", 1)
            except:
                return


def setup(bot):
    bot.add_cog(Hadith(bot))
