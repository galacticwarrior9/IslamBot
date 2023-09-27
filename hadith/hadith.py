import configparser
import random
import re
import textwrap

import aiohttp
import discord
import html2text
from discord.ext import commands

from utils import utils
from utils.slash_utils import generate_choices_from_dict

config = configparser.ConfigParser()
config.read('config.ini')
API_KEY = config['APIs']['sunnah.com']

ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'

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

HEADERS = {"X-API-Key": API_KEY}

CLEAN_ARABIC_REGEXP = re.compile(r'(\[+?[^\[]+?\])')


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

        self.text = self.format_hadith_text(self.text, self.lang)
        
        if self.lang == 'ar' and self.collection == "forty":  # if ahadith and is nawawi collection
            sunnah_links = []
            for links in self.text.split("،"):
                url = utils.find_url('sunnah.com/', links)  # find sunnah.com links in hadith text
                sunnah_links.append(url)

            sunnah_links  = [link.replace(").", "").replace(")", "") for link in sunnah_links if link is not None]

            for link in sunnah_links:
                self.text = self.text.replace(f"[]({link})", "")  # clean the text from these links and brackets

            for link in sunnah_links:
                author = link.split("/")[-3]  # author is the 3rd last item i.e ["sunnah.com", "bukhari", "1", "1"]
                self.text += f"[{arabic_hadith_collections[author]}]({link})، "  # add the sunnah.com links back to the end of the hadith text

            self.text = self.text[:-2]  # remove the extra comma and space from above line from the last word

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
    def format_hadith_text(html, lang):
        if lang != "en":
            html =  re.sub(CLEAN_ARABIC_REGEXP, '', html)
        h = html2text.HTML2Text()
        h.baseurl = "https://sunnah.com/"
        return h.handle(html.replace('`', 'ʿ').replace("<b>", '').replace("</b>", '').replace("<i>", '*').replace("</i>", '*'))


class HadithCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx_menu = discord.app_commands.ContextMenu(
            name='Get Hadith from URL',
            callback=self.get_hadith_text
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    async def abstract_hadith(self, interaction: discord.Interaction, collection_name, ref, lang):
        hadith = HadithSpecifics(collection_name, ref, lang)
        try:
            embed = await hadith.fetch_hadith()
        except InvalidHadith:
            return await interaction.response.send_message("Sorry, no hadith with this number could be found.")

        if hadith.num_pages == 1:
            return await interaction.response.send_message(embed=embed)

        # If there are multiple pages, construct buttons for their navigation.
        hadith_ui_view = HadithNavigator(hadith, interaction)
        await interaction.response.send_message(embed=embed, view=hadith_ui_view)

    async def _rhadith(self, interaction: discord.Interaction):
        await self.abstract_hadith(interaction, 'riyadussalihin', Reference(str(random.randint(1, 1896))), 'en')

    async def _rahadith(self, interaction: discord.Interaction):
        await self.abstract_hadith(interaction, 'riyadussalihin', Reference(str(random.randint(1, 1896))), 'ar')

    @discord.app_commands.command(name="hadith", description="Send a hadith in English from sunnah.com.")
    @discord.app_commands.choices(hadith_collection=generate_choices_from_dict(english_hadith_collections))
    @discord.app_commands.describe(
        hadith_collection="The name of the hadith collection.",
        hadith_number="The number of the hadith."
    )
    async def hadith(self, interaction: discord.Interaction, hadith_collection: str, hadith_number: str):
        await self.abstract_hadith(interaction, hadith_collection, Reference(hadith_number), 'en')

    @discord.app_commands.command(name="ahadith", description="Send a hadith in Arabic from sunnah.com.")
    @discord.app_commands.choices(hadith_collection=generate_choices_from_dict(arabic_hadith_collections))
    @discord.app_commands.describe(
        hadith_collection="The name of the hadith collection.",
        hadith_number="The number of the hadith."
    )
    async def ahadith(self, interaction: discord.Interaction, hadith_collection: str, hadith_number: str):
        await self.abstract_hadith(interaction, hadith_collection, Reference(hadith_number), 'ar')

    @discord.app_commands.command(name="rhadith", description="Send a random hadith in English from sunnah.com.")
    async def rhadith(self, interaction: discord.Interaction):
        await self._rhadith(interaction)

    @discord.app_commands.command(name="rahadith", description="Send a random hadith in Arabic from sunnah.com.")
    async def slash_rahadith(self, interaction: discord.Interaction):
        await self._rahadith(interaction)

    # See https://github.com/Rapptz/discord.py/issues/7823#issuecomment-1086830458 for why we can't use the
    # context menu annotation in cogs.
    async def get_hadith_text(self, interaction: discord.Interaction, message: discord.Message):
        url = utils.find_url('sunnah.com/', message.content)
        if url:
            try:
                meta = url.split("/")
                collection = meta[3]
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
                await self.abstract_hadith(interaction, collection, ref, "en")
            except InvalidHadith:
                await interaction.response.send_message("Could not find a valid `sunnah.com` link in this message.", ephemeral=True)
        else:
            await interaction.response.send_message("Could not find a valid `sunnah.com` link in this message.", ephemeral=True)


class HadithNavigator(discord.ui.View):
    def __init__(self, hadith: HadithSpecifics, interaction: discord.Interaction):
        super().__init__(timeout=300)
        self.hadith = hadith
        self.original_interaction = interaction

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.original_interaction.edit_original_response(view=self, content=":warning: This message has timed out.")

    @discord.ui.button(label='Previous Page', style=discord.ButtonStyle.grey, emoji='⬅')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hadith.page > 1:
            self.hadith.page -= 1
        else:
            self.hadith.page = self.hadith.num_pages

        em = self.hadith.make_embed()
        await interaction.response.edit_message(embed=em)

    @discord.ui.button(label='Next Page', style=discord.ButtonStyle.green, emoji='➡')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.hadith.page < self.hadith.num_pages:
            self.hadith.page += 1
        else:
            self.hadith.page = 1
        em = self.hadith.make_embed()
        await interaction.response.edit_message(embed=em)


async def setup(bot):
    await bot.add_cog(HadithCommands(bot))
