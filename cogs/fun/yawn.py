from discord.ext import commands
import requests
import discord

class yawn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='yawn')
    async def yawn(self, ctx):

        url = "https://api.otakugifs.xyz/gif?reaction=yawn"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']


        embed = discord.Embed(
            title=f"{ctx.author.display_name} yawned out loud!",
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
