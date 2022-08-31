from enum import Enum

import discord


class ErrorMessage(Enum):
    INVALID_TRANSLATION = "**Invalid translation**. List of translations: <https://github.com/galacticwarrior9/IslamBot/wiki/Qur%27an-Translation-List>"
    INVALID_AYAH = ":warning: There are only **{0}** verses in this surah."
    INVALID_SURAH_NUMBER = ":warning: **There are only 114 surahs.** Please choose a surah between 1 and 114."
    INVALID_SURAH_NAME = ":warning: **Invalid surah name!** Please try specifying its number instead."
    INVALID_ARABIC_TAFSIR = ":warning: **Invalid tafsir!** List of tafasir: <https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List#arabic-tafsir>"


async def respond_to_interaction_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
    hook = interaction.followup
    if isinstance(error, InvalidAyah):
        return await hook.send(content=ErrorMessage.INVALID_AYAH.value.format(error.num_verses))
    elif isinstance(error, InvalidSurahName):
        return await hook.send(content=ErrorMessage.INVALID_SURAH_NAME.value)
    elif isinstance(error, InvalidSurahNumber):
        return await hook.send(content=ErrorMessage.INVALID_SURAH_NUMBER.value)
    elif isinstance(error, InvalidTranslation):
        return await hook.send(content=ErrorMessage.INVALID_TRANSLATION.value)
    elif isinstance(error, InvalidArabicTafsir):
        return await hook.send(content=ErrorMessage.INVALID_ARABIC_TAFSIR.value)
    else:
        return await hook.send(f":warning: **An error occurred!** Code: {error}")


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