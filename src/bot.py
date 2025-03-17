import io
import os
import re
import logging
import sys
import uuid
import discord
from discord.ext import commands
import discord.app_commands
from dotenv import load_dotenv
import httpx
import yt_dlp

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')

logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter(
    fmt="\x1b[1;30m%(asctime)s \x1b[34m%(levelname)-8s \x1b[35m%(name)s \x1b[0m%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S")
handler.setFormatter(formatter)
logger.addHandler(handler)

intents = discord.Intents.all()
intents.message_content = True
intents.voice_states = True

bot = commands.Bot(command_prefix="$$$", intents=intents)

@bot.event
async def on_ready():
    logger.info(f'We have logged in as {bot.user}')
    logger.info(f'Bot ID: {bot.user.id}')
    try:
        synced = await bot.tree.sync()
        logger.info(f'Synced {len(synced)} commands')
    except Exception as e:
        logger.error('Error occurred when syncing command tree', exc_info=e)

@bot.tree.command(name='hello', description='Say hi to this fucking pervert!')
async def hello(interaction: discord.Interaction):
    await interaction.response.send_message('Sexo!')

@bot.tree.command(name='ytdlp', description='Download anything from xvideos.com')
async def ytdlp(interaction: discord.Interaction, url: str):
    logger.info(f'User @{interaction.user} requested to download `{url}`')

    await interaction.response.defer()
    
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best',
        'noplaylist': True,
        'quiet': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=False)

            if 'formats' not in info_dict:
                raise Exception("No downloadable formats found")
            
            best_format = info_dict['formats'][-1]
            stream_url = best_format['url']
            file_ext = best_format.get('ext') or 'unknown'
            title = info_dict.get('title', 'video')
            safe_title = re.sub(r'[^\w\s-]', '', title)
            filename = f'{safe_title}.{file_ext}'

            async with httpx.AsyncClient() as client:
                async with client.stream("GET", stream_url) as response: #enter the stream context.
                    if response.status_code != 200:
                        raise Exception(f'HTTP Error when downloading video: {response.status_code}')

                    byte_data = b""
                    async for chunk in response.aiter_bytes():
                        byte_data += chunk

            file_data = io.BytesIO(byte_data)
            file = discord.File(fp=file_data, filename=filename)

            await interaction.followup.send(title, file=file)

            logger.info(f'Downloaded "{filename}" from `{url}` and sent to user @{interaction.user}')
    except Exception as e:
        await interaction.followup.send(f'Error: {e}', silent=True)
        logger.error('Error occurred when downloading command tree', exc_info=e)

@bot.tree.command(name='stop', description='Stop any audio playing')
async def stop(interaction: discord.Interaction):
    logger.info(f'User @{interaction.user} requested to stop any audio')
    if interaction.guild.voice_client.is_playing():
        interaction.guild.voice_client.stop()
        await interaction.response.send_message('Alright, I\'ll shut up!')
        logger.info(f'Audio stopped for user @{interaction.user} successfully')
    else:
        await interaction.response.send_message('No audio is playing')
        logger.info(f'No audio was playing for user @{interaction.user}')

@bot.tree.command(name='play-url', description='Play audio from URL')
async def play_url(interaction: discord.Interaction, url: str):
    logger.info(f'User @{interaction.user} requested to play audio from `{url}`')

    await interaction.response.defer()
    
    await play_audio_with_ytdlp(interaction, url)

@bot.tree.command(name='play-ytsearch', description='Play audio from YouTube search')
async def play_ytsearch(interaction: discord.Interaction, keywords: str):
    logger.info(f'User @{interaction.user} requested to play audio from YouTube search "{keywords}"')
    
    await interaction.response.defer()
    
    url = f'ytsearch:{keywords}'
    await play_audio_with_ytdlp(interaction, url)

async def get_voice_channel(interaction: discord.Interaction):
    if not interaction.guild.voice_client:
        if not interaction.user.voice:
            logger.info(f'User @{interaction.user} is not in a voice channel')
            await interaction.response.send_message('You are not in a voice channel!')
            return None
        channel = interaction.user.voice.channel
        await channel.connect()
        logger.info(f'Joined to voice channel "{channel.name}" at guild "{channel.guild.name}" for user @{interaction.user}')
    else:
        channel = interaction.user.voice.channel
    return channel

async def play_audio_with_ytdlp(interaction: discord.Interaction, url: str):
    channel = await get_voice_channel(interaction)
    if not channel:
        return
    filename = get_temp_audio_filename()

    ydl_opts = {
        'format': 'bestaudio/best',  # Select best audio format
        'outtmpl': filename,  # Output filename template
        'extract_audio': True,  # Extract audio
        'audio_format': 'mp3',  # Convert to mp3 (or other desired format)
        'audio_quality': 0, #best quality
        'noplaylist': True, #prevent downloading entire playlists if URL is a playlist
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url)
            title = info_dict.get('title', 'video')
            
            source = discord.FFmpegPCMAudio(filename)
            interaction.guild.voice_client.play(source, after=lambda e: logger.error('An error occurred when playing audio at voice client', exc_info=e) if e else None)
            await interaction.followup.send(f'Playing audio "{title}"')

            logger.info(f'Played audio from `{url}` to voice channel "{channel.name}" at guild "{channel.guild.name}" for user @{interaction.user}')
    except Exception as e:
        await interaction.followup.send(f'Error: {e}', silent=True)
        logger.error('An error occurred when playing audio', exc_info=e)

def get_temp_audio_filename():
    if not os.path.exists("temp"):
        os.makedirs("temp")

    filename = f'temp/audio.mp3'
    if os.path.exists(filename):
        os.remove(filename)

    return filename

bot.run(TOKEN)
