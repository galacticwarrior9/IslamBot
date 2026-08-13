import json
import os
import discord
from discord.ext import commands
from discord import app_commands

class IdaaStreaming(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channels = self.load_channels()

    def load_channels(self):
        file_path = os.path.join(os.path.dirname(__file__), 'channels.json')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading channels.json: {e}")
            return []

    async def channel_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        choices = []
        for channel in self.channels:
            name = channel.get('ar', 'Unknown Record')
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name, value=channel['value']))
                if len(choices) >= 25:
                    break
        return choices

    @app_commands.command(name="radio_play", description="Play a radio station (Idaa) in your voice channel")
    @app_commands.autocomplete(station=channel_autocomplete)
    async def radio_play(self, interaction: discord.Interaction, station: str):
        if not interaction.user.voice:
            return await interaction.response.send_message("You must be in a voice channel to use this command.", ephemeral=True)
            
        channel = interaction.user.voice.channel
        
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.move_to(channel)
        else:
            try:
                voice_client = await channel.connect()
            except discord.ClientException as e:
                return await interaction.response.send_message(f"Could not connect to the voice channel. Make sure I have permissions and PyNaCl is installed. Error: {e}", ephemeral=True)
            
        # station here is the URL (value), because in autocomplete we passed value
        # let's find the matching name for display
        station_name = next((c.get('ar') for c in self.channels if c.get('value') == station), "Unknown Station")

        if voice_client.is_playing():
            voice_client.stop()
            
        FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }
        
        await interaction.response.defer()
        
        try:
            source = discord.FFmpegPCMAudio(station, **FFMPEG_OPTIONS)
            voice_client.play(source, after=lambda e: print(f'Player error: {e}') if e else None)
            await interaction.followup.send(f"📻 Now playing **{station_name}** in {channel.mention}")
        except Exception as e:
            await interaction.followup.send(f"An error occurred while trying to play the station: {e}")

    @app_commands.command(name="radio_stop", description="Stop the radio and leave the voice channel")
    async def radio_stop(self, interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        if voice_client and voice_client.is_connected():
            await voice_client.disconnect()
            await interaction.response.send_message("📻 Stopped the radio and left the voice channel.")
        else:
            await interaction.response.send_message("I am not currently in a voice channel.", ephemeral=True)

    @app_commands.command(name="radio_list", description="List all available radio stations")
    async def radio_list(self, interaction: discord.Interaction):
        embed = discord.Embed(title="📻 محطات إذاعة القرآن الكريم", color=discord.Color.gold())
        description = ""
        for idx, channel in enumerate(self.channels, 1):
            name = channel.get('ar', 'Unknown')
            description += f"**{idx}.** {name}\n"
        
        embed.description = description
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(IdaaStreaming(bot))
