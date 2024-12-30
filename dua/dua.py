import random

import discord
from discord.ext import commands
from fuzzywuzzy import process, fuzz

from utils.utils import get_site_source

URL = 'https://ahadith.co.uk/hisnulmuslim-dua-{}'
ICON = 'https://sunnah.com/images/hadith_icon2_huge.png'

DUAS = {
    'Afflictions': 49,
    'After Eating': 66,
    'After Insulting': 105,
    'After Sinning': 41,
    'After Sneezing': 72,
    'Angriness': 76,
    'Anxiety': 34,
    'Before Eating': 65,
    'Breaking Fast': 64,
    'Completing Wudu': 9,
    'Delight': 115,
    'Distress': 35,
    'Doubts': 37,
    'During Adhan': 15,
    'Entering Home': 11,
    'Fear Of People': 114,
    'Fear Of Shirk': 86,
    'Forgiveness': 127,
    'In Ruku': 17,
    'Leaving Home': 10,
    'Pain': 117,
    'Returning From Travel': 99,
    'Sorrow': 34,
    'Travel': 90,
    'Visiting Graves': 56,
    'Visiting Sick': 45,
    'During Rain': 60,
    'After Rain': 61,
    'Hearing Thunder': 58,
    'Entering Mosque': 13,
    'Leaving Mosque': 14,
    'Entering Toilet': 6,
    'Leaving Toilet': 7,
    'Waking Up': 1,
    'Wearing Garment': 2,
    'Wearing New Garment': 3,
    'Going To Mosque': 12,
    'Between Sujood': 20,
    'Fear During Sleep': 30,
    'Help From Debt': 38,
    'Difficulty': 40,
    'Strong Wind': 57,
    'Entertained By Host': 67,
    'Newly Married': 73,
    'Seeing Someone Afflicted': 77,
    'Conclusion Of Gathering': 79,
    'Thanking Someone': 81,
    'After Settling Debt': 85,
    'Boarding Vehicle': 89,
    'Entering Market': 92,
    'Ascending And Descending': 96,
    'Receiving News': 100,
    'Dog Barking': 104,
    'Day Of Arafah': 109,
    'Talbiyah': 120,
    'After Salam': 25,
    'Istikharah': 26,
    'After Witr': 33,
}


class Dua(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _dua(self, interaction: discord.Interaction, subject: str):
        subject = subject.title()
        try:
            dua_id = DUAS[subject]
        except KeyError:
            subject = process.extract(subject, DUAS.keys(), scorer=fuzz.partial_ratio, limit=1)
            if subject is None:
                raise KeyError

            subject = subject[0][0].title()
            dua_id = DUAS[subject]

        site_source = await get_site_source(URL.format(dua_id))
        dua_text = []
        for dua in site_source.findAll("div", {"class": 'search-item'}):
            text = dua.get_text(separator=" ").strip() \
                .replace("(saw)", "ﷺ")
            text = '\n' + text
            dua_text.append(text)
        dua_text = ''.join(dua_text)
        dua_text = dua_text.split("\n")  # split to get the number that was unintentionally scraped as an item

        for item in dua_text:
            if item.strip().isdigit():  # check if each item is a number
                dua_text.remove(item)  # remove then number

        dua_text = '\n'.join(dua_text)

        em = discord.Embed(title=f'Duas for {subject}', colour=0x467f05, description=dua_text)
        em.set_author(name="Fortress of the Muslim", icon_url=ICON)
        await interaction.followup.send(embed=em)

    async def _dua_list(self, interaction: discord.Interaction):
        dua_list_message = [f'**Type </dua:817163873730822195> <topic>**. Example: `/dua breaking fast`\n']

        for dua in DUAS:
            dua_list_message.append('\n' + dua)

        em = discord.Embed(title='Dua List', colour=0x467f05, description=''.join(dua_list_message))
        em.set_footer(text="Source: Fortress of the Muslim (Hisn al-Muslim)")

        await interaction.response.send_message(embed=em, ephemeral=True)

    @discord.app_commands.command(name="dua", description="Send ʾadʿiyah by topic.")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    @discord.app_commands.describe(topic="The topic of the dua, from /dualist.")
    async def dua(self, interaction: discord.Interaction, topic: str):
        await interaction.response.defer(thinking=True)
        await self._dua(interaction, topic)

    @discord.app_commands.command(name="rdua", description="Sends a random dua.")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def rdua(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True)
        await self._dua(interaction, random.choice(list(DUAS.keys())))

    @discord.app_commands.command(name="dualist", description="Sends the dua topic list.")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
    async def dua_list(self, interaction: discord.Interaction):
        await self._dua_list(interaction)

    @dua.autocomplete('topic')
    async def dua_topic_autocomplete_callback(self, interaction: discord.Interaction, current: str):
        if len(current) == 0:  # User has not started typing, so don't send anything
            return []
        choices = [
            discord.app_commands.Choice(name=k, value=k)
            for k, v in DUAS.items() if current.lower() in k.lower()
        ]
        if len(choices) > 25:  # Discord limits choices to 25
            return choices[0:24]
        return choices

    @dua.error
    async def on_dua_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        if isinstance(error, KeyError):
            await interaction.followup.send(
                f":warning: **Could not find dua for this topic.** Type </dualist:967584174586355741> for a list of dua topics.")


async def setup(bot):
    await bot.add_cog(Dua(bot))
