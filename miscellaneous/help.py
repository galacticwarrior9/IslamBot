import discord
from discord import SelectOption
from discord.ext import commands

SELECT_OPTIONS = [
    SelectOption(label="Qur'an", value="quran", description="View help for the Qur'an commands."),
    SelectOption(label="Hadith", value="hadith", description="View help for the hadith commands."),
    SelectOption(label="Prayer Times", value="prayertimes", description="View help for the prayer time commands."),
    SelectOption(label="Tafsir", value="tafsir", description="View help for the tafsir commands."),
    SelectOption(label="Dua", value="dua", description="View help for the dua commands."),
    SelectOption(label="Mushaf", value="mushaf", description="View help for the mushaf commands."),
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
        option = menu.values[0]

        if option == "quran":
            em = discord.Embed(title="Qurʼān", colour=0x558a25,
                               description='[Click here for the translations list.](https://github.com/galacticwarrior9/IslamBot/wiki/Qur%27an-Translation-List)')
            em.add_field(name="</quran:817163873730822199>", inline=True, value="Gets Qur'anic verses."
                                                           "\n\n`/quran <surah> <verse> <optional translation>`"
                                                           "\n\nExample: `/quran 2 255`"
                                                           "\n\n`/quran <surah> <first verse> <last verse> <optional translation>`"
                                                           "\n\nExample: `/quran 2 255 260 turkish`")

            em.add_field(name="</aquran:817163873730822198>", inline=True, value="Gets Qur'anic verses in Arabic."
                                                            f"\n\n`/aquran <surah> <verse>`"
                                                            f"\n\nExample: `/aquran 2 255`"
                                                            f"\n\n`/quran <surah> <first verse> <last verse>`"
                                                            f"\n\nExample: `/aquran 2 255 287`")

            em.add_field(name="</rquran:967584174586355733>", inline=True, value="Gets a random translated Qur'anic verse."
                                                            "\n\n`/rquran <translation>`"
                                                            "\n\nExample: `/rquran khattab`")

            em.add_field(name="</raquran:1001569600409972908>", inline=True, value="Gets a random Qur'anic verse in Arabic.")

            em.add_field(name="</settranslation:817163873730822200>", inline=True, value="Changes the default Qur'an translation."
                                                                    "\n\n`/settranslation <translation>`"
                                                                    "\n\nExample: `/settranslation khattab`"
                                                                    "\n\nYou must have the **Administrator** permission to use this command.")

            em.add_field(name="</surah:967584174586355734>", inline=True, value="Get information about a surah."
                                                           "\n\n`/surah <surah number or name>`"
                                                           "\n\nExample: `/surah 1`")

            em.add_field(name="</morphology:817163873760968744>", inline=True, value="View the morphology of a Qur'anic word."
                                                                "\n\n`/morphology <surah> <verse> <word number>`"
                                                                "\n\nExample: `/aquran 2 255 1`")

            await interaction.response.edit_message(embed=em)

        elif option == "tafsir":
            em = discord.Embed(title="Tafsīr", colour=0x558a25,
                               description="A tafsir is a commentary on the Qur'an. "
                                           "__**[Click here for the tafsir list.](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List)**__")

            # TODO: get id to make it work properly - by doing 0, it mentions the command but when users click on it, it won't fill in their text input
            em.add_field(name="</tafsir get:817163873730822197>", inline=True, value="Gets the tafsīr of a verse."
                                                            "\n\n`/tafsir <surah> <verse> <optional tafsir name>`"
                                                            "\n\nExample: `/tafsir 2 255`"
                                                            "\n\nExample 2: `/tafsir 2 255 ibnkathir`"
                                                            "\n\n[Click](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List#english) for a list of valid tafsirs.")

            em.add_field(name="</tafsir set_default_tafsir:817163873730822197>", inline=True, value="Changes the default tafsīr for the /tafsir get command."
                                                                           "\n\n`/tafsir set_default_tafsir <tafsir>`"
                                                                           "\n\nExample: `/tafsir set_default_tafsir jalalayn`"
                                                                           "\n\nYou must have the **Administrator** permission to use this command.")

            em.add_field(name="</atafsir get:817163873730822203>", inline=True, value="Gets the tafsīr of a verse in Arabic."
                                                             "\n\n`/atafsir <surah> <verse> <optional tafsir name>`"
                                                             "\n\nExample: `/atafsir 2 255`"
                                                             "\n\nExample 2: `/atafsir 2 255 zamakhshari`"
                                                             "\n\n[Click](https://github.com/galacticwarrior9/IslamBot/wiki/Tafsir-List#arabic-tafsir) for a list of valid tafsirs.")

            em.add_field(name="</atafsir set_default_atafsir:817163873730822203>", inline=True, value="Changes the default Arabic tafsīr for the /tafsir get command."
                                                                           "\n\n`/tafsir set_default_tafsir <tafsir>`"
                                                                           "\n\nExample: `/tafsir set_default_tafsir saadi`"
                                                                           "\n\nYou must have the **Administrator** permission to use this command.")

            await interaction.response.edit_message(embed=em)

        elif option == "calendar":
            em = discord.Embed(title="Hijri Calendar", colour=0x558a25)

            em.add_field(name="</calendar hijri_date:817163873760968745>", inline=True, value="Gets the current Hijri date.")

            em.add_field(name="</calendar to_hijri:817163873760968745>", inline=True,
                         value="Converts a Gregorian date to its Hijri counterpart.")

            em.add_field(name="</calendar to_gregorian:817163873760968745>", inline=True,
                         value="Converts a Hijri date to its Gregorian counterpart.")

            await interaction.response.edit_message(embed=em)

        elif option == "hadith":
            em = discord.Embed(title="Hadith", colour=0x558a25,
                               description="These commands fetch hadith from **[sunnah.com](https://sunnah.com)**.")

            em.add_field(name="</hadith:817163873730822202>", inline=True, value="Gets a sunnah.com hadith in English."
                                                            "\n\n `/hadith <collection> <hadith number>`"
                                                            "\n\nExample: `/hadith muslim 1051` for https://sunnah.com/muslim:1051")

            em.add_field(name="</ahadith:817163873730822201>", inline=True, value="Gets a sunnah.com hadith in Arabic. "
                                                             "The usage is the same as `/hadith`.")

            em.add_field(name="</rhadith:967584174586355738>", inline=True,
                         value="Gets a random sunnah.com hadith in English from Riyadh as-Saliheen. "
                               "The usage is `/rhadith`.")

            em.add_field(name="</rahadith:1001569600409972907>", inline=True,
                         value="Gets a random sunnah.com hadith in Arabic from Riyadh as-Saliheen. "
                               "The usage is `/rahadith`.")

            em.add_field(name="</biography:817163873760968746>", inline=True, value="Gets the biography of a hadith transmitter "
                                                               "or early Muslim from al-Dhahabi's *Siyar A'lam al-"
                                                               "al-Nubala*.")

            await interaction.response.edit_message(embed=em)

        elif option == "prayertimes":
            em = discord.Embed(title="Prayer Times", colour=0x558a25)

            em.add_field(name="</prayertimes get:817163873760968747>", inline=True, value="Gets prayer times for a specified location.")

            em.add_field(name="</prayertimes set_calculation_method:817163873760968747>", inline=True,
                         value="Sets the calculation method used in `/prayertimes get`")

            em.add_field(name="</prayertimes list_calculation_methods:817163873760968747>", inline=True,
                         value="Shows a list of calculation methods.")

            await interaction.response.edit_message(embed=em)

        elif option == "dua":
            em = discord.Embed(title="Dua", colour=0x558a25)
            em.add_field(name="</dualist:967584174586355741>", inline=True, value="Shows a list of duas.")

            em.add_field(name="</dua:817163873730822195>", inline=True, value="Gets a dua for a topic."
                                                         "\n\n__Usage__"
                                                         "\n\n`/dua <topic>`"
                                                         "\n\nExample: `/dua forgiveness`"
                                                         "\n\nSee `/dualist` for a list of topics.")

            em.add_field(name="</rdua:967584175047733278>", inline=True, value="Gets a random dua.")

            await interaction.response.edit_message(embed=em)

        elif option == "mushaf":
            em = discord.Embed(title="Mushaf", colour=0x558a25,
                               description="For these commands, the `tajweed` parameters control whether tajweed "
                                           "rules should be highlighted.")

            em.add_field(name="</mushaf by_ayah:817163873730822196>", inline=True, value="View a Qur'anic verse on a Medinian *mushaf*."
                                                                   "\n\n`/mushaf by_ayah <surah> <verse>`"
                                                                   "\n\nExample: `/mushaf 2 255`")

            em.add_field(name="</mushaf by_page:817163873730822196>", inline=True, value="Displays a page on the Medinian *mushaf*."
                                                                   "\n\n`/mushaf by_page <page number>`"
                                                                   "\n\nExample: `/mushaf 604`")
            em.add_field(name="</rmushaf:967584174586355736>", inline=True, value="Displays a random page on the Medinian *mushaf*.")

            await interaction.response.edit_message(embed=em)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.app_commands.command(name="help", description="Get the list of commands and links for IslamBot.")
    @discord.app_commands.allowed_installs(guilds=True, users=True)
    @discord.app_commands.allowed_contexts(guilds=True, dms=True, private_channels=True)
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
