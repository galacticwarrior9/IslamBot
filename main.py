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

config = configparser.ConfigParser()
config.read('config.ini')

token = config['IslamBot']['token']
prefix = config['IslamBot']['prefix']

description = "A Discord bot with Islamic utilities."

cog_list = ['hadith', 'hijricalendar', 'prayertimes', 'quran-morphology', 'quran', 'tafsir', 'tafsir-english',
            'mushaf', 'dua', 'help', 'TopGG']

bot = commands.AutoShardedBot(command_prefix=prefix, description=description)


@bot.event
async def on_ready():

    print(f'Logged in as {bot.user.name} ({bot.user.id}) on {len(bot.guilds)} servers')

    bot.remove_command('help')

    for cog in cog_list:
        bot.load_extension(cog)

bot.run(token)
