import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from cogs.general.suggestion import PersistentApproveRejectView
load_dotenv()


intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name} - {bot.user.id}')
    print('------')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you"))

@bot.event
async def setup_hook():
    await bot.load_extension('cogs.general')
    await bot.load_extension('cogs.fun')
    await bot.load_extension('cogs.moderation')
    bot.add_view(PersistentApproveRejectView())

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if bot.user in message.mentions:
        await message.channel.send(f'Nya! What can I do for you, {message.author.mention}? Run `.help` to see my commands!')

    await bot.process_commands(message)


bot.run(os.getenv('DISCORD_BOT_TOKEN'))
# bot.run(os.getenv('TEST_TOKEN'))