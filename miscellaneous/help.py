import discord
from discord import SelectOption
from discord.ext import commands

SELECT_OPTIONS = [
    SelectOption(label="Qur'an", value="quran", description="View help for the Qur'an commands."),
    SelectOption(label="Hadith", value="hadith", description="View help for the hadith commands."),
    SelectOption(label="Prayer Times", value="prayertimes", description="View help for the prayer time commands."),
    SelectOption(label="Tafsir", value="tafsir", description="View help for the tafsir commands."),
    SelectOption(label="Dua", value="dua", description="View help for the dua commands."),
    SelectOption(label="Calendar", value="calendar", description="View help for the Hijri calendar commands.")
]


class HelpMenu(discord.ui.View):
    def __init__(self, *args, interaction: discord.Interaction, **kwargs):
        super().__init__(timeout=600)
        self.latest_interaction = interaction

    async def interaction_check(self, interaction: discord.Interaction):
        result = await super().interaction_check(interaction)
        self.latest_interaction = interaction
        if not result:
            await interaction.response.defer()
        return result

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True
        await self.latest_interaction.edit_original_response(view=self, content=":warning: This message has timed out.")

    @discord.ui.select(custom_id="islambot:help", placeholder="Select a help topic.", options=SELECT_OPTIONS)
    async def select_callback(self, interaction: discord.Interaction, menu: discord.ui.Select):
        interaction.response.defer()

        option = menu.values[0]

        if option == "quran":
            em = discord.Embed(title="Qurʼān", colour=0x558a25,
                               description='[Click here for the translations list.](https://github.com/galacticwarrior9/IslamBot/wiki/Qur%27an-Translation-List)')
            em.add_field(name="/quran", inline=True, value="Gets Qur'anic verses."
                                                           "\n\n`/quran <surah> <verse> <optional translation>`"
                                                           "\n\nExample: `/quran 2 255`"
                                                           "\n\n`/quran <surah> <first verse> <last verse> <optional translation>`"
                                                           "\n\nExample: `/quran 2 255 260 turkish`")

            em.add_field(name="/aquran", inline=True, value="Gets Qur'anic verses in Arabic."
                                                            f"\n\n`/aquran <surah> <verse>`"
                                                            f"\n\nExample: `/aquran 2 255`"
                                                            f"\n\n`/quran <surah> <first verse> <last verse>`"
                                                            f"\n\nExample: `/aquran 2 255 287`")

            em.add_field(name="/rquran", inline=True, value="Gets a random translated Qur'anic verse."
                                                            "\n\n`/rquran <translation>`"
                                                            "\n\nExample: `/rquran khattab`")

            em.add_field(name="/raquran", inline=True, value="Gets a random Qur'anic verse in Arabic.")

            em.add_field(name="/settranslation", inline=True, value="Changes the default Qur'an translation."
                                                                    "\n\n`/settranslation <translation>`"
                                                                    "\n\nExample: `/settranslation khattab`"
                                                                    "\n\nYou must have the **Administrator** permission to use this command.")

            em.add_field(name="/mushaf", inline=True, value="View a Qur'anic verse on a standard *mushaf*."
                                                            "\n\n`/mushaf <surah> <verse>`"
                                                            "\n\nExample: `/mushaf 2 255`" \
                                                            "\n\nThe `tajweed` parameter controls whether tajweed rules should be highlighted.")

            em.add_field(name="/rmushaf", inline=True, value="Gets a random page of a standard *mushaf*."
                                                             "\n\nAdd 'tajweed' to the end of the command for color-coded tajweed rules."
                                                             "\n\nExample: `/rmushaf tajweed`")

            em.add_field(name="/surah", inline=True, value="Get information about a surah."
                                                           "\n\n`/surah <surah number or namer>`"
                                                           "\n\nExample: `/surah 1`")

            em.add_field(name="/morphology", inline=True, value="View the morphology of a Qur'anic word."
                                                                "\n\n`/morphology <surah> <verse> <word number>`"
                                                                "\n\nExample: `/aquran 2 255 1`")

            await interaction.response.edit_message(embed=em)

        elif option == "tafsir":
            em = discord.Embed(title="Tafsīr", colour=0x558a25,
                               description="A tafsir is a commentary on the Qur'an. "
                                           "__**[Click here for the tafsir list.](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List)**__")

            em.add_field(name="/tafsir", inline=True, value="Gets the tafsīr of a verse."
                                                            "\n\n`/tafsir <surah> <verse> <optional tafsir name>`"
                                                            "\n\nExample: `/tafsir 2 255`"
                                                            "\n\nExample 2: `/tafsir 2 255 ibnkathir`"
                                                            "\n\n[Click](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List#english) for a list of valid tafsirs.")

            em.add_field(name="/atafsir", inline=True, value="Gets the tafsīr of a verse in Arabic."
                                                             "\n\n`/atafsir <surah> <verse> <optional tafsir name>`"
                                                             "\n\nExample: `/atafsir 2 255`"
                                                             "\n\nExample 2: `/atafsir 2 255 zamakhshari`"
                                                             "\n\n[Click](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List#arabic-tafsir) for a list of valid tafsirs.")

            await interaction.response.edit_message(embed=em)

        elif option == "calendar":
            em = discord.Embed(title="Hijri Calendar", colour=0x558a25)

            em.add_field(name="/calendar hijri_date", inline=True, value="Gets the current Hijri date (in the US)")

            em.add_field(name="/calendar convert_to_hijri", inline=True,
                         value="Converts a Gregorian date to its Hijri counterpart.")

            em.add_field(name="/calendar convert_to_gregorian", inline=True,
                         value="Converts a Hijri date to its Gregorian counterpart.")

            await interaction.response.edit_message(embed=em)

        elif option == "hadith":
            em = discord.Embed(title="Hadith", colour=0x558a25,
                               description="These commands fetch hadith from **[sunnah.com](https://sunnah.com)**.")

            em.add_field(name="/hadith", inline=True, value="Gets a sunnah.com hadith in English."
                                                            "\n\n `/hadith <collection> <hadith number>`"
                                                            "\n\nExample: `/hadith muslim 1051` for https://sunnah.com/muslim:1051")

            em.add_field(name="/ahadith", inline=True, value="Gets a sunnah.com hadith in Arabic. "
                                                             "The usage is the same as `/hadith`.")

            em.add_field(name="/rhadith", inline=True,
                         value="Gets a random sunnah.com hadith in English from Riyadh as-Saliheen. "
                               "The usage is `/rhadith`.")

            em.add_field(name="/rahadith", inline=True,
                         value="Gets a random sunnah.com hadith in Arabic from Riyadh as-Saliheen. "
                               "The usage is `/rahadith`.")

            em.add_field(name="/biography", inline=True, value="Gets the biography of a hadith transmitter "
                                                               "or early Muslim from al-Dhahabi's *Siyar A'lam al-"
                                                               "al-Nubala*.")

            await interaction.response.edit_message(embed=em)

        elif option == "prayertimes":
            em = discord.Embed(title="Prayer Times", colour=0x558a25)

            em.add_field(name="/prayertimes get", inline=True, value="Gets prayer times for a specified location.")

            em.add_field(name="/prayertimes set_calculation_method", inline=True,
                         value="Sets the calculation method used in `/prayertimes get`")

            em.add_field(name="/prayertimes list_calculation_methods", inline=True,
                         value="Shows a list of calculation methods.")

            await interaction.response.edit_message(embed=em)

        elif option == "dua":
            em = discord.Embed(title="Dua", colour=0x558a25)
            em.add_field(name="/dualist", inline=True, value="Shows a list of duas.")
            
            em.add_field(name="/dua", inline=True, value="Gets a dua for a topic."
                                                         "\n\n__Usage__"
                                                         "\n\n`/dua <topic>`"
                                                         "\n\nExample: `/dua forgiveness`"
                                                         "\n\nSee `/dualist` for a list of topics.")
            
            em.add_field(name="/rdua", inline=True, value="Gets a random dua.")
            
            await interaction.response.edit_message(embed=em)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="help", description="Get the list of commands and links for IslamBot.")
    async def help(self, interaction: discord.Interaction):
        em = discord.Embed(title='IslamBot Help / أمر المساعدة', colour=0xdeb949)
        em.description = "**IslamBot** is a Discord bot that allows you to browse the Qur'an, fetch hadith, look up" \
                         " prayer times, read tafsir and more." \
                         "\n\nSuggestions, contributions and bug reports are welcome on the [support server](" \
                         "https://discord.gg/Ud3MHJR) and the [GitHub](https://github.com/galacticwarrior9/islambot)." \
                         "\n\nIf you benefit from the bot, please consider [donating](https://ko-fi.com/zaify)."
        em.add_field(name="Links", inline=False,
                     value="• [Vote / تصويت](https://top.gg/bot/352815253828141056/vote)\n"
                           "• [Support Server / سيرفر المساعدة](https://discord.gg/Ud3MHJR)\n" 
                           "• [Documentation / لتوثيق](https://github.com/galacticwarrior9/islambot/blob/master/README.md)\n"
                           "• [Contributors / المساعدين](https://github.com/galacticwarrior9/IslamBot/graphs/contributors)\n"
                           "• [Iqra / اقرأ بوت](https://top.gg/bot/706134327200841870)")

        em.set_thumbnail(url='https://images-na.ssl-images-amazon.com/images/I/71CYXRJdY4L.png')

        await interaction.response.send_message(embed=em, view=HelpMenu(interaction=interaction), ephemeral=True)


async def setup(bot):
    await bot.add_cog(Help(bot))
