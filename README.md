


# IslamBot

[![Discord Bots](https://top.gg/api/widget/status/352815253828141056.svg)](https://top.gg/bot/352815253828141056)
[![Discord](https://img.shields.io/discord/610613297452023837?label=Support%20Server)](https://discord.gg/Ud3MHJR)
[![Discord Bots](https://top.gg/api/widget/lib/352815253828141056.svg?noavatar=true)](https://top.gg/bot/352815253828141056)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/e41e4204a93a43f7821e3bdd55e6410b)](https://www.codacy.com/manual/galacticwarrior9/IslamBot?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=galacticwarrior9/IslamBot&amp;utm_campaign=Badge_Grade)
![GitHub contributors](https://img.shields.io/github/contributors/galacticwarrior9/IslamBot)

An Islamic bot for Discord with the following features:

* *Qur'an*, with support for 75+ translations.
* *Tafsir*, with 7 available in English and 37 in Arabic.
* *Hadith* in English and Arabic, from [sunnah.com](https://sunnah.com).
* Prayer times for any location in the world. 
* The ability to view the morphology of every word in the Qur'an. 
* Conversions between the Hijri and Gregorian calendars.
* Visualisation of Qur'anic verses on a *mushaf*. 
* Duas from *Fortress of the Muslim* (Hisn al-Muslim)

### Contributors
Thank you to all those who have [contributed](https://github.com/galacticwarrior9/IslamBot/graphs/contributors) to the project.

Also, thank you to following people who are not listed in the above link:

* Caleb, on whose code most of this project was originally based on.
* ala/Burhan from the Durkastan server, who rewrote most of the Qur'an code.
* Mew, who graciously translated much of the documentation into Arabic. 

## Qur'an

### -quran
**-quran** allows you to quote verses from the Qur'an. You can optionally specify a translation (see **Valid Translations** below). If you do not, the bot will send the verses in English.

**To get a single verse:**
```
-quran <surah>:<verse> <translation>
```
For example:
```
-quran 1:1 french
```
**To get multiple verses:**
```
-quran <surah>:<firstVerse>-<lastVerse> <translation>
```
For example:
```
-quran 1:1-7 khattab 
```
The above command would quote Surah 1, Verses 1-7 (Surah al-Fatihah) using the translation of Dr Mustafa Khattab.

#### Valid translations

[Click here for a list of valid translations.](https://github.com/galacticwarrior9/islambot/blob/master/Translations.md)


#### -settranslation

**-settranslation** allows you to change the default translation of `-quran` on your server. You must have the `Administrator` permission to use this command. 

```
-settranslation <translation>
```

For example:

```
-settranslation sahih 
```
The above command would set the default Qur'an translation to Sahih International. 


[Click here for a list of valid translations.](https://github.com/galacticwarrior9/islambot/blob/master/Translations.md)


### -aquran
**-aquran** functions exactly like  **-quran**, but sends the verses in Arabic.

For example, to quote the first verse of the Qur'an:
```
-aquran 1:1
```

### -morphology
**-morphology** allows you to analyse the Arabic morphology of any word in the Qur'an.

```
-morphology surah:verse:word number
```

For example:
```
-morphology 1:2:4
```
The above would analyse the morphology of the 4th word of the 2nd verse of the 1st chapter of the Qur'an. The bot will also show the syntax of the verse the word is in, if the data is available.


### -mushaf
**-mushaf** sends the page containing a Qur'anic verse on a standard mushaf.
```
-mushaf <surah>:<verse>
```
For example:
```
-mushaf 1:2
```
The above would send an image of the page containing Qur'an 1:2 on a *Medina Mushaf*. 

If you want a page with color-coded *tajweed* rules, add 'tajweed' to the end of the command.

For example:
```
-mushaf 112:1 tajweed
```



## Tafsir (Commentaries on the Qur'an) 

### -atafsir
**-atafsir** allows you to quote from over 37 Arabic *tafaseer* (commentaries on the Qurʾān). A list of valid *tafaseer* is available [here](https://github.com/galacticwarrior9/islambot/blob/master/Tafsir.md).

```
-atafsir <surah>:<verse(s> [tafsir]
```

For example:

```
-atafsir 2:255 tabari
```

The above command would quote the tafsir of Ayatul Kursi from Tafsir al-Tabari.


### -tafsir
**-tafsir** allows you to quote the English tasfir (commentary) of verses from Tafsīr al-Jalālayn (`jalalayn`), Tafsīr Ibn Kathīr (`ibnkathir`), Tafsīr al-Tustarī (`tustari`), Rashīd al-Dīn Maybudī's Kashf al-Asrār (`kashf`), al-Qurayshi's Laṭāʾif al-Ishārāt (`qurayshi`), Tafsīr ʿAbd al-Razzāq al-Kāshānī (`kashani`) and al-Wahidi's Asbāb al-Nuzūl (`wahidi`). It works in the same manner as **-atafsir**.

```
-tafsir <surah>:<verse> <jalalayn/ibnkathir/kashf/tustari/qurayshi/kashani/wahidi>
```

For example:

```
-tafsir 1:1 ibnkathir
```
The above command would quote the tafsir of Surah al-Fatihah, verse 1 from Tafsir Ibn Kathir. 

## Dua 

### -dualist
Sends the list of available dua topics for `-dua`. 


### -dua
**-dua** allows you to get duas from *Fortress of the Muslim* (Hisn al-Muslim). 

```
-dua <dua topic from -dualist>
```

For example, to get duas for breaking fasts:
```
-dua breaking fast
```


## Hadith 

### -hadith
**-hadith** allows you to quote hadith from sunnah.com in English.

```
-hadith <hadith collection name> <book number>:<hadith number>
```

For example, to get the second hadith in Book 1 of Sahih Bukhari:
```
-hadith bukhari 1:2
```

The above would fetch the hadith from https://sunnah.com/bukhari/1/2

Alternatively, you can simply type the sunnah.com link in chat. The bot will then send it if it is able to. 


#### Hadith collection names 

| **Hadith Collection** | **Name for Bot** | **Supported Languages** |
|--|--|--|
| Musnad Ahmad ibn Hanbal | `ahmad` | English, Arabic | 
| Mishkat al-Masabih | `mishkat` | English, Arabic | 
| Sahih al-Bukhari | `bukhari` | Urdu, English, Arabic
| Sahih Muslim | `muslim` | English, Arabic
|  Jami' at-Tirmidhi | `tirmidhi` | English, Arabic
| Sunan Abi Dawud | `abudawud` | Urdu, English, Arabic
| Sunan an-Nasa'i | `nasai` | English, Arabic
| Muwatta Malik | `malik` | English, Arabic
| Riyadh as-Saliheen | `riyadussaliheen ` | English, Arabic
| Al-Adab al-Mufrad | `adab ` | English, Arabic
| Bulugh al-Maram | `bulugh ` | English, Arabic
| 40 Hadith Qudsi | `qudsi ` | English, Arabic
| 40 Hadith Nawawi | `nawawi ` | English, Arabic

40 Hadith Qudsi and Nawawi are only forty hadith long and therefore only need a hadith number. For example: `-hadith qudsi 32`


### -ahadith
**-ahadith** is the same as -hadith, but sends the hadith in Arabic.

### -uhadith
**-uhadith** is the same as -hadith, but sends the hadith in Urdu. Only Sahih al-Bukhari and Sunan Abu Dawud are available in Urdu.


## Prayer (Salaah) Times

The bot can also send the prayer times for any location. More precise locations will yield more accurate prayer times. 

```
-prayertimes <location>
```

For example:
```
-prayertimes Burj Khalifa, Dubai
```

..would send prayer times in the general area of the Burj Khalifa in Dubai. 


## Hijri Calendar

### -hijridate

This shows the current Hijri date (in the US).

### -converttohijri
Converts a Gregorian date to its corresponding Hijri date.

```
-converttohijri DD-MM-YY 
```

For example:
```
-converttohijri 31-08-2017
```

### -convertfromhijri
Converts a Hijri date to its corresponding Gregorian date.

For example, to convert 17 Muharram 1407:
```
-convertfromhijri 17-01-1407
```

## Settings

🔒 You must have the **Administrator** permission to use these commands.

### -prefix set

Sets a custom prefix for the bot on your server.

For example, to change the prefix to `+`, type:
```
-prefix set +
```

### -prefix remove
Removes the bot's custom prefix on your server.
