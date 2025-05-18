from discord.ext import commands

from .recap import Recap

async def setup(bot: commands.Bot):
    await bot.add_cog(Recap(bot))
    
    
    print("Loaded AI Cog")