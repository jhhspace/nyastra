import discord
from discord.ext import commands
import sqlite3

DB_FILE = "./Databases/Ban.db"

class Kick(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.cursor = self.db.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS log_channels (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER
            )
        ''')
        self.db.commit()

    def get_log_channel_id(self, guild_id):
        self.cursor.execute('SELECT channel_id FROM log_channels WHERE guild_id = ?', (guild_id,))
        result = self.cursor.fetchone()
        return result[0] if result else None

    async def log_action(self, ctx, guild, embed):
        channel_id = self.get_log_channel_id(guild.id)
        if not channel_id:
            embed = discord.Embed(
                title="⚠️ Log Channel Not Set!",
                description="Please use `.setlogchannel [#channel]` to configure one, nya~",
                color=discord.Color.orange()
            )
            await ctx.send(embed=embed)
            return
        channel = guild.get_channel(channel_id)
        if not channel:
            await self.send_error(ctx, "The configured log channel was deleted, nya~! Please set a new one.")
            return
        await channel.send(embed=embed)

    async def send_error(self, ctx, message):
        embed = discord.Embed(
            title="❌ Error. oh nyo~!",
            description=message,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason=None):
        if user == ctx.author:
            await self.send_error(ctx, "You can't kick yourself, nya~! (≧▽≦)")
            return
        
        if not ctx.guild.me.guild_permissions.kick_members:
            await self.send_error(ctx, "I don't have permission to kick members, nya~!")
            return

        if user == ctx.guild.owner:
            await self.send_error(ctx, "I can't kick the server owner, nya~!")
            return
        
        if user.top_role >= ctx.guild.me.top_role:
            await self.send_error(ctx, "I can't kick someone with an equal or higher role than mine, nya~!")
            return
        
        if user == ctx.guild.me:
            await self.send_error(ctx, "I won't kick myself, nya~!")
            return
        
        try:
            await user.kick(reason=reason)
            embed = discord.Embed(
                title="😾 User Kicked!",
                description="The neko council shows the door! 🚪🐾",
                color=discord.Color.orange()
            )
            embed.add_field(name="User", value=f"{user} (ID: {user.id})", inline=False)
            embed.add_field(name="Reason", value=reason or "No reason provided~", inline=False)
            embed.add_field(name="Kicked by", value=f"{ctx.author} (ID: {ctx.author.id})", inline=False)
            embed.set_footer(text="Please behave, or the paws will come for you again! 🐾")

            await self.log_action(ctx, ctx.guild, embed)
            await ctx.send(embed=embed)
        except discord.Forbidden:
            await self.send_error(ctx, "I don't have permission to kick that user... (；´д｀)ゞ")
        except discord.HTTPException as e:
            await self.send_error(ctx, f"Couldn't kick the user, meow. Error: {e}")

    @kick.error
    async def kick_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.send_error(ctx, "You don’t have permission to use this command! ❌")
        elif isinstance(error, commands.MissingRequiredArgument):
            await self.send_error(ctx, "You're missing a required argument!\nPlease provide a User to kick. 🐾\n\nExample usage:\n.kick @User spamming")
        elif isinstance(error, commands.BadArgument):
            await self.send_error(ctx, "That doesn't look like a valid user... Check again, nya~ 💢")
        else:
            print(f"Unexpected error in kick command: {error}")
            await self.send_error(ctx, "An unknown error occurred, nya~\n\nPlease try again later! ⚠️")

def setup(bot):
    bot.add_cog(Kick(bot))
