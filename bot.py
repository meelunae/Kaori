from config import cfg
from cogs.music import Music
import discord
from discord.ext import commands

class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if cfg:
            print("Configuration loaded successfully!")

intents = discord.Intents.default()
intents.message_content = True
intents.voice_states = True
bot = commands.Bot(command_prefix=commands.when_mentioned_or(cfg.configured_prefix), 
                   description='Music streaming bot based on YTDL for various platforms', intents=intents)

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} - {bot.user.id})")
    print("------")
    print(f"Bot owner ID is {cfg.owner_id}")
    print(f"Configured command prefix is {cfg.configured_prefix}")
    await bot.add_cog(Music(bot))

def main():
    bot.run(cfg.kaori_token, reconnect=True)

if __name__ == "__main__":
    main()