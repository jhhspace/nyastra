import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
load_dotenv()


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')

@bot.event
async def setup_hook():
    await bot.load_extension('cogs.general')
    await bot.load_extension('cogs.fun')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        await message.channel.send(f'Nya! What can I do for you, {message.author.mention}? Run `.help` to see my commands!')

    await bot.process_commands(message)


bot.run(os.getenv('DISCORD_BOT_TOKEN'))