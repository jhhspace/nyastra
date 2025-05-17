import discord
from discord.ext import commands

class ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='ping')
    async def ping(self, ctx):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)
        embed = discord.Embed(title="Pong! Nyastra-Discord Server-Nyastra latency!", description=f"Latency: {latency}ms", color=0x00ff00)
        await ctx.send(embed=embed)