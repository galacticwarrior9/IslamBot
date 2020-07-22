from discord.ext import commands
import discord


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ihelp")
    async def ihelp(self, ctx, *, section: str = "main"):

        pre= ctx.prefix

        section = section.lower()

        if section == "main":
            em = discord.Embed(title='Help', colour=0x0a519c, description="**Type -ihelp <category>**, e.g. `-ihelp quran`")
            em.add_field(name="Categories", value='\n» Quran\n» Hadith\n» Tafsir\n» Prayer Times\n» Dua\n» Calendar\n» Settings' ,
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
            em.add_field(name=f"{pre}quran", inline=True, value="Gets Qur'anic verses."
                                              f"\n\n`{pre}quran <surah>:<ayah> <optional translation>`"
                                              f"\n\nExample: `{pre}quran 1:1`"
                                              f"\n\n`{pre}quran <surah:<first ayah>-<last ayah> <optional translation>`"
                                              f"\n\nExample: `{pre}quran 1:1-7 turkish`")

            em.add_field(name=f"{pre}aquran", inline=True, value="Gets Qur'anic verses in Arabic."
                                              f"\n\n`{pre}aquran <surah>:<ayah>`"
                                              f"\n\nExample: `{pre}aquran 1:1`"
                                              f"\n\n`{pre}quran <surah>:<first ayah>-<last ayah>`"
                                              f"\n\nExample: `{pre}aquran 1:1-7`")

            em.add_field(name=f"{pre}morphology", inline=True, value="View the morphology of a Qur'anic word."
                                              f"\n\n`{pre}morphology <surah>:<ayah>:<word number>`"
                                              f"\n\nExample: `{pre}aquran 2:255:1`")

            em.add_field(name=f"{pre}mushaf", inline=True, value="View a Qur'anic verse on a *mushaf*."
                                              f"\n\n`{pre}mushaf <surah>:<ayah>`"
                                              f"\n\nExample: `{pre}mushaf 1:1`"
                                              "\n\nAdd 'tajweed' to the end of the command for color-coded tajweed rules."
                                              f"\n\nExample: `{pre}mushaf 1:1 tajweed`")

            em.add_field(name=f"{pre}settranslation", inline=True, value="Changes the default Qur'an translation."
                                              f"\n\n`{pre}settranslation <translation>`"
                                              f"\n\nExample: `{pre}settranslation khattab`"
                                              "\n\nYou must have the **Administrator** permission to use this command.")

            await ctx.send(embed=em)

        elif section == "tafsir":
            em = discord.Embed(title="Tafsīr", colour=0x0a519c, description='[Click here for the tafsir list.](https://github.com/galacticwarrior9/islambot/blob/master/Tafsir.md)')

            em.add_field(name=f"{pre}tafsir", inline=True, value="Gets tafsīr in English."
                                              f"\n\n`{pre}tafsir <surah>:<ayah> <optional tafsir name>`"
                                              f"\n\nExample: `{pre}tafsir 1:1`"
                                              f"\n\nExample 2: `{pre}tafsir 1:1 ibnkathir`")

            em.add_field(name=f"{pre}atafsir", inline=True, value="Gets tafsīr in Arabic."
                                              f"\n\n`{pre}atafsir <surah>:<ayah> <optional tafsir name>`"
                                              f"\n\nExample: `{pre}atafsir 1:1`"
                                              f"\n\nExample 2: `{pre}atafsir 1:1 zamakhshari`")

            await ctx.send(embed=em)

        elif section == "calendar":
            em = discord.Embed(title="Hijri Calendar", colour=0x0a519c)

            em.add_field(name=f"{pre}hijridate", inline=True, value="Gets the current Hijri date (in the US)")

            em.add_field(name=f"{pre}converttohijri", inline=True, value="Converts a Gregorian date to its Hijri counterpart."
                                              f"\n\n`{pre}converttohijri DD-MM-YYYY`"
                                              f"\n\nExample: `{pre}converttohijri 15-01-2020`")

            em.add_field(name=f"{pre}convertfromhijri", inline=True, value="Converts a Hijri date to its Gregorian counterpart."
                                              f"\n\n`{pre}convertfromhijri DD-MM-YYYY`"
                                              f"\n\nExample: `{pre}convertfromhijri 15-06-1441`")
            await ctx.send(embed=em)

        elif section == "hadith":
            em = discord.Embed(title="Hadith", colour=0x0a519c, description="These commands fetch hadith from *sunnah.com*.")

            em.add_field(name=f"{pre}hadith", inline=True, value="Gets a sunnah.com hadith in English."
                                                            f"\n\n`{pre}hadith <collection> <book number>:<hadith number>`"
                                                            f"\n\nExample: `{pre}hadith bukhari 97:6` for http://sunnah.com/bukhari/97/6")

            em.add_field(name=f"{pre}ahadith", inline=True, value="Gets a sunnah.com hadith in Arabic."
                                                            f"\n\n`{pre}ahadith <collection> <book number>:<hadith number>`"
                                                            f"\n\nExample: `{pre}ahadith bukhari 97:6` for http://sunnah.com/bukhari/97/6")

            em.add_field(name=f"{pre}uhadith", inline=True, value="Gets a sunnah.com hadith in Urdu."
                                                            f"\n\n`{pre}uhadith <collection> <book number>:<hadith number>`"
                                                            f"\n\nExample: `{pre}uhadith bukhari 1:1` for http://sunnah.com/bukhari/1/1"
                                                            "\n\n*Only Sahih al-Bukhari and Sunan Abu Dawud are available in Urdu.*")

            await ctx.send(embed=em)

        elif section == "prayer times":
            em = discord.Embed(title="Prayer Times", colour=0x0a519c)

            em.add_field(name=f"{pre}prayertimes", inline=True, value="Gets prayer times for a specified location."
                                                                 f"\n\n`{pre}prayertimes <location>`"
                                                                 f"\n\nExample: `{pre}prayertimes Burj Khalifa, Dubai`")

            await ctx.send(embed=em)

        elif section == "dua":
            em = discord.Embed(title="Dua", colour=0x0a519c)
            em.add_field(name=f"{pre}dualist", inline=True, value="Shows a list of duas.")
            em.add_field(name=f"{pre}dua", inline=True, value="Gets a dua for a topic."
                                                         "\n\n__Usage__"
                                                         f"\n\n`{pre}dua <topic>`"
                                                         f"\n\nExample: `{pre}dua forgiveness`"
                                                         "\n\nSee `-dualist` for a list of topics.")
            await ctx.send(embed=em)

        elif section == "settings" or section == "settings".upper():
            em = discord.Embed(title="Settings",colour=0x0a519c)
            em.add_field(name=f"{pre}prefix set", inline=True, value="Sets a new prefix for the server"
                                                        "\n\n__Usage__"
                                                        f"\n\n`{pre}set <new_prefix>`"
                                                        "\n\nExample: `{prefix}set +`")
            em.add_field(name=f"{pre}prefix remove", inline=True, value="Removes any custom prefix that was set"
                                                         "\n\n__Usage__"
                                                         f"\n\n`{pre}prefix remove`"
                         )
            await ctx.send(embed=em)



# Register as cog
def setup(bot):
    bot.add_cog(Help(bot))
