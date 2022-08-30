import asyncio
import configparser

import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound

from utils.utils import PrefixHandler

config = configparser.ConfigParser()
config.read('config.ini')

token = config['IslamBot']['token']
default_prefix = config['IslamBot']['default_prefix']

prefix_list = default_prefix


async def get_prefix(_, message):
    try:
        guild_id = message.guild.id
    except AttributeError:
        return prefix_list
    if PrefixHandler.has_custom_prefix(guild_id):
        guild_prefix = PrefixHandler.get_prefix(guild_id)
        if guild_prefix:
            return *prefix_list, guild_prefix
    else:
        return prefix_list


description = "A Discord bot with Islamic utilities."

cog_list = {'hadith.hadith', 'hijri_calendar.hijri_calendar', 'quran.morphology', 'tafsir.tafsir',
            'tafsir.arabic_tafsir',
            'quran.mushaf', 'dua.dua', 'miscellaneous.help', 'miscellaneous.TopGG', 'miscellaneous.settings',
            'hadith.transmitter_biographies', 'quran.quran', 'salaah.salaah_times', 'miscellaneous.utility'}

intents = discord.Intents(messages=True, guilds=True, reactions=True)


class IslamBot(commands.AutoShardedBot):
    def __init__(self) -> None:
        super().__init__(command_prefix=get_prefix, description=description, case_insensitive=True, intents=intents)

    #async def setup_hook(self):
    #    print(f'Logged in as {self.user.name} ({self.user.id}) on {len(self.guilds)} servers')


bot = IslamBot()


async def main():
    async with bot:
        await bot.load_extension("quran.quran")
        await bot.load_extension("quran.mushaf")
        await bot.start(token)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id}) on {len(bot.guilds)} servers')
    await bot.tree.sync(guild=discord.Object(308241121165967362))

asyncio.run(main())
