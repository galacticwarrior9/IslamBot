import asyncio
import discord
import pytz
from aiohttp import ClientSession
from datetime import datetime
from dbhandler import update_server_prayer_times_details, delete_server_prayer_times_details, \
    get_server_prayer_times_details, get_user_calculation_method, update_user_calculation_method, \
    get_user_prayer_times_details, update_user_prayer_times_details, delete_user_prayer_times_details
from discord.ext import commands, tasks
from discord.ext.commands import CheckFailure, MissingRequiredArgument, BadArgument
from pytz import timezone

icon = 'https://www.muslimpro.com/img/muslimpro-logo-2016-250.png'

headers = {'content-type': 'application/json'}


class PrayerTimes(commands.Cog):

    def __init__(self, bot):
        self.session = ClientSession(loop = bot.loop)
        self.bot = bot
        self.send_reminders.start()
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

    @commands.command(name="prayertimes")
    async def prayertimes(self, ctx, *, location):

        calculation_method = await get_user_calculation_method(ctx.author.id)
        calculation_method = int(calculation_method)

        try:
            fajr, sunrise, dhuhr, asr, hanafi_asr, maghrib, isha, imsak, midnight, date = await \
                self.get_prayertimes(location, calculation_method)
        except:
            return await ctx.send("**Location not found**.")

        em = discord.Embed(colour=0x2186d3, title=date)
        em.set_author(name=f'Prayer Times for {location.title()}', icon_url=icon)
        em.add_field(name=f'**Imsak (إِمْسَاك)**', value=f'{imsak}', inline=True)
        em.add_field(name=f'**Fajr (صلاة الفجر)**', value=f'{fajr}', inline=True)
        em.add_field(name=f'**Sunrise (طلوع الشمس)**', value=f'{sunrise}', inline=True)
        em.add_field(name=f'**Ẓuhr (صلاة الظهر)**', value=f'{dhuhr}', inline=True)
        em.add_field(name=f'**Asr (صلاة العصر)**', value=f'{asr}', inline=True)
        em.add_field(name=f'**Asr - Ḥanafī School (صلاة العصر - حنفي)**', value=f'{hanafi_asr}', inline=True)
        em.add_field(name=f'**Maghrib (صلاة المغرب)**', value=f'{maghrib}', inline=True)
        em.add_field(name=f'**Isha (صلاة العشاء)**', value=f'{isha}', inline=True)
        em.add_field(name=f'**Midnight (منتصف الليل)**', value=f'{midnight}', inline=True)

        method_names = await self.get_calculation_methods()
        em.set_footer(text=f'Calculation Method: {method_names[calculation_method]}')
        await ctx.send(embed=em)

    @prayertimes.error
    async def on_prayertimes_error(self, ctx, error):
        if isinstance(error, MissingRequiredArgument):
            await ctx.send(f"**Please provide a location**. \n\nExample: `{ctx.prefix}prayertimes Dubai, UAE`")

    @commands.command(name="setcalculationmethod")
    async def setcalculationmethod(self, ctx):

        def is_user(msg):
            return msg.author == ctx.author

        em = discord.Embed(colour=0x467f05, description="Please select a **calculation method number**.\n\n")
        em.set_author(name='Calculation Methods', icon_url=icon)
        calculation_methods = await self.get_calculation_methods()
        for method, name in calculation_methods.items():
            em.description = f'{em.description}**{method}** - {name}\n'
        await ctx.send(embed=em)

        try:
            message = await self.bot.wait_for('message', timeout=120.0, check=is_user)
            method = message.content
            try:
                method = int(method)
                if method not in calculation_methods.keys():
                    raise TypeError
            except:
                return await ctx.send("❌ **Invalid calculation method number.** ")

            await update_user_calculation_method(ctx.author.id, method)
            await ctx.send(':white_check_mark: **Successfully updated!**')

        except asyncio.TimeoutError:
            await ctx.send("❌ **Timed out**. Please try again.")

    @commands.command(name="addprayerreminder")
    async def addprayerreminder(self, ctx):

        def is_user(msg):
            return msg.author == ctx.author

        em = discord.Embed(colour=0x467f05, title='Prayer Times Reminder Setup')
        em.set_author(name=ctx.guild, icon_url=icon)

        try:
            # Ask whether we want to send personal reminders (DMs) or public reminders (in a channel).
            em.description = "Do you want to receive reminders through your **server**, or **DMs**?" \
                             "\n\n__**Please type either `server` or `DMs`.**__" \
                             "\n\nYou __must__ have the **🔒 Administrator** permission to create server reminders." \
                             "\n\nYou __must__ share a mutual server with the bot and allow it to send you DMs to " \
                             "receive DM reminders."
            help_msg = await ctx.send(embed=em)

            message = await self.bot.wait_for('message', timeout=60.0, check=is_user)
            if message.content.lower() == 'server':
                server = True
            elif message.content.lower() == 'dms':
                server = False
            else:
                return await ctx.send("❌ **Invalid response**. Aborting.")

            # Ask for a reminder channel for server reminders.
            if server is True:
                em.description = "Please mention the **channel** to send prayer time reminders in."
                await help_msg.edit(embed=em)

                message = await self.bot.wait_for('message', timeout=60.0, check=is_user)
                if message.channel_mentions:
                    channel = message.channel_mentions[0]
                    if ctx.author.guild_permissions.administrator:
                        channel_id = channel.id
                    else:
                        return await ctx.send("❌ **You do not have the Administrator permission**. Aborting.")
                else:
                    return await ctx.send("❌ **Invalid channel**. Aborting.")
            # Ask for location.
            em.description = "Please set the **location** to send prayer times for. " \
                             "\n\n**Example**: Burj Khalifa, Dubai, UAE"
            await help_msg.edit(embed=em)

            message = await self.bot.wait_for('message', timeout=60.0, check=is_user)
            location = message.content

            # Ask for timezone.
            em.description = "Please select the **__timezone__ of the location**. " \
                             "**[Click here](https://timezonedb.com/time-zones)** for a list of timezones." \
                             "\n\n**Examples**: `Asia/Dubai`, `Europe/London`, `America/Toronto`"
            await help_msg.edit(embed=em)

            message = await self.bot.wait_for('message', timeout=180.0, check=is_user)
            if message.content in pytz.all_timezones:
                timezone = message.content
            else:
                return await ctx.send("❌ **Invalid timezone**. Aborting.")

            # Ask for calculation method.
            em.description = "Please select the prayer times **calculation method number**.\n\n"
            calculation_methods = await self.get_calculation_methods()
            for method, name in calculation_methods.items():
                em.description = f'{em.description}**{method}** - {name}\n'
            await help_msg.edit(embed=em)

            message = await self.bot.wait_for('message', timeout=180.0, check=is_user)
            method = message.content
            try:
                method = int(method)
                if method not in calculation_methods.keys():
                    raise TypeError
            except TypeError:
                return await ctx.send("❌ **Invalid calculation method number.** ")

            # Update database.
            try:
                if server is True:
                    await update_server_prayer_times_details(ctx.guild.id, channel_id, location, timezone, method)
                else:
                    await update_user_prayer_times_details(ctx.author.id, location, timezone, method)
            except Exception as e:
                print(e)
                return await ctx.send("❌ **An error occurred**. You may already have a reminder channel on the server.")

            # Send success message.
            em.description = f":white_check_mark: **Setup complete!**" \
                             f"\n\n**Location**: {location}\n**Timezone**: {timezone}" \
                             f"\n**Calculation Method**: {method}" \
                             f"\n\nIf you would like to change these details, use `{ctx.prefix}removeprayerreminder` " \
                             f"or `{ctx.prefix}removepersonalprayerreminder` and run this command again."
            await help_msg.edit(embed=em)

        except asyncio.TimeoutError:
            await ctx.send("**Timed out.** Please try again.")

    @commands.command(name="removeprayerreminder")
    @commands.has_permissions(administrator=True)
    async def removeprayerreminder(self, ctx, channel: discord.TextChannel):
        try:
            await delete_server_prayer_times_details(ctx.guild.id, channel.id)
            await ctx.send(f":white_check_mark: **You will no longer receive prayer times reminders in <#{channel.id}>.**")
        except:
            await ctx.send("❌ **An error occurred**.")

    @commands.command(name="removepersonalprayerreminder")
    async def removepersonalprayerreminder(self, ctx):
        try:
            await delete_user_prayer_times_details(ctx.author.id)
            await ctx.send(f":white_check_mark: **You will no longer receive prayer times reminders.**")
        except:
            await ctx.send("❌ **An error occurred**.")

    @addprayerreminder.error
    @removeprayerreminder.error
    async def on_error(self, ctx, error):
        if isinstance(error, CheckFailure):
            await ctx.send("🔒 You need the **Administrator** permission to use this command.")
        if isinstance(error, MissingRequiredArgument) or isinstance(error, BadArgument):
            await ctx.send("❌ **Please mention the channel to delete prayer time reminders for**.")

    @tasks.loop(minutes=1)
    async def send_reminders(self):
        print("Starting loop.")
        em = discord.Embed(colour=0x467f05)
        em.set_author(name='Prayer Times Reminder', icon_url=icon)

        # To be honest, this is a very crude implementation. I would appreciate PRs for improvement.
        servers = await get_server_prayer_times_details()
        for server in servers:
            channel_id = server[2]
            channel = self.bot.get_channel(int(channel_id))
            calculation_method = server[3]
            location = server[4]
            time_zone = server[5]
            try:
                await self.evaluate_times(channel, em, time_zone, location, calculation_method)
            except Exception as e:
                print(e)

        users = await get_user_prayer_times_details()
        for user in users:
            user_id = user[0]
            channel = self.bot.get_user(int(user_id))
            location = user[1]
            time_zone = user[2]
            calculation_method = user[3]
            try:
                await self.evaluate_times(channel, em, time_zone, location, calculation_method)
            except:
                await delete_user_prayer_times_details(int(user_id))

    # If the task stops for whatever reason, restart it.
    @send_reminders.after_loop
    async def after_send_reminders(self):
        print('Reminder task stopped! Restarting.')
        self.send_reminders.start()

    async def evaluate_times(self, channel, em, time_zone, location, calculation_method):

        # Get the time at the timezone and convert it into a string.
        tz = timezone(time_zone)
        tz_time = datetime.now(tz).strftime('%H:%M')

        # Get the prayer times for the location.
        fajr, _, dhuhr, asr, hanafi_asr, maghrib, isha, _, _, date = await self.get_prayertimes(
            location, calculation_method)
        em.title = location
        success = False

        if tz_time == fajr:
            em.description = f"It is **Fajr** time in **{location}**! (__{fajr}__)" \
                             f"\n\n**Dhuhr** will be at __{dhuhr}__."
            success = True

        elif tz_time == dhuhr:
            em.description = f"It is **Dhuhr** time in **{location}**! (__{dhuhr}__)" \
                             f"\n\n**Asr** will be at __{asr}__."
            success = True

        elif tz_time == asr:
            em.description = f"It is **Asr** time in **{location}**! (__{asr}__)." \
                             f"\n\nFor Hanafis, Asr will be at __{hanafi_asr}__." \
                             f"\n\n**Maghrib** will be at __{maghrib}__."
            success = True

        elif tz_time == maghrib:
            em.description = f"It is **Maghrib** time in **{location}**! (__{maghrib}__)" \
                             f"\n\n**Isha** will be at __{isha}__."
            success = True

        elif tz_time == isha:
            em.description = f"It is **Isha** time in **{location}**! (__{isha}__)"
            success = True

        if success:
            await channel.send(embed=em)


def setup(bot):
    bot.add_cog(PrayerTimes(bot))
