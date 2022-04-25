import asyncio
import configparser
import random
import re
import textwrap

import aiohttp
import discord
import html2text
from discord.ext import commands
from discord_slash import SlashContext, cog_ext, ButtonStyle
from discord_slash.context import MenuContext
from discord_slash.model import ContextMenuType
from discord_slash.utils import manage_components
from discord_slash.utils.manage_commands import create_option

from utils.slash_utils import generate_choices_from_dict

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['APIs']['sunnah.com']

ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'

HADITH_COLLECTION_LIST = {'bukhari', 'muslim', 'tirmidhi', 'abudawud', 'nasai',
                          'ibnmajah', 'malik', 'riyadussalihin', 'adab', 'bulugh',
                          'nawawi', 'shamail', 'ahmad', 'mishkat', 'hisn'}

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
    'forty': 'Al-Arbaʿīn al-Nawawiyyah',
    'hisn': 'Fortress of the Muslim'
}

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
    'forty': 'الأربعون النووية',
    'hisn': 'حصن المسلم'
}

hadith_collection_aliases = {
    'nawawi': 'forty'
}

INVALID_INPUT = '**Invalid arguments!** \n\nType `{0}hadith <collection name> <book number>:<hadith number>`' \
                '\n\n**Example**: `{0}hadith bukhari 1:1`' \
                '\n\nAlternatively, you can use the sunnah.com hadith number:' \
                '\n\n**Example**: `{0}hadith muslim 1051`' \
                f'\n\nValid collection names are `{HADITH_COLLECTION_LIST}`'

INVALID_COLLECTION = f'**Invalid hadith collection.**\nValid collection names are `{HADITH_COLLECTION_LIST}`'

HEADERS = {"X-API-Key": API_KEY}


class InvalidCollection(commands.CommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


class InvalidHadith(commands.CommandError):
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
            self.hadith_number = ref
            self.type = 'hadith_number'


class HadithSpecifics:
    def __init__(self, collection, ref, lang):
        self.ref = ref
        self.collection = collection
        self.chapter_name = None
        self.lang = lang
        self.grading = None
        self.graded_by = None
        self.hadith_number = None
        self.url = None
        self.text = None
        self.num_pages = None
        self.pages = None
        self.page = 1

    async def fetch_hadith(self):

        if self.ref.type == 'normal':
            self.url = f'https://api.sunnah.com/v1/collections/{self.collection}/books/{self.ref.book_number}/hadiths'

        else:
            self.url = f'https://api.sunnah.com/v1/collections/{self.collection}/hadiths/{self.ref.hadith_number}'

        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(self.url) as resp:
                if resp.status == 200:
                    hadith_list = await resp.json()
                    return self.process_hadith(hadith_list)
                elif resp.status == 404:
                    raise InvalidHadith

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
            self.formatted_collection = self.format_english_collection_name(self.collection)
        else:
            self.formatted_collection = self.format_arabic_collection_name(self.collection)

        em = self.make_embed()
        return em

    def make_embed(self):

        page = self.pages[self.page - 1]
        self.num_pages = len(self.pages)

        em = discord.Embed(colour=0x467f05, description=page)
        if self.chapter_name is not None:
            em.title = self.chapter_name
        em.set_author(name=f'{self.formatted_collection}', icon_url=ICON)

        if self.num_pages > 1:
            footer = f'Page {self.page}/{self.num_pages}'
        else:
            footer = ''

        try:
            footer = f'{footer}\nReference: {self.formatted_collection} {self.hadith_number} (Book {self.ref.book_number}, Hadith {self.ref.hadith_number})'
        except AttributeError:
            footer = f'{footer}\nReference: {self.formatted_collection} {self.hadith_number}'

        if self.grading and self.grading != '' and self.collection not in {'bukhari', 'muslim'}:
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
        return english_hadith_collections[collection_name]

    @staticmethod
    def format_arabic_collection_name(collection_name):
        return arabic_hadith_collections[collection_name]

    @staticmethod
    def format_hadith_text(html):
        h = html2text.HTML2Text()
        h.baseurl = "https://sunnah.com/"
        return h.handle(html.replace('`', 'ʿ').replace("</b>", '').replace("<i>", '*').replace("</i>", '*'))


class HadithCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def abstract_hadith(self, channel, collection_name, ref, lang):

        if collection_name not in HADITH_COLLECTION_LIST:
            raise InvalidCollection

        if collection_name in hadith_collection_aliases:
            collection_name = hadith_collection_aliases[collection_name]

        hadith = HadithSpecifics(collection_name, ref, lang)
        try:
            embed = await hadith.fetch_hadith()
        except InvalidHadith:
            return await channel.send("Sorry, no hadith with this number could be found.")

        if hadith.num_pages == 1:
            return await channel.send(embed=embed)

        # If there are multiple pages, construct buttons for their navigation.
        buttons = [
            manage_components.create_button(style=ButtonStyle.grey, label="Previous Page", emoji="⬅",
                                            custom_id="hadith_previous_page"),
            manage_components.create_button(style=ButtonStyle.green, label="Next Page", emoji="➡",
                                            custom_id="hadith_next_page")
        ]
        action_row = manage_components.create_actionrow(*buttons)
        await channel.send(embed=embed, components=[action_row])

        while True:
            try:
                button_ctx = await manage_components.wait_for_component(self.bot, components=action_row, timeout=600)
                if button_ctx.custom_id == 'hadith_previous_page':
                    if hadith.page > 1:
                        hadith.page -= 1
                    else:
                        hadith.page = hadith.num_pages
                    em = hadith.make_embed()
                    await button_ctx.edit_origin(embed=em)
                elif button_ctx.custom_id == 'hadith_next_page':
                    if hadith.page < hadith.num_pages:
                        hadith.page += 1
                    else:
                        hadith.page = 1
                    em = hadith.make_embed()
                    await button_ctx.edit_origin(embed=em)

            except asyncio.TimeoutError:
                break

    async def _rhadith(self, ctx):
        await self.abstract_hadith(ctx, 'riyadussalihin', Reference(str(random.randint(1, 1896))), 'en')

    @commands.command(name='hadith')
    async def hadith(self, ctx, collection_name: str, ref: Reference):
        await ctx.channel.trigger_typing()
        await self.abstract_hadith(ctx, collection_name.lower(), ref, 'en')

    @commands.command(name='ahadith')
    async def ahadith(self, ctx, collection_name: str, ref: Reference):
        await ctx.channel.trigger_typing()
        await self.abstract_hadith(ctx, collection_name.lower(), ref, 'ar')

    @commands.command(name="rhadith")
    async def rhadith(self, ctx):
        await ctx.channel.trigger_typing()
        await self._rhadith(ctx)

    @hadith.error
    async def hadith_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(ctx.prefix))
        elif isinstance(error, InvalidCollection):
            await ctx.send(INVALID_COLLECTION)

    @ahadith.error
    async def ahadith_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(INVALID_INPUT.format(f'{ctx.prefix}a'))
        elif isinstance(error, InvalidCollection):
            await ctx.send(INVALID_COLLECTION)

    @cog_ext.cog_slash(name="hadith", description="Send hadith in English from sunnah.com.",
                       options=[
                           create_option(
                               name="hadith_collection",
                               description="The name of the hadith collection.",
                               option_type=3,
                               required=True,
                               choices=generate_choices_from_dict(english_hadith_collections)),
                           create_option(
                               name="hadith_number",
                               description="The number of the hadith.",
                               option_type=3,
                               required=True)])
    async def slash_hadith(self, ctx: SlashContext, hadith_collection: str, hadith_number: str):
        await ctx.defer()
        await self.abstract_hadith(ctx, hadith_collection, Reference(hadith_number), 'en')

    @cog_ext.cog_slash(name="ahadith", description="Send hadith in Arabic from sunnah.com.",
                       options=[
                           create_option(
                               name="hadith_collection",
                               description="The name of the hadith collection.",
                               option_type=3,
                               required=True,
                               choices=generate_choices_from_dict(arabic_hadith_collections)),
                           create_option(
                               name="hadith_number",
                               description="The number of the hadith.",
                               option_type=3,
                               required=True)])
    async def slash_ahadith(self, ctx: SlashContext, hadith_collection: str, hadith_number: str):
        await ctx.defer()
        await self.abstract_hadith(ctx, hadith_collection, Reference(hadith_number), 'ar')

    @cog_ext.cog_slash(name="rhadith", description="Send a random hadith in English from sunnah.com.")
    async def slash_rhadith(self, ctx: SlashContext):
        await ctx.defer()
        await self._rhadith(ctx)

    def findURL(self, message):
        urls = re.findall(r'(https?://\S+)', message)
        for link in urls:
            if "sunnah.com/" in link:
                return link

    @cog_ext.cog_context_menu(target=ContextMenuType.MESSAGE, name="Get Hadith Text")
    async def get_hadith_text(self, ctx: MenuContext):
        content = ctx.target_message.content
        url = self.findURL(content)
        if url:
            try:
                meta = url.split("/")
                collection = meta[3]
                if collection in hadith_collection_aliases:
                    collection = hadith_collection_aliases[collection]
                if ":" in collection:  # For urls like http://sunnah.com/bukhari:1
                    if collection[-1] == "/":  # if url ended with /
                        collection = collection[:-1]
                    ref = collection.split(":")[1]  # getting hadith number
                    ref = Reference(ref)
                    collection = collection.split(":")[0]  # getting book name
                else:
                    book = meta[4]
                    try:
                        hadith = meta[5]
                        ref = f"{book}:{hadith}"
                        ref = Reference(ref)
                    except:
                        ref = Reference(
                            book)  # For hadith collections which are a single 'book' long (e.g. 40 Hadith Nawawi)
                await self.abstract_hadith(ctx, collection, ref, "en")
            except InvalidHadith:
                await ctx.send("**There is no valid sunnah.com link here**")
        else:
            await ctx.send("**There is no valid sunnah.com link here**")

    @commands.Cog.listener()
    async def on_message(self, message):
        content = message.content
        url = self.findURL(content)
        if url:
            meta = url.split("/")
            collection = meta[3]
            if collection in hadith_collection_aliases:
                collection = hadith_collection_aliases[collection]
            if ":" in collection:  # For urls like http://sunnah.com/bukhari:1
                if collection[-1] == "/":  # if url ended with /
                    collection = collection[:-1]
                ref = collection.split(":")[1]  # getting hadith number
                ref = Reference(ref)
                collection = collection.split(":")[0]  # getting book name
            else:
                book = meta[4]
                try:
                    hadith = meta[5]
                    ref = f"{book}:{hadith}"
                    ref = Reference(ref)
                except:
                    ref = Reference(
                        book)  # For hadith collections which are a single 'book' long (e.g. 40 Hadith Nawawi)
            await self.abstract_hadith(message.channel, collection, ref, "en")


def setup(bot):
    bot.add_cog(HadithCommands(bot))
