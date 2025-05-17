from discord.ext import commands
import requests
import discord

class sleep(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='sleep')
    async def sleep(self, ctx):

        url = "https://api.otakugifs.xyz/gif?reaction=sleep"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']


        embed = discord.Embed(
            title=f"{ctx.author.display_name} went to sleep, sleep tight!",
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
