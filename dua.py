import discord
import re
from discord.ext import commands
from utils import get_site_source

ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'


class Dua(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.url = 'https://ahadith.co.uk/hisnulmuslim-dua-{}'
        self.duas = {
            'afflictions': 49,
            'after eating': 66,
            'after insulting': 105,
            'after rain': 61,
            'after sinning': 41,
            'after sneezing': 72,
            'angriness': 76,
            'anxiety': 34,
            'before eating': 65,
            'breaking fast': 64,
            'completing wudu': 9,
            'delight': 115,
            'distress': 35,
            'doubts': 37,
            'during adhan': 15,
            'during rain': 60,
            'entering home': 11,
            'entering mosque': 13,
            'entering toilet': 6,
            'fear of people': 114,
            'fear of shirk': 86,
            'forgiveness': 127,
            'hearing thunder': 58,
            'in ruku': 17,
            'leaving home': 10,
            'leaving mosque': 14,
            'leaving toilet': 7,
            'pain': 117,
            'returning from travel': 99,
            'sorrow': 34,
            'travel': 90,
            'visiting grave': 56,
            'visiting sick': 45
        }

    @staticmethod
    def get_dua_id(self, subject):
        return self.duas[subject]

    @commands.command(name='dua')
    async def dua(self, ctx, *, subject: str):

        subject = subject.lower()

        try:
            dua_id = self.get_dua_id(self, subject)

        except KeyError:
            return await ctx.send("Could not find dua for this.")

        site_source = await get_site_source(self.url.format(dua_id))
        dua_text = []
        for dua in site_source.findAll("div", {"class": 'search-item'}):
            text = dua.get_text(separator=" ").strip()\
                .replace("(saw)", "ﷺ") \
                .replace("Indeed ", "Indeed, ") \
                .replace("Abee", "Abi")
            text = '\n' + text
            dua_text.append(text)

        dua_text = ''.join(dua_text)
        dua_text = re.sub(r'\d+', '', dua_text)

        em = discord.Embed(title=f'Duas for {subject.title()}', colour=0x467f05, description=dua_text)
        em.set_author(name="Fortress of the Muslim (Hisnul Muslim)", icon_url=ICON)

        await ctx.send(embed=em)

    @commands.command(name='dualist')
    async def dualist(self, ctx):
        dua_list_message = ['**Type {0}dua <topic>**. Example: `{0}dua breaking fast`\n'.format(ctx.prefix)]

        for dua in self.duas:
            dua_list_message.append('\n' + dua.title())

        em = discord.Embed(title=f'Dua List', colour=0x467f05, description=''.join(dua_list_message))
        em.set_footer(text="Source: Fortress of the Muslim (Hisnul Muslim)")

        await ctx.send(embed=em)


def setup(bot):
    bot.add_cog(Dua(bot))
