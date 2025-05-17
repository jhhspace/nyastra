import discord
import random
from discord.ext import commands

class ball8(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='8ball', aliases=['8b'])
    async def ball8(self, ctx):
        """Ask the magic 8 ball a question."""
        responses = [
            "Nyaa~! Yes~! 💕",
            "Mmm... nope! 🐾",
            "Maybeee~ nya? Who knows~",
            "Ask again later, I'm grooming my tail~ 🐱",
            "Definitely, nya! Believe it~! ✨",
            "Nuh-uh! Not happening, nya~ 🙀",
            "I wouldn’t bet your fishies on it, nya~",
            "For sure, nya! Like catnip to a kitty~ 🐾",
            "Don't count on it, nya... I'm not feeling it~ 😿",
            "Yes~ but only if you give me headpats first~! 🥰",
            "Ehh... nyot sure~ wanna cuddle and ask again~?",
            "Pawsitively~! I can feel it in my whiskers~! ✨",
            "Nyaah! That’s a secret~! You’ll have to find out~ 💫",
            "Mou~! I’m too sleepy to think... zzz~ 💤",
            "Hmph! Don’t rush me, dummy nya~! 💢",
            "You better bring snacks if you want an answer~! 🍣",
            "Nyahaha~! You already know the answer, silly~!",
            "Ufufu~ it’s written in the stars… nya~ 🌟",
            "Only if you say ‘nya’ ten times really fast~ 😽",
            "Heehee~ sure, but don’t blame me if it backfires nya~ 😼"
        ]
        question = ctx.message.content[7:]
        if not question:
            await ctx.send("Ask me a question!!")
            return
        response = random.choice(responses)
        await ctx.send(response)