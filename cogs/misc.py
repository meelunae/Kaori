from config import cfg
import discord
from discord.ext import commands
from utils import restart_bot

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        help_embed = discord.Embed(color=0x874efe)
        help_embed.add_field(name=f"{cfg.configured_prefix}play [YouTube/SoundCloud URL]", value="If the bot is not currently playing anything, plays a song from the provided URL. \nOtherwise, adds the song from the provided URL to the queue.",inline=False) 
        help_embed.add_field(name=f"{cfg.configured_prefix}skip", value="Skips currently playing song.",inline=False)
        help_embed.add_field(name=f"{cfg.configured_prefix}pause", value="Pauses currently playing song.",inline=False)
        help_embed.add_field(name=f"{cfg.configured_prefix}resume", value="Resumes music playback from paused state.",inline=False)
        help_embed.add_field(name=f"{cfg.configured_prefix}stop", value="Stops currently playing song and disconnects bot from the voice channel.",inline=False)
        help_embed.add_field(name=f"{cfg.configured_prefix}queue", value="Shows the songs that are currently in queue.",inline=False)
        help_embed.add_field(name=f"{cfg.configured_prefix}remove [Number]", value="Deletes from the queue the song that is in position *number*",inline=False)
        await ctx.send(embed=help_embed)

    @commands.command()
    async def restart(self, ctx):
        if ctx.author.id == cfg.owner_id:
            restart_embed = discord.Embed(color=0x874efe)
            restart_embed.add_field(name="Restarting", value="Restart requested by Ema. Be back soon! :)")
            await ctx.send(embed=restart_embed)
            restart_bot()