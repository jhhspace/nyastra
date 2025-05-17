from discord.ext import commands
import requests
import discord

class bite(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='bite')
    async def bite(self, ctx, member: discord.Member = None):
        url = "https://api.otakugifs.xyz/gif?reaction=bite"
        response = requests.get(url)
        data = response.json()
        gif_url = data['url']

        if member:
            title = f"{ctx.author.display_name} is biting at {member.display_name}!"
        else:
            title = f"{ctx.author.display_name} is biting the air for some reason"

        embed = discord.Embed(
            title=title,
            color=discord.Color.random()
        )
        embed.set_image(url=gif_url)

        await ctx.send(embed=embed)
