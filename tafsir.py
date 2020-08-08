import discord
import textwrap
import re
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from utils import get_site_source, convert_to_arabic_number, convert_from_arabic_number


icon = 'https://lh5.ggpht.com/lRz25mOFrRL42NuHtuSCneXbWV2Gtm7iYZ5eQbuA7JWUC3guWaTaQxNJ7j9rsRMCNAU=w150'

dictName = {
    'ibnatiyah': 'المحرر الوجيز — ابن عطية (٥٤٦ هـ)',
    'tabari': 'جامع البيان — ابن جرير الطبري (٣١٠ هـ)',
    'fathalbayan': 'فتح البيان — صديق حسن خان (١٣٠٧ هـ)',
    'muyassar': 'الميسر — مجمع الملك فهد',
    'ibnkathir': 'تفسير القرآن العظيم — ابن كثير (٧٧٤ هـ)',
    'shawkani': 'فتح القدير — الشوكاني (١٢٥٠ هـ)',
    'mukhtasar': 'المختصر — مركز تفسير',
    'qurtubi': 'الجامع لأحكام القرآن — القرطبي (٦٧١ هـ)',
    'ibnjuzayy': 'التسهيل لعلوم التنزيل — ابن جُزَيّ (٧٤١ هـ)',
    'saadi': 'تيسير الكريم الرحمن — السعدي (١٣٧٦ هـ)',
    'baghawi': 'معالم التنزيل — البغوي (٥١٦ هـ)',
    'jazaeri': 'أيسر التفاسير — أبو بكر الجزائري (١٤٣٩ هـ)',
    'alusi': 'روح المعاني — الآلوسي (١٢٧٠ هـ)',
    'ibnaljawzi': 'زاد المسير — ابن الجوزي (٥٩٧ هـ)',
    'razi': 'مفاتيح الغيب — فخر الدين الرازي (٦٠٦ هـ)',
    'ibnuthaymeen': 'تفسير القرآن الكريم — ابن عثيمين (١٤٢١ هـ)',
    'mawardi': 'النكت والعيون — الماوردي (٤٥٠ هـ)',
    'jalalayn': 'تفسير الجلالين — المحلّي والسيوطي (٨٦٤، ٩١١ هـ)',
    'ibnalqayyim': 'تفسير ابن قيّم الجوزيّة — ابن القيم (٧٥١ هـ)',
    'baqai': 'نظم الدرر — البقاعي (٨٨٥ هـ)',
    'iji': 'جامع البيان — الإيجي (٩٠٥ هـ)',
    'baydawi': 'أنوار التنزيل — البيضاوي (٦٨٥ هـ)',
    'ibnashur': 'التحرير والتنوير — ابن عاشور (١٣٩٣ هـ)',
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
    'zamakhshari': 'الكشاف — الزمخشري (٥٣٨ هـ)',
    'ibnabihatim': 'تفسير القرآن العظيم مسندًا — ابن أبي حاتم الرازي (٣٢٧ هـ)',
    'thaalabi': 'الجواهر الحسان — الثعالبي (٨٧٥ هـ)'
}

dictNameReverse = dict((value, key) for key, value in dictName.items())

dictID = {
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
    'thaalabi': 'althaalabi'
}


class Tafsir(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.url = 'https://tafsir.app/{}/{}/{}'

    def make_url(self, tafsir_id, surah, ayah):
        url = self.url.format(tafsir_id, surah, ayah)
        return url

    '''
    Gets the tafir ID (for use in the URL) and Arabic name
    '''
    @staticmethod
    def get_tafsir_id(tafsir):
        tafsir_name = dictName[tafsir.lower()]
        tafsir_id = dictID[tafsir.lower()]
        return tafsir_name, tafsir_id

    '''
    Get the surah and ayah from the ref. 
    '''
    @staticmethod
    def process_ref(ref: str):
        surah, ayah = ref.split(':')
        return surah, ayah

    '''
    Gets, formats and paginates the tafsir text.
    '''
    @staticmethod
    def process_text(content, page):

        # Parse the website's source and find the tafsir text.
        soup = BeautifulSoup(content, 'html.parser')
        tag = soup.find('div', attrs={'id': 'preloaded'})
        text = tag.get_text(separator=" ").strip()
        text = text.replace(']]', '*]')\
            .replace('[[', '[*')\
            .replace('*', '')\
            .replace('"ayah":', '') \
            .replace('"', '') \
            .replace('}', ' ﴾') \
            .replace('{', ' ﴿') \
            .replace(' ).', ').#') \

        # Paginate the text, set the embed text to the current page and calculate how many pages were made:
        try:
            pages = textwrap.wrap(text, 2034, break_long_words=False)
            text = pages[page - 1]
            text = '***' + text + '***'
            num_pages = len(pages)
        except IndexError:
            return

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

        return text, num_pages, footer

    @staticmethod
    def make_embed(text, page, tafsir_name, surah, ayah, footer, formatted_url, num_pages):

        ref = convert_to_arabic_number(f'{surah}:{ayah}')
        text = text.replace('#', '\n')
        em = discord.Embed(title=ref, colour=0x467f05, description=text)
        if footer != '':
            em.set_footer(text=f'Page {page}/{num_pages} \n____________________________________\n{footer}')
        else:
            em.set_footer(text=f'Page {page}/{num_pages}')
        em.set_author(name=f'{tafsir_name}', url=formatted_url, icon_url=icon)

        return em

    @commands.command(name="atafsir", aliases=["atafseer"])
    async def atafsir(self, ctx, ref: str, tafsir: str = "tabari", page: int = 1):

        surah, ayah = self.process_ref(ref)

        tafsir_name, tafsir_id = self.get_tafsir_id(tafsir)

        formatted_url = self.make_url(tafsir_id, surah, ayah)

        content = str(await get_site_source(formatted_url))

        try:
            text, num_pages, footer = self.process_text(content, page)
        except AttributeError:
            return await ctx.send('***عفوا، لا مواد لهذه الآية في هذا الكتاب***')

        em = self.make_embed(text, page, tafsir_name, surah, ayah, footer, formatted_url, num_pages)

        msg = await ctx.send(embed=em)
        if num_pages > 1:
            await msg.add_reaction(emoji='⬅')
            await msg.add_reaction(emoji='➡')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.message.author == self.bot.user and user != self.bot.user:
            msg = reaction.message
            embed = msg.embeds[0]

            # Get the tafsir ID to use in the URL from its Arabic name in the embed's author:
            arabic_name = embed.author.name
            try:
                tafsir_name = dictNameReverse[arabic_name]
            except KeyError:
                return

            tafsir_id = dictID[tafsir_name]

            # Get the surah and ayah from the embed's title:
            ref = convert_from_arabic_number(embed.title)
            surah, ayah = self.process_ref(ref)

            # Get the page number from the embed footer. First we split to get the word, then again to get the current
            # page.
            page = int(embed.footer.text.split(' ')[1].split('/')[0])
            num_pages = int(embed.footer.text.split(' ')[1].split('/')[1])

            # If the reaction is the forward arrow, attempt to get the last page:
            if reaction.emoji == '➡':
                await msg.remove_reaction(emoji="➡", member=user)

                new_page = page - 1
                if new_page < 1:
                    new_page = num_pages

                formatted_url = self.make_url(tafsir_id, surah, ayah)
                content = str(await get_site_source(formatted_url))
                text, _, footer = self.process_text(content, new_page)

                em = self.make_embed(text, new_page, arabic_name, surah, ayah, footer, formatted_url, num_pages)
                await msg.edit(embed=em)
                await msg.add_reaction(emoji='⬅')

            # If the reaction is the backwards arrow, attempt to get the next page.
            elif reaction.emoji == '⬅':
                await reaction.message.remove_reaction(emoji="⬅", member=user)

                new_page = page + 1
                if new_page > num_pages:
                    new_page = 1

                formatted_url = self.make_url(tafsir_id, surah, ayah)
                content = str(await get_site_source(formatted_url))
                text, _, footer = self.process_text(content, new_page)

                em = self.make_embed(text, new_page, arabic_name, surah, ayah, footer, formatted_url, num_pages)
                await msg.edit(embed=em)
                await msg.add_reaction(emoji='➡')

    @atafsir.error
    async def on_atafsir_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"**لقد أدخلت الأمر خطأ**. اكتب `{ctx.prefix}atafsir <رقم السورة>:<رقم الآية> <اسم تفسير اختياري>`")


def setup(bot):
    bot.add_cog(Tafsir(bot))
