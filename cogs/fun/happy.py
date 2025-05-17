from discord.ext import commands
import requests
import discord

class happy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='happy')
    async def happy(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=happy"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} is happy about {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is happy"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
