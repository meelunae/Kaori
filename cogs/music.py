import asyncio
from config import cfg
import datetime
import discord
from discord.ext import commands, tasks
from utils import build_embed, import_opus
import yt_dlp

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

import_opus()
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.duration = str(datetime.timedelta(seconds=data.get('duration'))).split(":", 1)[1]
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        
        if 'entries' in data:
            data = data['entries'][0]
        
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
    
class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queues = {}
    
    def same_voice_channel():
        async def predicate(ctx):
            if not ctx.author.voice:
                connect_embed=build_embed(ctx.cog.bot, title="Error", description="You are not connected to a voice channel.", color=0xff0000)
                await ctx.send(embed=connect_embed)
                return False
            elif not ctx.voice_client:
                connect_embed=build_embed(ctx.cog.bot, title="Error", description="I am not connected to a voice channel.", color=0xff0000)
                await ctx.send(embed=connect_embed)
                return False
            elif ctx.author.voice.channel != ctx.voice_client.channel:
                connect_embed=build_embed(ctx.cog.bot, title="Error", description="You are not in the same voice channel as me.", color=0xff0000)
                await ctx.send(embed=connect_embed)
                return False
            else:
                return True
        return commands.check(predicate)
    
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                connect_embed=build_embed(self.bot, title="Error", description="You are not connected to a voice channel.", color=0xff0000)
                await ctx.send(embed=connect_embed)
                raise commands.CommandError("Author not connected to a voice channel.")  

    @commands.command()
    @commands.guild_only()
    @commands.before_invoke(ensure_voice)
    async def play(self, ctx, *, url):
        # Hardcoded check because decorators won't work well together 
        if ctx.author.voice.channel != ctx.voice_client.channel:
            connect_embed=build_embed(ctx.cog.bot, title="Error", description="You are not in the same voice channel as me.", color=0xff0000)
            await ctx.send(embed=connect_embed)
            return
        # We initalize the queue for current guild if it is not initialized yet
        if ctx.guild.id not in self.queues:
            self.queues[ctx.guild.id] = []
        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        if ctx.voice_client.is_playing():
            self.queues[ctx.guild.id].append({'title': player.title, 'url': url})
            play_embed = build_embed(self.bot, title="Added to Queue", description=f"\n{player.title}")
            play_embed.add_field(name=f"", value=f"In position #{len(self.queues[ctx.guild.id])}", inline=True)
        else:
            play_embed = build_embed(self.bot, title="Now Playing", description=f"\n{player.title}")
            play_embed.add_field(name="Length", value=f"\n{player.duration}", inline=False)
            play_embed.add_field(name=f"", value=f"Requested by {ctx.author.mention}", inline=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next_song(ctx), self.bot.loop).result())
        await ctx.send(embed=play_embed)

    async def play_next_song(self, ctx):
        if len(self.queues[ctx.guild.id]) > 0:
            song = self.queues[ctx.guild.id].pop(0)
            player = await YTDLSource.from_url(song['url'], loop=self.bot.loop, stream=True)
            embed = build_embed(self.bot, title="Now Playing", description=f"\n{player.title}")
            embed.add_field(name="Length", value=f"\n{player.duration}", inline=False)
            embed.add_field(name=f"", value=f"Requested by {ctx.author.mention}", inline=True)
            ctx.voice_client.play(player, after=lambda e: asyncio.run_coroutine_threadsafe(self.play_next_song(ctx), self.bot.loop).result())
            await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    async def queue(self, ctx):
        embed_description = ""
        if len(self.queues[ctx.guild.id]) == 0:
            embed_description = "The queue is currently empty."
        else:
            for i, song in enumerate(self.queues[ctx.guild.id], start=1):
                embed_description += f'{i}. {song["title"]}\n'
        queue_embed = build_embed(self.bot, title="Queue", description=embed_description)
        await ctx.send(embed=queue_embed)

    @commands.command()
    @commands.guild_only()
    @same_voice_channel()
    async def remove(self, ctx, *, number):
        remove_embed = discord.Embed(color=0x874efe)
        try:
            idx = int(number)
            if len(self.queues[ctx.guild.id]) < idx or idx < 1:
                remove_embed = build_embed(self.bot, title="Error", description="There is no queue element for the selected index.", color=0xff0000)
            else:
                song = self.queues[ctx.guild.id].pop(idx-1)
                remove_embed = build_embed(self.bot, title="Removed from Queue", description=f"{song['title']} was removed from the queue.")
        
        except ValueError:
                remove_embed = build_embed(self.bot, title="Error", description="The value you provided is not a number.", color=0xff0000)
                raise commands.CommandError("Tried to run remove from queue while passing an invalid input.")
        finally:
                await ctx.send(embed=remove_embed)

    @commands.command()
    @commands.guild_only()
    @same_voice_channel()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            pause_embed = build_embed(self.bot, title="Playback paused", description="Type !resume to resume playback.")
        elif ctx.voice_client and ctx.voice_client.is_paused():
            pause_embed = build_embed(self.bot, title="Error", description="I am not currently playing any music so I can't pause playback.", color=0xff0000)
        else:
            pause_embed = build_embed(self.bot, title="Error", description="I am not in a voice channel right now.", color=0xff0000)
        await ctx.send(embed=pause_embed)

    @commands.command()
    @commands.guild_only()
    @same_voice_channel()
    async def resume(self, ctx):
        if ctx.voice_client and  ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            resume_embed = build_embed(self.bot, title="Playback resumed", description="")
        elif ctx.voice_client and ctx.voice_client.is_playing():
            resume_embed = build_embed(self.bot, title="Error", description="Music is already playing!", color=0xff0000)
        else:
            resume_embed = build_embed(self.bot, title="Error", description="I am not in a voice channel right now.", color=0xff0000)
        await ctx.send(embed=resume_embed)

    @commands.command()
    @commands.guild_only()
    @same_voice_channel()
    async def skip(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await self.play_next_song(ctx)
            skip_embed = build_embed(self.bot, title="Skipped", description=f"Skip requested by {ctx.author.mention}")
        else:
            skip_embed = build_embed(self.bot, title="Error", description="I am not currently playing any music so I can't skip.", color=0xff0000)
        await ctx.send(embed=skip_embed)

    @commands.command()
    @commands.guild_only()
    @same_voice_channel()
    async def stop(self, ctx):
        if ctx.voice_client:
            self.queues[ctx.guild.id] = [] # Emptying our queue for next instance
            await ctx.voice_client.disconnect()
            stop_embed = build_embed(self.bot, title="Stopped", description="Music has been stopped and the queue has been emptied.")
        else: 
            stop_embed = build_embed(self.bot, title="Error", description="I am not in a voice channel right now.", color=0xff0000)
        await ctx.send(embed=stop_embed)


    @commands.command()
    @commands.guild_only()
    @same_voice_channel()
    async def flush(self, ctx):
        songs_number = len(self.queues[ctx.guild.id])
        if songs_number > 0:
            self.queues[ctx.guild.id] = []
            flush_embed = build_embed(self.bot, title="Queue flushed", description=f"I have removed {songs_number} items from the queue.")
        else: 
            flush_embed = build_embed(self.bot, title="Error", description=f"Queue is empty so I cannot remove anything from it.", color=0xff0000)
        await ctx.send(embed=flush_embed)
    
    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # We ignore voice state changes that do not originate from the bot
        if not member.id == self.bot.user.id:
            return
        # We ignore voice state changes generated by disconnect() events too
        elif before.channel is not None:
            return
        # Check if music is playing every 3 minutes with an asyncio loop
        else:
            voice = after.channel.guild.voice_client
            while True:
                await asyncio.sleep(180)
                # If not playing, disconnect
                if voice.is_playing() == False:
                    print ("The bot isn't playing, disconnecting.")
                    await voice.disconnect()
                    break

