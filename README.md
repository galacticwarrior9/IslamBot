

# IslamBot  
 ![GitHub contributors](https://img.shields.io/github/contributors/galacticwarrior9/IslamBot) [![Discord](https://img.shields.io/discord/610613297452023837?label=Support%20Server)](https://discord.gg/Ud3MHJR)  

**IslamBot** is an open-source Discord bot that provides several utilities useful for the study and practice of Islam. Features include:
  
* *Qur'an*, with support for [100+ translations](https://github.com/galacticwarrior9/IslamBot/wiki/Qur%27an-Translation-List).  
* *Hadith* in English and Arabic, from [sunnah.com](https://sunnah.com).  
* Get prayer times for any location, with the ability to change the calculation method.
*  *Tafsir*, with support for many [*tafasir*](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List).
* Convert between the Hijri and Gregorian calendars.  
* Fetch specific Qur'anic verses and pages from the *mushaf*.   
* Browse duas from *Fortress of the Muslim*.

## Documentation
Instructions on how to use the bot are available on the [wiki](https://github.com/galacticwarrior9/IslamBot/wiki). 

 - [Qur'an](https://github.com/galacticwarrior9/IslamBot/wiki/Qur%27an)
	 - [Translations](v)
 - [Hadith](https://github.com/galacticwarrior9/IslamBot/wiki/Hadith)
 - [Prayer Times](https://github.com/galacticwarrior9/IslamBot/wiki/Prayer-Times)
 - [Tafsir](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir)
	 - [*Tafasir*](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List)
 - [Dua](https://github.com/galacticwarrior9/IslamBot/wiki/Dua)
 - [Mushaf](https://github.com/galacticwarrior9/IslamBot/wiki/Mushaf)
 - [Calendar](https://github.com/galacticwarrior9/IslamBot/wiki/Calendar)

## Information for Developers

The Python packages required to run the bot are listed in [requirements.txt](https://github.com/galacticwarrior9/IslamBot/blob/master/requirements.txt) file. Options are retrieved from a file named `config.ini` in the base directory. An example `config.ini` can be found [here](https://github.com/galacticwarrior9/IslamBot/blob/master/example_config.ini).

To run the bot, you will need to exclude the TopGG extension from loading. It is recommended to only sync commands with your test server to avoid falling afoul of Discord's strict rate limits on global command synchronisation. Please consult the comments in [main.py](https://github.com/galacticwarrior9/IslamBot/blob/master/main.py) for more information.

You can use the `/reload` command to reload extensions and commands while the bot is running. If you have made a change to a command, reload its extension first before reloading commands.

If you lack a sunnah.com API key, you may use the demo key provided in the [API documentation](https://sunnah.stoplight.io/docs/api/) for testing. Be aware that this key has a low request limit.
