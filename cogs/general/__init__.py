from discord.ext import commands

from .help import HelpCog
from .ping import ping
from .vct import VCTracker

async def setup(bot: commands.Bot):
    await bot.add_cog(HelpCog(bot))
    await bot.add_cog(ping(bot))
    await bot.add_cog(VCTracker(bot))