from discord.ext import commands

from .ban import BanUnban
from .kick import Kick
from .mute import Mute
from .warn import Warn

async def setup(bot: commands.Bot):
    await bot.add_cog(BanUnban(bot))
    await bot.add_cog(Kick(bot))
    await bot.add_cog(Mute(bot))
    await bot.add_cog(Warn(bot))
    
    print("Loaded Moderation Cog")