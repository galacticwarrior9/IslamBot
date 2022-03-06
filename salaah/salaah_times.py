import asyncio
import datetime as dt
from datetime import timedelta

import discord
from aiohttp import ClientSession
from dateutil.tz import gettz
from discord.ext import commands
from discord.ext.commands import MissingRequiredArgument
from discord_slash import SlashContext, cog_ext
from discord_slash.utils.manage_commands import create_option

from praytimes import PrayTimes
from utils.database_utils import PrayerTimesHandler

icon = 'https://images-na.ssl-images-amazon.com/images/I/51q8CGXOltL.png'

headers = {'content-type': 'application/json'}


class PrayerTimes(commands.Cog):
    def __init__(self, bot):
        self.session = ClientSession(loop=bot.loop)
        self.bot = bot
        self.methods_url = 'https://api.aladhan.com/methods'
        self.prayertimes_url = 'http://api.aladhan.com/timingsByAddress?address={}&method={}&school={}'

    async def get_calculation_methods(self):
        async with self.session.get(self.methods_url, headers=headers) as resp:
            data = await resp.json()
            data = data['data'].values()

            # There's an entry ('CUSTOM') with no 'name' value, so we need to ignore it:
            calculation_methods = {method['id']: method['name'] for method in data if int(method['id']) != 99}
            return calculation_methods

    async def get_prayertimes(self, location, calculation_method):
        url = self.prayertimes_url.format(location, calculation_method, '0')

        async with self.session.get(url, headers=headers) as resp:
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

        url = self.prayertimes_url.format(location, calculation_method, '1')

        async with self.session.get(url, headers=headers) as resp:
            data = await resp.json()
            hanafi_asr = data['data']['timings']['Asr']

        return fajr, sunrise, dhuhr, asr, hanafi_asr, maghrib, isha, imsak, midnight, date

    async def get_prayertimes_local(self, location, calculation_method):
        async def get_information(location):
            url = "http://api.aladhan.com/v1/hijriCalendarByAddress"
            params = {"address": location}
            async with self.session.get(url, headers=headers, params=params) as resp:
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

    async def _prayertimes(self, ctx, location):
        calculation_method = await PrayerTimesHandler.get_user_calculation_method(ctx.author.id)
        calculation_method = int(calculation_method)

        try:
            fajr, sunrise, dhuhr, asr, hanafi_asr, maghrib, isha, imsak, midnight, date = await \
                self.get_prayertimes(location, calculation_method)
        except:
            return await ctx.send("**Location not found**.")

        em = discord.Embed(colour=0x2186d3, title=date)
        em.set_author(name=f'Prayer Times for {location.title()}', icon_url=icon)
        em.add_field(name='**Imsak (إِمْسَاك)**', value=f'{imsak}', inline=True)
        em.add_field(name='**Fajr (صلاة الفجر)**', value=f'{fajr}', inline=True)
        em.add_field(name='**Sunrise (طلوع الشمس)**', value=f'{sunrise}', inline=True)
        em.add_field(name='**Ẓuhr (صلاة الظهر)**', value=f'{dhuhr}', inline=True)
        em.add_field(name='**Asr (صلاة العصر)**', value=f'{asr}', inline=True)
        em.add_field(name='**Asr - Ḥanafī School (صلاة العصر - حنفي)**', value=f'{hanafi_asr}', inline=True)
        em.add_field(name='**Maghrib (صلاة المغرب)**', value=f'{maghrib}', inline=True)
        em.add_field(name='**Isha (صلاة العشاء)**', value=f'{isha}', inline=True)
        em.add_field(name='**Midnight (منتصف الليل)**', value=f'{midnight}', inline=True)

        calculation_methods = await self.get_calculation_methods()
        em.set_footer(text=f'Calculation Method: {calculation_methods[calculation_method]}')
        await ctx.send(embed=em)

    @commands.command(name="prayertimes")
    async def prayertimes(self, ctx, *, location):
        await ctx.channel.trigger_typing()
        await self._prayertimes(ctx, location)

    @prayertimes.error
    async def on_prayertimes_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"**Please provide a location**. \n\nExample: `{ctx.prefix}prayertimes Dubai, UAE`")

    @cog_ext.cog_slash(name="prayertimes", description="Get the prayer times for a location.",
                       options=[
                           create_option(
                               name="location",
                               description="The location to get prayer times for.",
                               option_type=3,
                               required=True)])
    async def slash_prayertimes(self, ctx: SlashContext, location: str, calculation_method: int = None):
        await ctx.defer()
        await self._prayertimes(ctx, location)

    @commands.command(name="setcalculationmethod")
    async def setcalculationmethod(self, ctx, method_num: int):
        await ctx.channel.trigger_typing()
        calculation_methods = await self.get_calculation_methods()
        try:
            if method_num not in calculation_methods.keys():
                raise TypeError
        except:
            return await ctx.send("❌ **Invalid calculation method number.** ")

        await PrayerTimesHandler.update_user_calculation_method(ctx.author.id, method_num)
        await ctx.send(':white_check_mark: **Successfully updated!**')

    async def _methodlist(self, ctx):
        em = discord.Embed(colour=0x467f05, description='')
        em.set_author(name='Calculation Methods', icon_url=icon)
        calculation_methods = await self.get_calculation_methods()
        for method, name in calculation_methods.items():
            em.description = f'{em.description}**{method}** - {name}\n'
        await ctx.send(embed=em)

    @commands.command(name="methodlist")
    async def methodlist(self, ctx):
        await ctx.channel.trigger_typing()
        await self._methodlist(ctx)


def setup(bot):
    bot.add_cog(PrayerTimes(bot))
