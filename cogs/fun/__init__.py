import importlib
import pkgutil
from discord.ext import commands

async def setup(bot: commands.Bot):
    for _, name, _ in pkgutil.iter_modules(__path__):
        module = importlib.import_module(f".{name}", __name__)
        cog = getattr(module, name)(bot)
        await bot.add_cog(cog)
print("Loaded Fun Cog")