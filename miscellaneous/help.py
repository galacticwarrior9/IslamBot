import discord
from discord.ext import commands
from discord_slash import cog_ext, SlashContext
from discord_slash.utils.manage_commands import create_option

from utils.slash_utils import generate_choices_from_list

SECTIONS = ['Main', 'Quran', 'Hadith', 'Tafsir', 'Prayer Times', 'Dua', 'Calendar', 'Settings']


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def _help(self, ctx, pre, section):
        section = section.lower()

        if section == "main":
            em = discord.Embed(title='IslamBot Help / أمر المساعدة', colour=0xdeb949,
                               description=f"**Type {pre}ihelp <category>**, e.g. `{pre}ihelp quran`\n")
            if pre == '/':
                em.description = "**Type /help <category>**, e.g. `/help quran`\n"
            em.add_field(name="Categories",
                         value='\n» Quran\n» Hadith\n» Tafsir\n» Prayer Times\n» Dua\n» Calendar\n» Settings',
                         inline=False)
            em.add_field(name="Links", value="• [Vote / تصويت](https://top.gg/bot/352815253828141056/vote)\n"
                                             "• [Support Server / سيرفر المساعدة](https://discord.gg/Ud3MHJR)\n"
                                             "• [Documentation / لتوثيق](https://github.com/galacticwarrior9/islambot/blob/master/README.md)\n"
                                             "• [Contributors / المساعدين](https://github.com/galacticwarrior9/IslamBot/graphs/contributors)\n"
                                             "• [GitHub / غيت هاب](https://github.com/galacticwarrior9/islambot)\n"
                                             "• [Donate](https://github.com/galacticwarrior9/islambot)\n"
                                             "• [Iqra / اقرأ بوت](https://top.gg/bot/706134327200841870)"
                         , inline=False)
            em.set_thumbnail(url='https://images-na.ssl-images-amazon.com/images/I/71CYXRJdY4L.png')
            await ctx.send(embed=em)

        elif section == "quran":
            em = discord.Embed(title="Qurʼān", colour=0x0a519c,
                               description='[Click here for the translations list.](https://github.com/galacticwarrior9/IslamBot/wiki/Qur%27an-Translation-List)')
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

            em.add_field(name=f"{pre}mushaf", inline=True, value="View a Qur'anic verse on a standard *mushaf*."
                                                                 f"\n\n`{pre}mushaf <surah>:<ayah>`"
                                                                 f"\n\nExample: `{pre}mushaf 1:1`"
                                                                 "\n\nAdd 'tajweed' to the end of the command for color-coded tajweed rules."
                                                                 f"\n\nExample: `{pre}mushaf 1:1 tajweed`")

            em.add_field(name=f"{pre}rmushaf", inline=True, value="Gets a random page of a standard *mushaf*."
                                                                  "\n\nAdd 'tajweed' to the end of the command for color-coded tajweed rules."
                                                                  f"\n\nExample: `{pre}rmushaf tajweed`")

            em.add_field(name=f"{pre}surah", inline=True, value="Get information about a surah."
                                                                f"\n\n`{pre}surah <surah number>`"
                                                                f"\n\nExample: `{pre}surah 1`")

            em.add_field(name=f"{pre}settranslation", inline=True, value="Changes the default Qur'an translation."
                                                                         f"\n\n`{pre}settranslation <translation>`"
                                                                         f"\n\nExample: `{pre}settranslation khattab`"
                                                                         "\n\nYou must have the **Administrator** permission to use this command.")

            em.add_field(name=f"{pre}rquran", inline=True, value="Gets a random translated Qur'anic verse."
                                                                 f"\n\n`{pre}rquran <translation>`"
                                                                 f"\n\nExample: `{pre}rquran khattab`")

            em.add_field(name=f"{pre}raquran", inline=True, value="Gets a random Qur'anic verse in Arabic."
                                                                 f"\n\n`{pre}raquran <translation>`")

            await ctx.send(embed=em)

        elif section == "tafsir":
            em = discord.Embed(title="Tafsīr", colour=0x0a519c,
                               description='[Click here for the tafsir list.](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List)')

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

            em.add_field(name=f"{pre}converttohijri", inline=True,
                         value="Converts a Gregorian date to its Hijri counterpart."
                               f"\n\n`{pre}converttohijri DD-MM-YYYY`"
                               f"\n\nExample: `{pre}converttohijri 15-01-2020`")

            em.add_field(name=f"{pre}convertfromhijri", inline=True,
                         value="Converts a Hijri date to its Gregorian counterpart."
                               f"\n\n`{pre}convertfromhijri DD-MM-YYYY`"
                               f"\n\nExample: `{pre}convertfromhijri 15-06-1441`")
            await ctx.send(embed=em)

        elif section == "hadith":
            em = discord.Embed(title="Hadith", colour=0x0a519c,
                               description="These commands fetch hadith from *sunnah.com*.")

            em.add_field(name=f"{pre}hadith", inline=True, value="Gets a sunnah.com hadith in English."
                                                                 f"\n\n `{pre}hadith <collection> <hadith number>`"
                                                                 f"\n\nExample: `{pre}hadith muslim 1051` for https://sunnah.com/muslim:1051")

            em.add_field(name=f"{pre}ahadith", inline=True, value="Gets a sunnah.com hadith in Arabic. "
                                                                  f"The usage is the same as `{pre}hadith`.")

            em.add_field(name=f"{pre}biography", inline=True, value="Gets the biography of a hadith transmitter "
                                                                    "or early Muslim from al-Dhahabi's *Siyar A'lam al-"
                                                                    "al-Nubala*."
                                                                    f"\n\n`{pre}biography <name of person in Arabic>`"
                                                                    f"\n\nExample: `{pre}biography عبد الله بن عباس`")

            em.add_field(name=f"{pre}rhadith", inline=True, value="Gets a random sunnah.com hadith in English from Riyadh as-Saliheen."
                                                                  f"The usage is `{pre}rhadith`.")

            em.add_field(name=f"{pre}rahadith", inline=True, value="Gets a random sunnah.com hadith in Arabic from Riyadh as-Saliheen."
                                                                  f"The usage is `{pre}rahadith`.")

            await ctx.send(embed=em)

        elif section == "prayer times":
            em = discord.Embed(title="Prayer Times", colour=0x0a519c)

            em.add_field(name=f"{pre}prayertimes", inline=True, value="Gets prayer times for a specified location."
                                                                      f"\n\n`{pre}prayertimes <location>`"
                                                                      f"\n\nExample: `{pre}prayertimes Burj Khalifa, Dubai`")

            em.add_field(name=f"{pre}methodlist", inline=True, value="Shows a list of calculation methods.")

            em.add_field(name=f"{pre}setcalculationmethod", inline=True, value="Sets the Calculation Method"
                                                                               "\n\n__Usage__"
                                                                               f"\n\n`{pre}setcalculationmethod <method number>`"
                                                                               f"\n\nExample: `{pre}setcalculationmethod 4`"
                                                                               f"\n\nSee `{pre}methodlist` for a list of methods.")

            await ctx.send(embed=em)

        elif section == "dua":
            em = discord.Embed(title="Dua", colour=0x0a519c)
            em.add_field(name=f"{pre}dualist", inline=True, value="Shows a list of duas.")
            em.add_field(name=f"{pre}dua", inline=True, value="Gets a dua for a topic."
                                                              "\n\n__Usage__"
                                                              f"\n\n`{pre}dua <topic>`"
                                                              f"\n\nExample: `{pre}dua forgiveness`"
                                                              f"\n\nSee `{pre}dualist` for a list of topics.")
            em.add_field(name=f"{pre}rdua", inline=True, value="Gets a random dua. "
                                                               f"The usage is `{pre}rdua`.")
            await ctx.send(embed=em)

        elif section == "settings":
            em = discord.Embed(title="Settings", colour=0x0a519c, description='🔒 You need the **Administrator** '
                                                                              'permission to use these commands.')
            em.add_field(name=f"{pre}prefix set", inline=True, value="Sets a custom prefix for the server."
                                                                     "\n\n__Usage__"
                                                                     f"\n\n`{pre}prefix set <new_prefix>`"
                                                                     f"\n\nExample: `{pre}prefix set +`")
            em.add_field(name=f"{pre}prefix remove", inline=True, value="Removes any custom prefix that was set."
                                                                        "\n\n__Usage__"
                                                                        f"\n\n`{pre}prefix remove`")
            await ctx.send(embed=em)

    @commands.command(name="ihelp")
    async def help(self, ctx, *, section: str = "Main"):
        await ctx.channel.trigger_typing()
        await self._help(ctx, ctx.prefix, section)

    @cog_ext.cog_slash(name="help", description="The help command for the bot.",
                       options=[
                           create_option(
                               name="section",
                               description="The section topic of help",
                               option_type=3,
                               choices=generate_choices_from_list(list(SECTIONS)),
                               required=False)])
    async def slash_help(self, ctx: SlashContext, section: str = "Main"):
        await ctx.defer()
        prefix = '/calendar ' if section.lower() == 'calendar' else '/'
        # `/calendar ` is the prefix because it's a base command with subcommands
        await self._help(ctx, prefix, section)


def setup(bot):
    bot.add_cog(Help(bot))
