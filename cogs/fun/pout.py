from discord.ext import commands
import requests
import discord

class pout(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='pout')
    async def pout(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=pout"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} is pouting at {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is pouting!"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
