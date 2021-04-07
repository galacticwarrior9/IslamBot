import configparser
import discord
from discord.ext import commands
from discord.ext.commands import CommandNotFound
from discord_slash import SlashCommand
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

cog_list = {'hadith.hadith', 'hijri_calendar.hijri_calendar', 'quran.morphology', 'tafsir.tafsir', 'tafsir.arabic_tafsir',
            'quran.mushaf', 'dua.dua', 'miscellaneous.help', 'miscellaneous.TopGG', 'miscellaneous.settings',
            'hadith.transmitter_biographies', 'quran.quran', 'salaah.salaah_times', 'miscellaneous.utility'}

intents = discord.Intents(messages=True, guilds=True, reactions=True)

bot = commands.AutoShardedBot(command_prefix=get_prefix, description=description, case_insensitive=True,
                              intents=intents)
slash = SlashCommand(bot, sync_commands=True)

bot.remove_command('help')

for cog in cog_list:
    bot.load_extension(cog)


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} ({bot.user.id}) on {len(bot.guilds)} servers')


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        return


bot.run(token)
