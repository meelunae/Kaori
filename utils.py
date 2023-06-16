import discord
import os
import platform
import sys

def build_embed(bot, **kwargs) -> discord.Embed:  

  # TODO: add support for embed fields straight from kwargs. Rough way of how to do it is commented below, but I want something different. 
  title = kwargs.pop('title', 'Title')
  description = kwargs.pop('description', 'Description')
  color = kwargs.pop('color', 0x874efe)  # To be changed to configurable for funsies!
  img = kwargs.pop('img', None)
  author_icon = kwargs.pop('author_icon', bot.user.avatar.url)
  author_name = kwargs.pop('author_name', bot.user.name)
  footer_text = kwargs.pop('footer_text', None)
  footer_icon = kwargs.pop('footer_icon', None)
  embed = discord.Embed(color=color, description=description, title=title)
  embed.set_author(name=author_name, icon_url=author_icon)

  if img:
    embed.set_image(url=img)

  if footer_text or footer_icon:
    embed.set_footer(text=footer_text,icon_url=footer_icon)

  # for key, value in kwargs.items():
      # embed.add_field(name=key, value=value, inline=True)
  return embed

def import_opus():
  if platform.system() == "Darwin":
    try:
      # We try loading libopus from the default install directory for Apple Silicon macOS Homebrew
      discord.opus.load_opus('/opt/homebrew/Cellar/opus/1.3.1/lib/libopus.0.dylib')
    except FileNotFoundError as e:
      print(f"FileNotFoundError while trying to import libopus: \n"f"{e}")

def restart_bot(): 
  os.execv(sys.executable, ['python3'] + sys.argv)