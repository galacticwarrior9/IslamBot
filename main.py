"""
    This file is part of IslamBot.
    IslamBot is free software: you can redistribute it and/or modify
    it under the terms of version 3 of the GNU General Public License
    as published by the Free Software Foundation.
    Simply put, this means you can use the code for your own purposes on the *condition* that
    it is:
    (1) made open-source, and
    (2) credit is given.
    I don't know why you would though, it isn't great!
"""

import configparser
from discord.ext import commands
from utils import PrefixHandler


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
            return (*prefix_list, guild_prefix)
    else:
        return prefix_list

description = "A Discord bot with Islamic utilities."

cog_list = ['hadith', 'hijricalendar', 'prayertimes', 'quran-morphology', 'quran', 'tafsir', 'tafsir-english',
            'mushaf', 'dua', 'help', 'TopGG', 'settings']

bot = commands.AutoShardedBot(command_prefix=get_prefix, description=description)

bot.remove_command('help')

for cog in cog_list:
    bot.load_extension(cog)


@bot.event
async def on_ready():

    print(f'Logged in as {bot.user.name} ({bot.user.id}) on {len(bot.guilds)} servers')


bot.run(token)
