from discord.ext import commands
import requests
import discord

class pat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='pat')
    async def pat(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=pat"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} is patting {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is patting themselves!"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
