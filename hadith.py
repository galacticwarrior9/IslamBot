from discord.ext import commands
import aiohttp
import asyncio
import configparser
import discord
import html2text
import re
import textwrap

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['APIs']['sunnah.com']

ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'

HADITH_COLLECTION_LIST = ['bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai',
                    'ibnmajah', 'malik', 'riyadussalihin', 'adab', 'bulugh',
                    'qudsi', 'nawawi', 'shamail', 'ahmad', 'mishkat', 'hisn']

INVALID_INPUT = '**Invalid arguments!** \n\nType `{0}hadith <collection name> <book number>:<hadith number>`' \
                '\n\n**Example**: `{0}hadith bukhari 1:1`' \
                '\n\nAlternatively, you can use the sunnah.com hadith number:' \
                '\n\n**Example**: `{0}hadith muslim 1051`' \
                f'\n\nValid collection names are `{HADITH_COLLECTION_LIST}`'

INVALID_COLLECTION = f'**Invalid hadith collection.**\nValid collection names are `{HADITH_COLLECTION_LIST}`'


class InvalidCollection(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class Reference:
    def __init__(self, ref):
        self.process_ref(ref)

    def process_ref(self, ref):
        if ':' in ref:
            self.book_number, self.hadith_number = ref.split(':')
            self.type = 'normal'
        else:
            self.hadith_number = int(ref)
            self.type = 'hadith_number_only'


class HadithSpecifics:
    def __init__(self, collection, ref, lang):
        self.ref = ref
        self.collection = collection
        self.chapter_name = None
        self.lang = lang
        self.grading = None
        self.graded_by = None
        self.hadith_number = None
        self.text = None
        self.num_pages = None
        self.pages = None
        self.page = 1

    async def fetch_hadith(self):

        if self.ref.type == 'normal':
            url = f'https://api.sunnah.com/v1/collections/{self.collection}/books/{self.ref.book_number}/hadiths'

        else:
            url = f'https://api.sunnah.com/v1/collections/{self.collection}/hadiths/{self.ref.hadith_number}'

        headers = {"X-API-Key": API_KEY}
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    hadith_list = await resp.json()
                    return self.process_hadith(hadith_list)

    def process_hadith(self, hadith_list):

        if self.ref.type == 'normal':
            hadith_list = [hadith for hadith in hadith_list['data']]
            hadith = hadith_list[int(self.ref.hadith_number) - 1]
            self.hadith_number = hadith['hadithNumber']

            if self.lang == 'en':
                self.text = hadith["hadith"][0]["body"]
                self.chapter_name = hadith["hadith"][0]["chapterTitle"]
                try:
                    self.grading = hadith["hadith"][0]["grades"][0]["grade"]
                    self.graded_by = hadith["hadith"][0]["grades"][0]["graded_by"]
                except IndexError:
                    pass

            else:
                self.text = hadith["hadith"][1]["body"]
                self.chapter_name = hadith["hadith"][1]["chapterTitle"]
                try:
                    self.grading = hadith["hadith"][1]["grades"][0]["grade"]
                    self.graded_by = hadith["hadith"][1]["grades"][0]["graded_by"]
                except IndexError:
                    pass

        else:
            self.hadith_number = hadith_list['hadithNumber']
            if self.lang == 'en':
                self.text = hadith_list['hadith'][0]['body']
                self.chapter_name = hadith_list['hadith'][0]['chapterTitle']
                try:
                    self.grading = hadith_list['hadith'][0]["grades"][0]["grade"]
                    self.graded_by = hadith_list['hadith'][0]["grades"][0]["graded_by"]
                except IndexError:
                    pass

            else:
                self.text = hadith_list['hadith'][1]['body']
                self.chapter_name = hadith_list['hadith'][1]['chapterTitle']
                try:
                    self.grading = hadith_list['hadith'][1]["grades"][0]["grade"]
                    self.graded_by = hadith_list['hadith'][1]["grades"][0]["graded_by"]
                except IndexError:
                    pass

        self.text = self.format_hadith_text(self.text)
        self.pages = textwrap.wrap(self.text, 1024)

        if self.lang == 'en':
            self.collection = self.format_english_collection_name(self.collection)
        else:
            self.collection = self.format_arabic_collection_name(self.collection)

        em = self.make_embed()
        return em

    def make_embed(self):

        page = self.pages[self.page - 1]
        self.num_pages = len(self.pages)

        em = discord.Embed(title=self.chapter_name, colour=0x467f05, description=page)
        em.set_author(name=f'{self.collection}', icon_url=ICON)

        if self.num_pages > 1:
            footer = f'Page {self.page}/{self.num_pages}'
        else:
            footer = ''

        if self.ref.book_number:
            footer = footer + f'\nReference: {self.collection} {self.hadith_number} (Book {self.ref.book_number}, Hadith {self.ref.hadith_number})'
        else:
            footer = footer + f'\nReference: {self.collection} {self.hadith_number}'

        if self.grading and self.grading != '':
            if self.lang == 'en':
                footer = footer + f'\nGrading: {self.grading}'
            else:
                footer = footer + f'\n{self.grading}'
            if self.graded_by and self.graded_by != '':
                footer = footer + f' - {self.graded_by}'

        em.set_footer(text=footer)

        return em

    @staticmethod
    def format_english_collection_name(collection_name):
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

        return english_hadith_collections[collection_name]

    @staticmethod
    def format_arabic_collection_name(collection_name):
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

        return arabic_hadith_collections[collection_name]

    @staticmethod
    def format_hadith_text(html):
        h = html2text.HTML2Text()
        h.baseurl = "https://sunnah.com/"
        return h.handle(html.replace('`', 'ʿ').replace("</b>", '').replace("<i>", '*').replace("</i>", '*'))


class HadithCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.dua_list = None

    async def abstract_hadith(self, channel, collection_name, ref, lang):

        if collection_name not in HADITH_COLLECTION_LIST:
            raise InvalidCollection

        if collection_name == 'qudsi' or collection_name == 'nawawi':
            collection_name = collection_name + '40'

        hadith = HadithSpecifics(collection_name, ref, lang)
        embed = await hadith.fetch_hadith()
        msg = await channel.send(embed=embed)

        if hadith.num_pages > 1:
            await msg.add_reaction(emoji='⬅')
            await msg.add_reaction(emoji='➡')

        await msg.add_reaction(emoji='❎')

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=180, check=lambda reaction, user:
                (reaction.emoji == '➡' or reaction.emoji == '⬅' or reaction.emoji == '❎')
                and user != self.bot.user
                and reaction.message.id == msg.id)

            except asyncio.TimeoutError:
                await msg.remove_reaction(emoji='➡', member=self.bot.user)
                await msg.remove_reaction(emoji='⬅', member=self.bot.user)
                await msg.remove_reaction(emoji='❎', member=self.bot.user)
                break

            if reaction.emoji == '➡':
                if hadith.page < hadith.num_pages:
                    hadith.page += 1
                else:
                    hadith.page = 1

            if reaction.emoji == '⬅':
                if hadith.page > 1:
                    hadith.page -= 1
                else:
                    hadith.page = hadith.num_pages

            if reaction.emoji == '❎':
                return await msg.delete()

            em = hadith.make_embed()
            await msg.edit(embed=em)

            try:
                await msg.remove_reaction(reaction.emoji, user)

            # The above fails if the bot doesn't have the "Manage Messages" permission, but it can be safely ignored
            # as it is not essential functionality.
            except discord.ext.commands.errors.CommandInvokeError:
                pass

    @commands.command(name='hadith')
    async def hadith(self, ctx, collection_name: str, ref: Reference):
        await self.abstract_hadith(ctx.channel, collection_name, ref, 'en')

    @commands.command(name='ahadith')
    async def ahadith(self, ctx, collection_name: str, ref: Reference):
        await self.abstract_hadith(ctx.channel, collection_name, ref, 'ar')

    @hadith.error
    async def hadith_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(ctx.prefix))
        elif isinstance(error, InvalidCollection):
            await ctx.send(INVALID_COLLECTION)
        else:
            await ctx.send("Hadith could not be found.")

    @ahadith.error
    async def ahadith_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(f'{ctx.prefix}a'))
        elif isinstance(error, InvalidCollection):
            await ctx.send(INVALID_COLLECTION)
        else:
            await ctx.send("Hadith could not be found.")

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
            meta = url.split("/")
            collection = meta[3]
            book = meta[4]
            if collection == "nawawi40" or collection == "qudsi40":
                collection = collection[:-2]
            try:
                hadith = meta[5]
                ref = f"{book}:{hadith}"
                ref = Reference(ref)
            except:
                ref = Reference(book)  # For hadith collections which are a single 'book' long (e.g. 40 Hadith Nawawi)
            await self.abstract_hadith(message.channel, collection, ref, "en")


def setup(bot):
    bot.add_cog(HadithCommands(bot))


