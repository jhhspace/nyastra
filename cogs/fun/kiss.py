from discord.ext import commands
import requests
import discord

class kiss(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='kiss')
    async def kiss(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=kiss"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} is kissing {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is kissing the air"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
