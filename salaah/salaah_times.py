import datetime as dt
from datetime import timedelta

import discord
from dateutil.tz import gettz
from discord.ext import commands

from salaah.praytimes import PrayTimes
from utils.database_utils import PrayerTimesHandler

ICON = 'https://images-na.ssl-images-amazon.com/images/I/51q8CGXOltL.png'
METHODS_URL = 'https://api.aladhan.com/v1/methods'
PRAYER_TIMES_URL = 'http://api.aladhan.com/v1/timingsByAddress?address={}&method={}&school={}'

headers = {'content-type': 'application/json'}


class PrayerTimes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def get_calculation_methods(self):
        async with self.bot.session.get(METHODS_URL, headers=headers) as resp:
            data = await resp.json()
            data = data['data'].values()

            # There's an entry ('CUSTOM') with no 'name' value, so we need to ignore it:
            calculation_methods = {method['id']: method['name'] for method in data if int(method['id']) != 99}
            return calculation_methods

    async def get_prayertimes(self, location, calculation_method):
        url = PRAYER_TIMES_URL.format(location, calculation_method, '0')

        async with self.bot.session.get(url, headers=headers) as resp:
            data = await resp.json()
            fajr = data['data']['timings']['Fajr']
            sunrise = data['data']['timings']['Sunrise']
            dhuhr = data['data']['timings']['Dhuhr']
            asr = data['data']['timings']['Asr']
            maghrib = data['data']['timings']['Maghrib']
            isha = data['data']['timings']['Isha']
            imsak = data['data']['timings']['Imsak']
            midnight = data['data']['timings']['Midnight']
            date = data['data']['date']['readable']

        url = PRAYER_TIMES_URL.format(location, calculation_method, '1')

        async with self.bot.session.get(url, headers=headers) as resp:
            data = await resp.json()
            hanafi_asr = data['data']['timings']['Asr']

        return fajr, sunrise, dhuhr, asr, hanafi_asr, maghrib, isha, imsak, midnight, date

    async def get_prayertimes_local(self, location, calculation_method):
        async def get_information(location):
            url = "http://api.aladhan.com/v1/hijriCalendarByAddress"
            params = {"address": location}
            async with self.bot.session.get(url, headers=headers, params=params) as resp:
                data = await resp.json()
                meta = data['data'][0]['meta']
                coordinates = (meta['latitude'], meta['longitude'])
                timezone_name = meta['timezone']
            time = dt.datetime.now(gettz(timezone_name))
            timezone_offset = time.utcoffset() / timedelta(hours=1)
            return coordinates, time, timezone_offset

        def get_method_name(method_id):
            id_to_name = {
                3: 'MWL',
                2: 'ISNA',
                5: 'Egypt',
                4: 'Makkah',
                1: 'Karachi',
                7: 'Tehran',
                0: 'Jafari',
                8: 'Gulf',  # TODO add this method to praytimes.py
                9: 'Kuwait',  # TODO add this method to praytimes.py
                10: 'Qatar',  # TODO add this method to praytimes.py
                11: 'Singapore',  # TODO add this method to praytimes.py
                12: 'France',  # TODO add this method to praytimes.py
                13: 'Turkey',  # TODO add this method to praytimes.py
                14: 'Russia',  # TODO add this method to praytimes.py

                # didn't include method 'MOONSIGHTING' because it uses 'shafaq' parameter,
                # which isn't used in praytimes.py
            }
            return id_to_name[method_id]

        coordinates, time, time_offset = await get_information(location)
        date = (time.year, time.month, time.day)
        method_name = get_method_name(calculation_method)
        prayTimes = PrayTimes()
        prayTimes.setMethod(method_name)
        prayTimes.adjust({"highLats": "AngleBased"})
        prayTimes.adjust({"asr": "Standard"})
        times = prayTimes.getTimes(date, coordinates, time_offset)
        prayTimes.adjust({"asr": "Hanafi"})
        timesWithHanafiAsr = prayTimes.getTimes(date, coordinates, time_offset)

        fajr = times['fajr']
        sunrise = times['sunrise']
        dhuhr = times['dhuhr']
        asr = times['asr']
        hanafi_asr = timesWithHanafiAsr['asr']
        maghrib = times['maghrib']
        isha = times['isha']
        imsak = times['imsak']
        midnight = times['midnight']
        sunrise = times['sunrise']
        readable_date = time.strftime('%d %B, %Y')

        return fajr, sunrise, dhuhr, asr, hanafi_asr, maghrib, isha, imsak, midnight, readable_date

    async def _prayer_times(self, interaction: discord.Interaction, location: str):
        calculation_method = await PrayerTimesHandler.get_user_calculation_method(interaction.user.id)
        calculation_method = int(calculation_method)

        try:
            fajr, sunrise, dhuhr, asr, hanafi_asr, maghrib, isha, imsak, midnight, date = await \
                self.get_prayertimes(location, calculation_method)
        except:
            return await interaction.followup.send(":warning: **Location not found**.")

        em = discord.Embed(colour=0x2186d3, title=date)
        em.set_author(name=f'Prayer Times for {location.title()}', icon_url=ICON)\
            .add_field(name='**Imsak (إِمْسَاك)**', value=f'{imsak}', inline=True)\
            .add_field(name='**Fajr (صلاة الفجر)**', value=f'{fajr}', inline=True)\
            .add_field(name='**Sunrise (طلوع الشمس)**', value=f'{sunrise}', inline=True)\
            .add_field(name='**Ẓuhr (صلاة الظهر)**', value=f'{dhuhr}', inline=True)\
            .add_field(name='**Asr (صلاة العصر)**', value=f'{asr}', inline=True)\
            .add_field(name='**Asr - Ḥanafī School (صلاة العصر - حنفي)**', value=f'{hanafi_asr}', inline=True)\
            .add_field(name='**Maghrib (صلاة المغرب)**', value=f'{maghrib}', inline=True)\
            .add_field(name='**Isha (صلاة العشاء)**', value=f'{isha}', inline=True)\
            .add_field(name='**Midnight (منتصف الليل)**', value=f'{midnight}', inline=True)

        calculation_methods = await self.get_calculation_methods()
        em.set_footer(text=f'Calculation Method: {calculation_methods[calculation_method]}')
        await interaction.followup.send(embed=em)

    group = discord.app_commands.Group(name="prayertimes", description="Commands related to prayer times.")

    @group.command(name="get", description="Get the prayer times for a location.")
    @discord.app_commands.describe(
        location="The location to get prayer times for.",
        calculation_method="The method to use when calculating the prayer times."
    )
    async def prayer_times(self, interaction: discord.Interaction, location: str, calculation_method: int = None):
        await interaction.response.defer(thinking=True)
        await self._prayer_times(interaction, location)

    async def _set_calculation_method(self, interaction: discord.Interaction, method_num: int):
        calculation_methods = await self.get_calculation_methods()

        if method_num not in calculation_methods.keys():
            return await interaction.followup.send("❌ **Invalid calculation method number.**", ephemeral=True)

        await PrayerTimesHandler.update_user_calculation_method(interaction.user.id, method_num)
        return await interaction.followup.send(':white_check_mark: **Successfully updated!**', ephemeral=True)

    @group.command(name="set_calculation_method", description="Change your default prayer times calculation method")
    @discord.app_commands.describe(
        method_number="The number of the prayer time calculation method, from /prayertimes list_calculation_methods."
    )
    async def set_calculation_method(self, interaction: discord.Interaction, method_number: int):
        await interaction.response.defer(thinking=True, ephemeral=True)
        await self._set_calculation_method(interaction, method_number)

    async def _list_methods(self, interaction: discord.Interaction):
        em = discord.Embed(colour=0x467f05, description='')
        em.set_author(name='Calculation Methods', icon_url=ICON)
        calculation_methods = await self.get_calculation_methods()
        for method, name in calculation_methods.items():
            em.description = f'{em.description}**{method}** - {name}\n'
        return await interaction.followup.send(embed=em, ephemeral=True)

    @group.command(name="list_calculation_methods", description="Sends the list of calculation methods.")
    async def list_methods(self, interaction: discord.Interaction):
        await interaction.response.defer(thinking=True, ephemeral=True)
        await self._list_methods(interaction)


async def setup(bot):
    await bot.add_cog(PrayerTimes(bot), guild=discord.Object(308241121165967362))
