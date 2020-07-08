from discord.ext import commands
import discord


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ihelp")
    async def ihelp(self, ctx, *, section: str = "main"):

        section = section.lower()

        if section == "main":
            em = discord.Embed(title='Help', colour=0x0a519c, description="**Type -ihelp <category>**, e.g. `-ihelp quran`")
            em.add_field(name="Categories", value='\n» Quran\n» Hadith\n» Tafsir\n» Prayer Times\n» Dua\n» Calendar',
                         inline=False)
            em.add_field(name="Links", value="• [Vote](https://top.gg/bot/352815253828141056/vote)\n"
                                             "• [Support Server](https://discord.gg/Ud3MHJR)\n"
                                             "• [Documentation](https://github.com/galacticwarrior9/islambot/blob/master/README.md)\n"
                                             "• [Contributors](https://github.com/galacticwarrior9/IslamBot/graphs/contributors)"
                                             "• [GitHub](https://github.com/galacticwarrior9/islambot)\n"
                                             "• [Iqra](https://top.gg/bot/706134327200841870)"
                         , inline=False)
            em.set_thumbnail(url='https://images-na.ssl-images-amazon.com/images/I/71CYXRJdY4L.png')
            await ctx.send(embed=em)

        elif section == "quran":
            em = discord.Embed(title="Qurʼān", colour=0x0a519c, description='[Click here for the translations list.](https://github.com/galacticwarrior9/islambot/blob/master/Translations.md)')
            em.add_field(name="-quran", inline=True, value="Gets Qur'anic verses."
                                              "\n\n`-quran <surah>:<ayah> <optional translation>`"
                                              "\n\nExample: `-quran 1:1`"
                                              "\n\n`-quran <surah:<first ayah>-<last ayah> <optional translation>`"
                                              "\n\nExample: `-quran 1:1-7 turkish`")

            em.add_field(name="-aquran", inline=True, value="Gets Qur'anic verses in Arabic."
                                              "\n\n`-aquran <surah>:<ayah>`"
                                              "\n\nExample: `-aquran 1:1`"
                                              "\n\n`-quran <surah>:<first ayah>-<last ayah>`"
                                              "\n\nExample: `-aquran 1:1-7`")

            em.add_field(name="-morphology", inline=True, value="View the morphology of a Qur'anic word."
                                              "\n\n`-morphology <surah>:<ayah>:<word number>`"
                                              "\n\nExample: `-aquran 2:255:1`")

            em.add_field(name="-mushaf", inline=True, value="View a Qur'anic verse on a *mushaf*."
                                              "\n\n`-mushaf <surah>:<ayah>`"
                                              "\n\nExample: `-mushaf 1:1`"
                                              "\n\nAdd 'tajweed' to the end of the command for color-coded tajweed rules."
                                              "\n\nExample: `-mushaf 1:1 tajweed`")

            em.add_field(name="-settranslation", inline=True, value="Changes the default Qur'an translation."
                                              "\n\n`-settranslation <translation>`"
                                              "\n\nExample: `-settranslation khattab`"
                                              "\n\nYou must have the **Administrator** permission to use this command.")

            await ctx.send(embed=em)

        elif section == "tafsir":
            em = discord.Embed(title="Tafsīr", colour=0x0a519c, description='[Click here for the tafsir list.](https://github.com/galacticwarrior9/islambot/blob/master/Tafsir.md)')

            em.add_field(name="-tafsir", inline=True, value="Gets tafsīr in English."
                                              "\n\n`-tafsir <surah>:<ayah> <optional tafsir name>`"
                                              "\n\nExample: `-tafsir 1:1`"
                                              "\n\nExample 2: `-tafsir 1:1 ibnkathir`")

            em.add_field(name="-atafsir", inline=True, value="Gets tafsīr in Arabic."
                                              "\n\n`-atafsir <surah>:<ayah> <optional tafsir name>`"
                                              "\n\nExample: `-atafsir 1:1`"
                                              "\n\nExample 2: `-atafsir 1:1 zamakhshari`")

            await ctx.send(embed=em)

        elif section == "calendar":
            em = discord.Embed(title="Hijri Calendar", colour=0x0a519c)

            em.add_field(name="-hijridate", inline=True, value="Gets the current Hijri date (in the US)")

            em.add_field(name="-converttohijri", inline=True, value="Converts a Gregorian date to its Hijri counterpart."
                                              "\n\n`-converttohijri DD-MM-YYYY`"
                                              "\n\nExample: `-converttohijri 15-01-2020`")

            em.add_field(name="-convertfromhijri", inline=True, value="Converts a Hijri date to its Gregorian counterpart."
                                              "\n\n`-convertfromhijri DD-MM-YYYY`"
                                              "\n\nExample: `-convertfromhijri 15-06-1441`")
            await ctx.send(embed=em)

        elif section == "hadith":
            em = discord.Embed(title="Hadith", colour=0x0a519c, description="These commands fetch hadith from *sunnah.com*.")

            em.add_field(name="-hadith", inline=True, value="Gets a sunnah.com hadith in English."
                                                            "\n\n`-hadith <collection> <book number>:<hadith number>`"
                                                            "\n\nExample: `-hadith bukhari 97:6` for http://sunnah.com/bukhari/97/6")

            em.add_field(name="-ahadith", inline=True, value="Gets a sunnah.com hadith in Arabic."
                                                            "\n\n`-ahadith <collection> <book number>:<hadith number>`"
                                                            "\n\nExample: `-ahadith bukhari 97:6` for http://sunnah.com/bukhari/97/6")

            em.add_field(name="-uhadith", inline=True, value="Gets a sunnah.com hadith in Urdu."
                                                            "\n\n`-uhadith <collection> <book number>:<hadith number>`"
                                                            "\n\nExample: `-uhadith bukhari 1:1` for http://sunnah.com/bukhari/1/1"
                                                            "\n\n*Only Sahih al-Bukhari and Sunan Abu Dawud are available in Urdu.*")

            await ctx.send(embed=em)

        elif section == "prayer times":
            em = discord.Embed(title="Prayer Times", colour=0x0a519c)

            em.add_field(name="-prayertimes", inline=True, value="Gets prayer times for a specified location."
                                                                 "\n\n`-prayertimes <location>`"
                                                                 "\n\nExample: `-prayertimes Burj Khalifa, Dubai`")

            await ctx.send(embed=em)

        elif section == "dua":
            em = discord.Embed(title="Dua", colour=0x0a519c)
            em.add_field(name="-dualist", inline=True, value="Shows a list of duas.")
            em.add_field(name="-dua", inline=True, value="Gets a dua for a topic."
                                                         "\n\n__Usage__"
                                                         "\n\n`-dua <topic>`"
                                                         "\n\nExample: `-dua forgiveness`"
                                                         "\n\nSee `-dualist` for a list of topics.")
            await ctx.send(embed=em)


# Register as cog
def setup(bot):
    bot.add_cog(Help(bot))
