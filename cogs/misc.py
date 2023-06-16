from config import cfg
from discord.ext import commands
from utils import build_embed, restart_bot

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx):
        description = f"""
        **{cfg.configured_prefix}play [YouTube/SoundCloud URL]**
        If the bot is not currently playing anything, plays a song from the provided URL. \nOtherwise, adds the song from the provided URL to the queue.\n
        **{cfg.configured_prefix}skip**
        Skips currently playing song.\n
        **{cfg.configured_prefix}pause**
        Pauses currently playing song.\n
        **{cfg.configured_prefix}resume**
        Resumes music playback from paused state.\n
        **{cfg.configured_prefix}stop**
        Stops currently playing song and disconnects bot from the voice channel.\n
        **{cfg.configured_prefix}queue**
        Shows the songs that are currently in queue.\n
        **{cfg.configured_prefix}remove [Number]**
        Deletes from the queue the song that is in position `number`\n
        """
        help_embed = build_embed(self.bot, title="Commands usage", description=description)
        await ctx.send(embed=help_embed)

    @commands.command()
    async def restart(self, ctx):
        if ctx.author.id == cfg.owner_id:
            restart_embed = build_embed(self.bot, title="Restarting...", description="Restart requested by Ema. Be back soon! :)")
            await ctx.send(embed=restart_embed)
            restart_bot()