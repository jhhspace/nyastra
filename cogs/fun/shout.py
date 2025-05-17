from discord.ext import commands
import requests
import discord

class shout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='shout')
    async def shout(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=shout"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} is shouting at {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is shouting for no reason at all"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
