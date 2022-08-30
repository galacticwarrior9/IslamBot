from datetime import datetime, date

import discord
from discord.ext import commands, tasks
from hijri_converter import convert

from utils.utils import convert_to_arabic_number, make_embed

ICON = 'https://icons.iconarchive.com/icons/paomedia/small-n-flat/512/calendar-icon.png'
DATE_INVALID = ':warning: You provided an invalid date!'
GREGORIAN_DATE_OUT_OF_RANGE = '**Sorry, this year is out of range**. The year must be between 1924 and 2077.'
HIJRI_DATE_OUT_OF_RANGE = '**Sorry, this year is out of range**. The year must be between 1343 and 1500.'


class HijriCalendar(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def get_current_hijri():
        hijri = convert.Gregorian.today().to_hijri()
        return f'{hijri.day} {hijri.month_name()} {hijri.year} {hijri.notation(language="en")}'

    @staticmethod
    def get_hijri(gregorian_date: date = None):
        hijri = convert.Gregorian.fromdate(gregorian_date).to_hijri()
        return f'{gregorian_date.strftime("%d %B %Y")} is **{hijri.month_name()} {hijri.day}, {hijri.year} AH**.' \
               f'\n\nالتاريخ الهجري: __**' \
               f'{hijri.day_name(language="ar")} {convert_to_arabic_number(str(hijri.day))} ' \
               f'{hijri.month_name(language="ar")} {convert_to_arabic_number(str(hijri.year))} ' \
               f'{hijri.notation(language="ar")}**__'

    @staticmethod
    def get_gregorian(hijri_date):
        gregorian = convert.Hijri(hijri_date.year, hijri_date.month, hijri_date.day).to_gregorian()
        return f'{hijri_date.strftime("%d-%m-%Y")} AH is **{gregorian.strftime("%d %B %Y")}**'

    async def _convert_to_hijri(self, interaction: discord.Interaction, gregorian_date: str):
        response = interaction.response
        try:
            gregorian_date = datetime.strptime(gregorian_date, "%d-%m-%Y").date()
        except:
            return await response.send_message(DATE_INVALID)

        try:
            hijri = self.get_hijri(gregorian_date=gregorian_date)
        except OverflowError:
            return await response.send_message(GREGORIAN_DATE_OUT_OF_RANGE)

        em = discord.Embed(colour=0x72bcd4, description=hijri)
        em.set_author(name="Gregorian → Hijri Conversion", icon_url=ICON)
        await response.send_message(embed=em)

    async def _convert_to_gregorian(self, interaction: discord.Interaction, hijri_date: str):
        response = interaction.response
        try:
            hijri_date = datetime.strptime(hijri_date, "%d-%m-%Y").date()
        except:
            return await response.send_message(DATE_INVALID)

        try:
            gregorian = self.get_gregorian(hijri_date=hijri_date)
        except OverflowError:
            return await response.send_message(HIJRI_DATE_OUT_OF_RANGE)

        em = discord.Embed(colour=0x72bcd4, description=gregorian)
        em.set_author(name="Hijri → Gregorian Conversion", icon_url=ICON)
        await response.send_message(embed=em)

    async def _hijridate(self, interaction: discord.Interaction):
        hijri = self.get_current_hijri()
        em = discord.Embed(colour=0x72bcd4, description=hijri).set_author(name="Today's Hijri Date", icon_url=ICON)
        await interaction.response.send_message(embed=em)

    group = discord.app_commands.Group(name="calendar", description="Convert between Gregorian and Hijri dates.")

    @group.command(name="to_hijri", description="Convert a Gregorian date to a Hijri date.")
    @discord.app_commands.describe(
        day="The day of the Gregorian date to convert, e.g. 1, 31",
        month="The month of the Gregorian date to convert, e.g. 1 for January; 12 for December",
        year="The year of the Gregorian date to convert, e.g. 2023. Must be between 1924 and 2077."
    )
    async def convert_to_hijri(self, interaction: discord.Interaction, day: int, month: int, year: int):
        await self._convert_to_hijri(interaction, f"{day}-{month}-{year}")

    @group.command(name="to_gregorian", description="Convert a Hijri date to a Gregorian date.")
    @discord.app_commands.describe(
        day="The day of the Hijri date to convert, e.g. 1, 29",
        month="The month of the Hijri date to convert, e.g. 1 for Muḥarram, 9 for Ramaḍān",
        year="The year of the Hijri date to convert, e.g. 1444. Must be between 1343 and 1500."
    )
    async def convert_to_gregorian(self, interaction: discord.Interaction, day: int, month: int, year: int):
        await self._convert_to_gregorian(interaction, f"{day}-{month}-{year}")

    @group.command(name="hijri_date", description="Get the current Hijri date.")
    async def hijri_date(self, interaction: discord.Interaction):
        await self._hijridate(interaction)

    @hijri_date.error
    @convert_to_hijri.error
    @convert_to_gregorian.error
    async def on_convert_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        await interaction.response.send_message(f":warning: **Error!** `{error}`")


async def setup(bot):
    await bot.add_cog(HijriCalendar(bot), guild=discord.Object(308241121165967362))
