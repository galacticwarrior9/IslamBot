import discord
from discord.ext import commands
from aiohttp import ClientSession

icon = 'https://www.muslimpro.com/img/muslimpro-logo-2016-250.png'

headers = {'content-type': 'application/json'}


class PrayerTimes(commands.Cog):

    def __init__(self, bot):
        self.session = ClientSession(loop = bot.loop)
        self.bot = bot
        self.hanafi_url = 'http://api.aladhan.com/timingsByAddress?address={0}&method=4&school=1'
        self.default_url = 'http://api.aladhan.com/timingsByAddress?address={0}&method=4&school=0'

    @commands.command(name="prayertimes")
    async def prayertimes(self, ctx, *, location):

        try:
            # Open URL and parse JSON
            async with self.session.get(self.default_url.format(location, '0'), headers=headers) as resp:
                data = await resp.json()

            # Assign variables from JSON
            fajr = data['data']['timings']['Fajr']
            sunrise = data['data']['timings']['Sunrise']
            dhuhr = data['data']['timings']['Dhuhr']
            default_asr = data['data']['timings']['Asr']
            maghrib = data['data']['timings']['Maghrib']
            isha = data['data']['timings']['Isha']
            imsak = data['data']['timings']['Imsak']
            midnight = data['data']['timings']['Midnight']
            date = data['data']['date']['readable']

            async with self.session.get(self.hanafi_url.format(location, '1'), headers=headers) as resp:
                data = await resp.json()

            hanafi_asr = data['data']['timings']['Asr']

            # Construct and send embed
            em = discord.Embed(colour=0x2186d3, title=date)
            em.set_author(name=f'Prayer Times for {location.title()}', icon_url=icon)
            em.add_field(name=f'**Imsak (إِمْسَاك)**', value=f'{imsak}', inline=True)
            em.add_field(name=f'**Fajr (صلاة الفجر)**', value=f'{fajr}', inline=True)
            em.add_field(name=f'**Sunrise (طلوع الشمس)**', value=f'{sunrise}', inline=True)
            em.add_field(name=f'**Ẓuhr (صلاة الظهر)**', value=f'{dhuhr}', inline=True)
            em.add_field(name=f'**Asr (صلاة العصر)**', value=f'{default_asr}', inline=True)
            em.add_field(name=f'**Asr - Ḥanafī School (صلاة العصر - حنفي)**', value=f'{hanafi_asr}', inline=True)
            em.add_field(name=f'**Maghrib (صلاة المغرب)**', value=f'{maghrib}', inline=True)
            em.add_field(name=f'**Isha (صلاة العشاء)**', value=f'{isha}', inline=True)
            em.add_field(name=f'**Midnight (منتصف الليل)**', value=f'{midnight}', inline=True)
            em.set_footer(text=f'Calculation Method: Umm al-Qura University')
            await ctx.send(embed=em)

        except:
            await ctx.send('**Invalid arguments!** Usage: `-prayertimes [location]`.\n'
                           'Example: `-prayertimes London`\n')


# Register as cog
def setup(bot):
    bot.add_cog(PrayerTimes(bot))
