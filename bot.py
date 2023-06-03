import asyncio
import datetime
import discord
from discord.ext import commands, tasks
import os
import sys
import youtube_dl

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn',
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
}

#discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.3.1/lib/libopus.0.dylib')
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.duration = str(datetime.timedelta(seconds=data.get('duration'))).split(":", 1)[1]
        self.title = data.get('title')
        self.url = data.get('url')
        print(self.duration)

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


def restart_bot(): 
  os.execv(sys.executable, ['python3'] + sys.argv)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queued_songs = [] 

    @commands.command()
    async def join(self, ctx, *, channel: discord.VoiceChannel):
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

    @commands.command()
    async def play(self, ctx, *, url):
        play_embed = discord.Embed(color=0x874efe)
        # We check if the task is already running to avoid starting it multiple times
        if not (check_vc_members.is_running()):
            check_vc_members.start(ctx.guild.id, ctx.author.voice.channel.id)
        
        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        if ctx.voice_client.is_playing():
            self.queued_songs.append({'title': player.title, 'url': url})
            play_embed.add_field(name="Added to Queue", value=f"\n{player.title}", inline=False)
            play_embed.add_field(name=f"", value=f"In position #{len(self.queued_songs)}", inline=True)
        else:
            play_embed=discord.Embed(color=0x874efe)
            play_embed.add_field(name="Now Playing", value=f"\n{player.title}", inline=False)
            play_embed.add_field(name="Length", value=f"\n{player.duration}", inline=False)
            play_embed.add_field(name=f"", value=f"Requested by {ctx.author.mention}", inline=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next_song(ctx), bot.loop).result())
        await ctx.send(embed=play_embed)

    async def play_next_song(self, ctx):
        if len(self.queued_songs) > 0:
            song = self.queued_songs.pop(0)
            player = await YTDLSource.from_url(song['url'], loop=self.bot.loop, stream=True)
            embed=discord.Embed(color=0x874efe)
            embed.add_field(name="Now Playing", value=f"\n{player.title}", inline=False)
            embed.add_field(name="Length", value=f"\n{player.duration}", inline=False)
            embed.add_field(name=f"", value=f"Requested by {ctx.author.mention}", inline=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next_song(ctx), bot.loop).result())
            await ctx.send(embed=embed)

    @commands.command()
    async def queue(self, ctx):
        queue_embed=discord.Embed(color=0x874efe)
        if len(self.queued_songs) == 0:
            queue_embed.add_field(name="Queue", value=f"The queue is currently empty.", inline=False)
        else:
            embed_value = ""
            for i, song in enumerate(self.queued_songs, start=1):
                embed_value += f'\n{i}. {song["title"]}\n'
            queue_embed.add_field(name="Queue", value=f"{embed_value}", inline=False)
        await ctx.send(embed=queue_embed)

    @commands.command()
    async def remove(self, ctx, *, number):
        remove_embed = discord.Embed(color=0x874efe)
        try:
            index = int(number) - 1
            if len(self.queued_songs) < index:
                remove_embed.add_field(name="Error", value=f"The element you are trying to remove is not in the queue.", inline=False)
            else:
                song = self.queued_songs.pop(index)
                remove_embed.add_field(name="Removed from Queue", value=f'{song["title"]} was removed from the queue.', inline=False)
        
        except ValueError:
                remove_embed.add_field(name="Error", value=f"The value you provided is not a number.", inline=False)
                raise commands.CommandError("Tried to run remove from queue while passing an invalid input.")
        finally:
                await ctx.send(embed=remove_embed)

    @commands.command()
    async def skip(self, ctx):
        skip_embed = discord.Embed(color=0x874efe)
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await self.play_next_song(ctx)
            skip_embed.add_field(name="Skipped", value=f"", inline=False)
            skip_embed.add_field(name="", value=f"Skip requested by {ctx.author.mention}")
        else:
            skip_embed.add_field(name="Error", value=f"I am not currently playing any music so I can't skip.", inline=False)
        await ctx.send(embed=skip_embed)

    @commands.command()
    async def flush(self, ctx):
        flush_embed = discord.Embed(color=0x874efe)
        songs_number = len(self.queued_songs)
        self.queued_songs = []
        flush_embed.add_field(name="Queue flushed", value=f"I have removed {songs_number} items from the queue.")
        await ctx.send(embed=flush_embed)

    @commands.command()
    async def restart(self, ctx):
        if ctx.author.id == 174602493890789377:
            restart_embed = discord.Embed(color=0x874efe)
            restart_embed.add_field(name="Restarting", value="Restart requested by Ema. Be back soon! :)")
            await ctx.send(embed=restart_embed)
            restart_bot()

    @play.before_invoke
    async def ensure_voice(self, ctx):
        connect_embed = discord.Embed(color=0xff0000)
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                connect_embed.add_field(name="Error", value=f"You are not connected to a voice channel.", inline=False)
                await ctx.send(embed=connect_embed)
                raise commands.CommandError("Author not connected to a voice channel.")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"),
                   description='Relatively simple music bot example', intents=intents)


@tasks.loop(minutes=5)
async def check_vc_members(guild_id, voice_channel_id):
    guild = bot.get_guild(guild_id)  
    voice_channel = guild.get_channel(voice_channel_id)
    if voice_channel:
        voice_members = voice_channel.members
        if len(voice_members) == 1:  # Exclude the bot itself
            for voice_client in bot.voice_clients:
                await voice_client.disconnect()
    else:
        print("The voice channel is not found.")       

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')
    print('------')

    await bot.add_cog(Music(bot))

bot.run('token')