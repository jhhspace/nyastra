from discord.ext import commands
import requests
import discord

class slap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='slap')
    async def slap(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=slap"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} slaps {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is slapping the air"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
