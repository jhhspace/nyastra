from discord.ext import commands
import requests
import discord

class wave(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='wave')
    async def wave(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=wave"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} is waving at {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is waving away"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
