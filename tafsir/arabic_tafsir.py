import asyncio
import re
import textwrap

import discord
from bs4 import BeautifulSoup
from discord.ext import commands
from discord_slash import cog_ext, SlashContext, ButtonStyle
from discord_slash.utils import manage_components
from discord_slash.utils.manage_commands import create_option

from quran.quran_info import QuranReference
from utils.slash_utils import generate_choices_from_list
from utils.utils import get_site_source, convert_to_arabic_number

ICON = 'https://lh5.ggpht.com/lRz25mOFrRL42NuHtuSCneXbWV2Gtm7iYZ5eQbuA7JWUC3guWaTaQxNJ7j9rsRMCNAU=w150'


class InvalidTafsir(Exception):
    pass


ids = {
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

names = {
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


class ArabicTafsir:
    def __init__(self, surah: int, ayah: int, supplied_tafsir: str):
        self.surah = surah
        self.ayah = ayah
        self.id = supplied_tafsir.lower()
        self.website_id = self.get_tafsir_id()
        self.name = self.get_tafsir_name()

        self.url = None
        self.page = 1
        self.pages = None

    '''
    Gets the tafsir ID on tafsir.app.
    '''
    def get_tafsir_id(self):
        if self.id in ids:
            return ids[self.id]
        else:
            raise InvalidTafsir
    '''
    Gets the tafsir's Arabic name.
    '''
    def get_tafsir_name(self):
        return names[self.id]

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


class Tafsir(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def send(self, ctx, tafsir):
        await tafsir.fetch_text()
        em = tafsir.make_embed()
        num_pages = len(tafsir.pages)
        if num_pages == 1:
            return await ctx.send(embed=em)

        # If there are multiple pages, construct buttons for their navigation.
        buttons = [
            manage_components.create_button(style=ButtonStyle.green, label="الصفحة التالية", emoji="⬅",
                                            custom_id="atafsir_next_page"),
            manage_components.create_button(style=ButtonStyle.red, label="الصفحة السابقة", emoji="➡",
                                            custom_id="atafsir_previous_page"),
            manage_components.create_button(style=ButtonStyle.URL, label="tafsir.app", url=tafsir.url)
        ]
        action_row = manage_components.create_actionrow(*buttons)
        await ctx.send(embed=em, components=[action_row])
        while True:
            try:
                button_ctx = await manage_components.wait_for_component(self.bot, components=action_row,
                                                                        timeout=600)
                if button_ctx.custom_id == 'atafsir_previous_page':
                    if tafsir.page > 1:
                        tafsir.page -= 1
                    else:
                        tafsir.page = num_pages
                    em = tafsir.make_embed()
                    await button_ctx.edit_origin(embed=em)
                elif button_ctx.custom_id == 'atafsir_next_page':
                    if tafsir.page < num_pages:
                        tafsir.page += 1
                    else:
                        tafsir.page = 1
                    em = tafsir.make_embed()
                    await button_ctx.edit_origin(embed=em)

            except asyncio.TimeoutError:
                break

    @commands.command(name="atafsir")
    async def atafsir(self, ctx, ref: str, tafsir: str = "tabari"):
        quran_reference = QuranReference(ref, False)
        tafsir = ArabicTafsir(quran_reference.surah, quran_reference.ayat_list, tafsir)
        await self.send(ctx, tafsir)

    @cog_ext.cog_slash(name="atafsir", description="تبعث تفسير أي آية, يوجد 56 تفسير متاح بالعربية",
                       options=[
                           create_option(
                               name="تفسير",
                               description="اسم التفسير.",
                               option_type=3,
                               required=True,
                               choices=generate_choices_from_list(list(names.values()))),
                           create_option(
                               name= "السورة_و_الآية",
                               description = "رقم السورة:رقم الآية - على سبيل المثال: 2:255",
                               option_type=3,
                               required=True)
                       ])
    async def slash_atafsir(self, ctx: SlashContext, ref: str, tafsir: str):
        await ctx.defer()
        quran_reference = QuranReference(ref, False)
        tafsir = ArabicTafsir(quran_reference.surah, quran_reference.ayat_list, tafsir)
        await self.send(ctx, tafsir)


def setup(bot):
    bot.add_cog(Tafsir(bot))
