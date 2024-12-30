import re
import textwrap

import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from fuzzywuzzy import process, fuzz

from quran.quran_info import QuranReference, SurahNameTransformer
from utils.database_utils import ServerArabicTafsir
from utils.errors import InvalidArabicTafsir, respond_to_interaction_error
from utils.slash_utils import get_key_from_value
from utils.utils import get_site_source, convert_to_arabic_number

ICON = 'https://lh5.ggpht.com/lRz25mOFrRL42NuHtuSCneXbWV2Gtm7iYZ5eQbuA7JWUC3guWaTaQxNJ7j9rsRMCNAU=w150'

TAFSIR_IDS = {
    'ibnatiyah': 'ibn-atiyah',
    'tabari': 'tabari',
    'fathalbayan': 'fath-albayan',
    'muyassar': 'muyassar',
    'ibnkathir': 'ibn-katheer',
    'shawkani': 'fath-alqadeer',
    'mukhtasar': 'mukhtasar',
    'qurtubi': 'qurtubi',
    'ibnjuzayy': 'altasheel',
    'saadi': 'saadi',
    'baghawi': 'baghawi',
    'jazaeri': 'aysar-altafasir',
    'alusi': 'alaloosi',
    'ibnaljawzi': 'zad-almaseer',
    'razi': 'alrazi',
    'ibnuthaymeen': 'ibn-uthaymeen',
    'mawardi': 'almawirdee',
    'jalalayn': 'jalalayn',
    'ibnalqayyim': 'ibn-alqayyim',
    'baqai': 'nathm-aldurar',
    'iji': 'iejee',
    'baydawi': 'albaydawee',
    'ibnashur': 'ibn-aashoor',
    'nasafi': 'alnasafi',
    'samaani': 'samaani',
    'wahidi': 'alwajeez',
    'makki': 'makki',
    'abuhayyan': 'albahr-almuheet',
    'zamanin': 'zimneen',
    'qasimi': 'mahasin-altaweel',
    'thalabi': 'althalabi',
    'abualsuod': 'abu-alsuod',
    'suyuti': 'aldur-almanthoor',
    'samarqandi': 'samarqandi',
    'zamakhshari': 'kashaf',
    'ibnabihatim': 'ibn-abi-hatim',
    'thaalabi': 'althaalabi',
    'farraa': 'farraa',
    'jassas': 'aljasas',
    'zajjaj': 'zajjaj',
    'ibnalarabi': 'ahkam-ibn-alarabee',
    'adwaa': 'adwaa-albayan',
    'tadabbur': 'tadabbur-wa-amal',
    'mawsoah': 'qiraat-almawsoah',
    'naskh': 'eedah-naskh-mansukh',
    'iraab': 'aliraab-almuyassar',
    'jadwal': 'aljadwal',
    'lubab': 'lubab',
    'aldur': 'aldur-almasoon',
    'mushkil-iraab': 'mujtaba-mushkil-iraab',
    'iraab-aldarweesh': 'iraab-aldarweesh',
    'majaz': 'majaz-alquran',
    'asbab': 'wahidi-asbab',
    'altibyan': 'altibyan-ghreeb',
    'ibnqutaybah': 'ghareeb-ibn-qutaybah',
    'siraaj': 'siraaj-ghareeb',
    'mafateeh': 'mafateeh-alaghanee'
}

TAFSIR_NAMES = {
    'tabari': 'جامع البيان — ابن جرير الطبري (٣١٠ هـ)',
    'razi': 'مفاتيح الغيب — فخر الدين الرازي (٦٠٦ هـ)',
    'zamakhshari': 'الكشاف — الزمخشري (٥٣٨ هـ)',
    'qurtubi': 'الجامع لأحكام القرآن — القرطبي (٦٧١ هـ)',
    'baghawi': 'معالم التنزيل — البغوي (٥١٦ هـ)',
    'baydawi': 'أنوار التنزيل — البيضاوي (٦٨٥ هـ)',
    'jalalayn': 'تفسير الجلالين — المحلّي والسيوطي (٨٦٤، ٩١١ هـ)',
    'alusi': 'روح المعاني — الآلوسي (١٢٧٠ هـ)',
    'ibnashur': 'التحرير والتنوير — ابن عاشور (١٣٩٣ هـ)',
    'ibnuthaymeen': 'تفسير القرآن الكريم — ابن عثيمين (١٤٢١ هـ)',
    'ibnatiyah': 'المحرر الوجيز — ابن عطية (٥٤٦ هـ)',
    'fathalbayan': 'فتح البيان — صديق حسن خان (١٣٠٧ هـ)',
    'muyassar': 'الميسر — مجمع الملك فهد',
    'ibnkathir': 'تفسير القرآن العظيم — ابن كثير (٧٧٤ هـ)',
    'shawkani': 'فتح القدير — الشوكاني (١٢٥٠ هـ)',
    'mukhtasar': 'المختصر — مركز تفسير',
    'ibnjuzayy': 'التسهيل لعلوم التنزيل — ابن جُزَيّ (٧٤١ هـ)',
    'saadi': 'تيسير الكريم الرحمن — السعدي (١٣٧٦ هـ)',
    'jazaeri': 'أيسر التفاسير — أبو بكر الجزائري (١٤٣٩ هـ)',
    'ibnaljawzi': 'زاد المسير — ابن الجوزي (٥٩٧ هـ)',
    'mawardi': 'النكت والعيون — الماوردي (٤٥٠ هـ)',
    'ibnalqayyim': 'تفسير ابن قيّم الجوزيّة — ابن القيم (٧٥١ هـ)',
    'baqai': 'نظم الدرر — البقاعي (٨٨٥ هـ)',
    'iji': 'جامع البيان — الإيجي (٩٠٥ هـ)',
    'nasafi': 'مدارك التنزيل — النسفي (٧١٠ هـ)',
    'samaani': 'تفسير القرآن — السمعاني (٤٨٩ هـ)',
    'wahidi': 'الوجيز — الواحدي (٤٦٨ هـ)',
    'makki': 'الهداية إلى بلوغ النهاية — مكي بن أبي طالب (٤٣٧ هـ)',
    'abuhayyan': 'البحر المحيط — أبو حيان (٧٤٥ هـ)',
    'zamanin': 'تفسير القرآن العزيز — ابن أبي زمنين (٣٩٩ هـ)',
    'qasimi': 'محاسن التأويل — القاسمي (١٣٣٢ هـ)',
    'thalabi': 'الكشف والبيان — الثعلبي (٤٢٧ هـ)',
    'abualsuod': 'إرشاد العقل السليم — أبو السعود (٩٨٢ هـ)',
    'suyuti': 'الدر المنثور — جلال الدين السيوطي (٩١١ هـ)',
    'samarqandi': 'بحر العلوم — السمرقندي (٣٧٣ هـ)',
    'ibnabihatim': 'تفسير القرآن العظيم مسندًا — ابن أبي حاتم الرازي (٣٢٧ هـ)',
    'thaalabi': 'الجواهر الحسان — الثعالبي (٨٧٥ هـ)',
    'farraa': 'معاني القرآن للفراء — أبو زكريا الفراء (٢٠٧ هـ)',
    'jassas': 'أحكام القرآن للجصاص — الجصاص (٣٧٠ هـ)',
    'zajjaj': 'معاني الزجاج — الزجاج (٣١١ هـ)',
    'ibnalarabi': 'أحكام القرآن لابن العربي — ابن العربي (٥٤٣ هـ)',
    'adwaa': 'أضواء البيان — محمد الأمين الشنقيطي (١٣٩٤ هـ)',
    'tadabbur': 'تدبر وعمل — شركة الخبرات الذكية',
    'mawsoah': 'القراءات — الموسوعة القرآنية — إبراهيم الأبياري (١٤١٤ هـ)',
    'naskh': 'ناسخ القرآن ومنسوخه لمكي — مكي بن أبي طالب (٤٣٧ هـ)',
    'iraab': 'الإعراب الميسر — شركة الدار العربية',
    'jadwal': 'الجدول في إعراب القرآن — محمود الصافي (١٣٧٦ هـ)',
    'lubab': 'اللباب في علوم الكتاب — ابن عادل (٨٨٠ هـ)',
    'aldur': 'الدر المصون للسمين الحلبي — السمين الحلبي (٧٥٦ هـ)',
    'mushkil-iraab': 'مجتبى مشكل إعراب القرآن — أحمد بن محمد الخراط',
    'iraab-aldarweesh': 'إعراب القرآن للدرويش — محيي الدين درويش (١٤٠٣ هـ)',
    'majaz': 'مجاز القرآن لمعمر بن المثنى — أبو عبيدة معمر بن المثنى (٢٠٩ هـ)',
    'asbab': 'أسباب النزول للواحدي — الواحدي (٤٦٨ هـ)',
    'altibyan': 'غريب القرآن لابن الهائم — ابن الهائم (٨١٥ هـ)',
    'ibnqutaybah': 'غريب القرآن لابن قتيبة — ابن قتيبة (٢٧٦ هـ)',
    'siraaj': 'غريب القرآن للخضيري — محمد بن عبد العزيز الخضيري',
    'mafateeh': 'مفاتيح الأغاني في القراءات — أبو العلاء الكرماني (بعد ٥٦٣ هـ)'
}


class DefaultArabicTafsir:
    @staticmethod
    async def get_guild_tafsir(guild_id):
        guild_tafsir_handler = ServerArabicTafsir(guild_id)
        tafsir_name = await guild_tafsir_handler.get()

        # Ensure we are not somehow retrieving an invalid tafsir
        if tafsir_name in TAFSIR_NAMES:
            return tafsir_name

        await guild_tafsir_handler.delete()
        return guild_tafsir_handler.default_value


class ArabicTafsirRequest:
    def __init__(self, surah: int, ayah: int, supplied_tafsir: str):
        self.surah = surah
        self.ayah = ayah
        self.id = supplied_tafsir.lower()
        self.website_id = self.get_tafsir_id()
        self.name = self.get_tafsir_name()

        self.url = None
        self.page = 1
        self.pages = None
        self.num_pages = 1

    '''
    Gets the tafsir ID on tafsir.app.
    '''

    def get_tafsir_id(self):
        if self.id in TAFSIR_IDS:
            return TAFSIR_IDS[self.id]

        tafsir = process.extract(self.id, TAFSIR_IDS.keys(), scorer=fuzz.partial_ratio, limit=1)
        if tafsir is None:
            raise InvalidArabicTafsir

        self.id = tafsir[0][0]
        return TAFSIR_IDS[self.id]

    '''
    Gets the tafsir's Arabic name.
    '''

    def get_tafsir_name(self):
        return TAFSIR_NAMES[self.id]

    '''
    Retrieves the raw text from tafsir.app, then processes it.
    '''

    async def fetch_text(self):
        self.url = f'https://tafsir.app/{self.website_id}/{self.surah}/{self.ayah}'
        content = str(await get_site_source(self.url))
        self.process_text(content)

    '''
    Gets, formats and paginates the tafsir text.
    '''

    def process_text(self, content):
        # Parse the website's source and find the tafsir text.
        soup = BeautifulSoup(content, 'html.parser')
        tag = soup.find('div', attrs={'id': 'preloaded'})
        text = tag.get_text().strip()

        # Discord doesn't handle text comprised from both Arabic and non-Arabic text/symbols well, so we need to fix it.
        text = (text.replace('*', '')
                .replace('⁕', '')
                .replace('}', ' ﴾')
                .replace('{', ' ﴿')
                .replace('﴾', '﴾"')
                .replace('﴿', '"﴿')
                .replace('«', '"«')
                .replace('»', '»"')
                .replace('"ayah":', '')
                .replace(']]', ']')
                .replace('[[', '['))

        cleanb = re.compile('\([^)]*\)')
        text = re.sub(cleanb, '', text)

        # Paginate the text, set the embed text to the current page and calculate how many pages were made:
        self.pages = textwrap.wrap(text, 2034, break_long_words=True)
        self.num_pages = len(self.pages)

    def process_footnotes(self):
        text = self.pages[self.page - 1]
        # Now we process the footnotes for the current page.
        # Firstly, we find all the footnotes in the text and add them to the footer text.
        footnotes = re.findall("\[(.*?)\]", text)
        footer = []
        footnote_number = 1
        for footnote in footnotes:
            text = text.replace(footnote, '')
            footnote_number_arabic = convert_to_arabic_number(str(footnote_number))
            footer.append(f'\n({footnote_number_arabic}) {footnote}')
            footnote_number = footnote_number + 1
        footer = ''.join(footer)

        # Now we replace the footnotes in the text with a reference:
        total_footnotes = len(footnotes)
        footnote_number = 1
        for x in range(total_footnotes):
            footnote_number_arabic = convert_to_arabic_number(str(footnote_number))
            text = text.replace('[]', f'({footnote_number_arabic})', 1)
            footnote_number = footnote_number + 1

        return text, footer

    def make_embed(self):
        ref = convert_to_arabic_number(f'{self.surah}:{self.ayah}')
        text, footer = self.process_footnotes()

        text = text.replace('#', '\n')
        text = f'```py\n{text}\n```'

        em = discord.Embed(title=ref, colour=0x467f05, description=text)
        if footer != '':
            em.set_footer(text=f'Page {self.page}/{len(self.pages)} \n____________________________________\n{footer}')
        else:
            em.set_footer(text=f'Page {self.page}/{len(self.pages)}')
        em.set_author(name=f'{self.name}', url=self.url, icon_url=ICON)
        return em


class ArabicTafsir(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send(self, interaction: discord.Interaction, tafsir: ArabicTafsirRequest):
        await tafsir.fetch_text()
        em = tafsir.make_embed()
        if tafsir.num_pages == 1:
            return await interaction.followup.send(embed=em)

        # If there are multiple pages, construct buttons for their navigation.
        tafsir_ui_view = ArabicTafsirNavigator(tafsir, interaction)
        await interaction.followup.send(embed=em, view=tafsir_ui_view)

    group = discord.app_commands.Group(name="atafsir", description="Commands related to arabic tafsir.")

    @group.command(name="get", description="تبعث تفسير أي آية, يوجد 56 تفسير متاح بالعربية")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @discord.app_commands.describe(
        surah="اكتب رقم أو اسم السورة",
        verse_number="اكتب رقم آية",
        tafsir_name="اسم التفسير."
    )
    async def atafsir(self, interaction: discord.Interaction, surah: discord.app_commands.Transform[int, SurahNameTransformer], verse_number: int, tafsir_name: str = None):
        await interaction.response.defer(thinking=True)
        quran_reference = QuranReference(ref=f'{surah}:{verse_number}')

        if tafsir_name is None:
            tafsir_name = await DefaultArabicTafsir.get_guild_tafsir(interaction.guild_id)

        tafsir = ArabicTafsirRequest(quran_reference.surah, quran_reference.ayat_list, tafsir_name)
        await self.send(interaction, tafsir)

    @group.command(name="set_default_atafsir", description="تعيين التفسير العربي الافتراضي")
    @discord.app_commands.describe(tafsir_name="اسم التفسير.")
    @discord.app_commands.checks.has_permissions(administrator=True)
    @discord.app_commands.guild_only()
    async def set_default_atafsir(self, interaction: discord.Interaction, tafsir_name: str):
        await interaction.response.defer(thinking=True, ephemeral=True)

        await ServerArabicTafsir(interaction.guild_id).update(tafsir_name)
        await interaction.followup.send(f":white_check_mark: **Successfully updated the default arabic tafsir to `{TAFSIR_NAMES[tafsir_name]}`!**")

    @atafsir.autocomplete('tafsir_name')
    @set_default_atafsir.autocomplete('tafsir_name')
    async def atafsir_autocomplete_callback(self, interaction: discord.Interaction, current: str):
        closest_matches = [match[0] for match in process.extract(current, TAFSIR_NAMES.values(), scorer=fuzz.token_sort_ratio, limit=5)]
        choices = [discord.app_commands.Choice(name=match, value=get_key_from_value(match, TAFSIR_NAMES)) for match in closest_matches]
        return choices

    @atafsir.error
    @set_default_atafsir.error
    async def on_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await respond_to_interaction_error(interaction, error)


class ArabicTafsirNavigator(discord.ui.View):
    def __init__(self, tafsir: ArabicTafsirRequest, interaction: discord.Interaction):
        super().__init__(timeout=600)
        self.tafsir = tafsir
        self.original_interaction = interaction

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.original_interaction.edit_original_response(view=self, content=":warning: This message has timed out.")

    @discord.ui.button(label='Previous Page', style=discord.ButtonStyle.red, emoji='⬅')
    async def previous_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.tafsir.page > 1:
            self.tafsir.page -= 1
        else:
            self.tafsir.page = self.tafsir.num_pages
        em = self.tafsir.make_embed()
        await interaction.response.edit_message(embed=em)

    @discord.ui.button(label='Next Page', style=discord.ButtonStyle.green, emoji='➡')
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.tafsir.page < self.tafsir.num_pages:
            self.tafsir.page += 1
        else:
            self.tafsir.page = 1
        em = self.tafsir.make_embed()
        await interaction.response.edit_message(embed=em)


async def setup(bot):
    await bot.add_cog(ArabicTafsir(bot))
