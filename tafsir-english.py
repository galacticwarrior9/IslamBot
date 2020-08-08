import asyncio
import discord
import textwrap
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from utils import get_site_source

icon = 'https://cdn6.aptoide.com/imgs/6/a/6/6a6336c9503e6bd4bdf98fda89381195_icon.png'

dictName = {
    'ibnkathir': 'Tafsīr Ibn Kathīr',
    'jalalayn': 'Tafsīr al-Jalālayn',
    'tustari': 'Tafsīr al-Tustarī',
    'kashani': 'Tafsīr ʿAbd al-Razzāq al-Kāshānī',
    'qushayri': 'Laṭāʾif al-Ishārāt',
    'wahidi': 'Asbāb al-Nuzūl',
    'kashf': 'Kashf al-Asrār'
}

dictID = {
    'tustari': 93,
    'kashani': 107,
    'qushayri': 108,
    'wahidi': 86,
    'kashf': 109,
}

invalid_verse = '**Invalid arguments.** Type the command in this format: `{0}tafsir <surah>:<ayah> <tafsir name>`.' \
                '\n\n**Example**: `{0}tafsir 1:1 ibnkathir`'

invalid_tafsir = "**Couldn't find tafsir!** Please choose from the following: `ibnkathir`, `jalalayn`, `qushayri`, " \
                 "`wahidi`, `tustari`, `kashf`."

no_tafsir = "**Could not find tafsir for this verse.** Please try another tafsir."

altafsir_url = 'https://www.altafsir.com/Tafasir.asp?tMadhNo=0&tTafsirNo={}&tSoraNo={}&tAyahNo={}&tDisplay=yes&Page={}&Size=1&LanguageId=2'

ibnkathir_url = 'http://www.alim.org/library/quran/AlQuran-tafsir/TIK/{}/{}'

jalalayn_url = 'https://raw.githubusercontent.com/galacticwarrior9/islambot/master/tafsir_jalalayn.txt'


class TafsirSpecifics:
    def __init__(self, tafsir, ref, page):
        self.page = page
        self.pages = None
        self.num_pages = None
        self.url = None
        self.tafsir = tafsir.lower()
        self.tafsir_name = dictName[tafsir]
        self.surah, self.ayah = ref.split(':')
        self.text = None
        self.make_url(self.tafsir, self.surah, self.ayah)
        self.embed = None

    def make_url(self, tafsir, surah, ayah):
        if tafsir in dictID.keys():
            tafsir_id = dictID[tafsir]
            self.url = altafsir_url.format(tafsir_id, surah, ayah, 1)
        elif tafsir == 'jalalayn':
            self.url = jalalayn_url
        elif tafsir == 'ibnkathir':
            self.url = ibnkathir_url.format(surah, ayah)

    async def get_text(self, tafsir, ctx):
        source = await get_site_source(self.url)
        tags = []

        if tafsir in dictID.keys():
            for tag in source.findAll('font', attrs={'class': 'TextResultEnglish'}):
                tags.append(f' {tag.getText()}')
            for tag in source.findAll('font', attrs={'class': 'TextArabic'}):
                tags.append(tag.getText())
            self.text = ''.join(tags)

        elif tafsir == 'ibnkathir':
            body = source.find('note')
            text = body.text
            self.text = text
            self.clean_text()

        elif tafsir == 'jalalayn':
            source = source.decode('utf-8')
            self.ayah = int(self.ayah)
            self.surah = int(self.surah)
            try:
                char1 = f'[{self.surah}:{self.ayah}]'
                next_ayah = self.ayah + 1
                char2 = f'[{self.surah}:{next_ayah}]'

                text = source[(source.index(char1) + len(char1)):source.index(char2)]
                self.text = f"{text}".replace('`', '\\`').replace('(s)', '(ﷺ)').rstrip()

            except:
                char1 = f'[{self.surah}:{self.ayah}]'
                self.surah += 1
                char2 = f'[{self.surah}:1]'

                text = source[(source.index(char1) + len(char1)):source.index(char2)]
                self.text = u"{}".format(text).replace('`', '\\`').rstrip()

        self.pages = textwrap.wrap(self.text, 2000, break_long_words=False)
        self.num_pages = len(self.pages)

    def clean_text(self):
        self.text = self.text.replace('`', "'") \
            .replace('bin', 'b. ') \
            .replace('Hadith', 'hadith') \
            .replace('Messenger of Allah', 'Messenger of Allah ﷺ') \
            .replace('«', '#«') \
            .replace('»', '»#') \
            .replace(' "', ' #"') \
            .replace('." ', '."#') \
            .replace('﴿', '#') \
            .replace('﴾', '#') \


    async def make_embed(self):
        em = discord.Embed(title=f'{self.surah}:{self.ayah}', colour=0x467f05, description=self.pages[self.page - 1])
        em.description = em.description.replace('#', '\n\n')
        em.set_author(name=f'{self.tafsir_name}', icon_url=icon)
        if self.num_pages > 1:
            em.set_footer(text=f'Page: {self.page}/{self.num_pages}')
        self.embed = em


class TafsirEnglish(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.baseurl = 'https://www.altafsir.com/Tafasir.asp?tMadhNo=0&tTafsirNo={}&tSoraNo={}&tAyahNo={}&tDisplay=y' \
                       'es&Page={}&Size=1&LanguageId=2'

    async def send_embed(self, ctx, spec):
        msg = await ctx.send(embed=spec.embed)
        if spec.num_pages > 1:
            await msg.add_reaction(emoji='⬅')
            await msg.add_reaction(emoji='➡')

        while True:
            try:
                reaction, user = await self.bot.wait_for("reaction_add", timeout=300, check=lambda reaction, user:
                (reaction.emoji == '➡' or reaction.emoji == '⬅')
                 and user != self.bot.user
                 and reaction.message.id == msg.id)

            except asyncio.TimeoutError:
                await msg.remove_reaction(emoji='➡', member=self.bot.user)
                await msg.remove_reaction(emoji='⬅', member=self.bot.user)
                break

            if reaction.emoji == '➡' and spec.page:
                spec.page += 1
                if spec.page > spec.num_pages:
                    spec.page = 1

            if reaction.emoji == '⬅':
                spec.page -= 1
                if spec.page < 1:
                    spec.page = spec.num_pages

            await spec.make_embed()
            await msg.edit(embed=spec.embed)
            try:
                await msg.remove_reaction(reaction.emoji, user)
            # The above fails if the bot doesn't have the "Manage Messages" permission, but it can be safely ignored
            # as it is not essential functionality.
            except discord.ext.commands.errors.CommandInvokeError:
                pass

    @commands.command(name='tafsir')
    async def tafsir(self, ctx, ref: str, tafsir: str = "jalalayn", page: int = 1):
        try:
            spec = TafsirSpecifics(tafsir, ref, page)
        except KeyError:
            return await ctx.send(invalid_tafsir)
        except ValueError:
            return await ctx.send(invalid_verse.format(ctx.prefix))

        try:
            await spec.get_text(spec.tafsir, ctx)
        except AttributeError:  # Occurs when no tafsir is found using Ibn Kathir
            await ctx.send(no_tafsir)

        try:
            await spec.make_embed()
        except IndexError:
            return await ctx.send(no_tafsir)

        await self.send_embed(ctx, spec)

    @tafsir.error
    async def on_tafsir_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(invalid_verse.format(ctx.prefix))


def setup(bot):
    bot.add_cog(TafsirEnglish(bot))
