from enum import Enum

import discord
import pymysql
from discord.app_commands import MissingPermissions


class ErrorMessage(Enum):
    INVALID_TRANSLATION = "**Invalid translation**. List of translations: <https://github.com/galacticwarrior9/IslamBot/wiki/Qur%27an-Translation-List>"
    INVALID_AYAH = ":warning: There are only **{0}** verses in this surah."
    INVALID_SURAH_NUMBER = ":warning: **There are only 114 surahs.** Please choose a surah between 1 and 114."
    INVALID_SURAH_NAME = ":warning: **Invalid surah name!** Please try specifying its number instead."
    INVALID_TAFSIR = ":warning: **Invalid tafsir!** List of tafasir: <https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List#arabic-tafsir>"
    INVALID_ARABIC_TAFSIR = ":warning: **Invalid tafsir!** List of tafasir: <https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List#arabic-tafsir>"
    DATABASE_UNREACHABLE = "Could not contact database. Please report this on the support server!"
    ADMINISTRATOR_REQUIRED = "🔒 You need the **Administrator** permission to use this command."


async def respond_to_interaction_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    if isinstance(error, InvalidAyah):
        await reply_to_interaction(interaction, ErrorMessage.INVALID_AYAH.value.format(error.num_verses))
    elif isinstance(error, InvalidSurahName):
        await reply_to_interaction(interaction, ErrorMessage.INVALID_SURAH_NAME.value)
    elif isinstance(error, InvalidSurahNumber):
        await reply_to_interaction(interaction, ErrorMessage.INVALID_SURAH_NUMBER.value)
    elif isinstance(error, InvalidTranslation):
        await reply_to_interaction(interaction, ErrorMessage.INVALID_TRANSLATION.value)
    elif isinstance(error, InvalidTafsir):
        await reply_to_interaction(interaction, ErrorMessage.INVALID_TAFSIR.value)
    elif isinstance(error, InvalidArabicTafsir):
        await reply_to_interaction(interaction, ErrorMessage.INVALID_ARABIC_TAFSIR.value)
    elif isinstance(error, MissingPermissions):
        await reply_to_interaction(interaction, ErrorMessage.ADMINISTRATOR_REQUIRED.value)
    elif isinstance(error, pymysql.err.OperationalError):
        print(error)
        await reply_to_interaction(interaction, ErrorMessage.DATABASE_UNREACHABLE.value)
    else:
        print(error)
        await reply_to_interaction(interaction, f":warning: **An error occurred!** Code: {error}")


async def reply_to_interaction(interaction: discord.Interaction, message: str):
    """ Safely replies to an interaction, taking into consideration whether it has already been responded to. """
    if interaction.response.is_done():
        await interaction.followup.send(content=message)
    else:
        await interaction.response.send_message(content=message)


class InvalidAyah(discord.app_commands.AppCommandError):
    def __init__(self, num_verses, *args, **kwargs):
        self.num_verses = num_verses
        super().__init__(*args)


class InvalidSurahNumber(discord.app_commands.AppCommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)


class InvalidSurahName(discord.app_commands.AppCommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)


class InvalidTranslation(discord.app_commands.AppCommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)


class InvalidArabicTafsir(discord.app_commands.AppCommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)


class InvalidTafsir(discord.app_commands.AppCommandError):
    def __init__(self, *args, **kwargs):
        super().__init__(*args)