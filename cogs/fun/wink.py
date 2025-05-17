from discord.ext import commands
import requests
import discord

class wink(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='wink')
    async def wink(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=wink"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} is winking at {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is winking"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
