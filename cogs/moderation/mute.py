import re
import discord
from discord.ext import commands
import sqlite3
from datetime import timedelta

DB_FILE = "./Databases/Ban.db"

def parse_duration(duration_str):
    match = re.fullmatch(r"(\d+)([smhd])", duration_str.lower())
    if not match:
        return None

    amount, unit = match.groups()
    amount = int(amount)

    if unit == "s":
        return timedelta(seconds=amount)
    elif unit == "m":
        return timedelta(minutes=amount)
    elif unit == "h":
        return timedelta(hours=amount)
    elif unit == "d":
        return timedelta(days=amount)
    return None

class Mute(commands.Cog):
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

    @commands.command(name="mute")
    @commands.has_permissions(moderate_members=True)
    async def mute(self, ctx, member: discord.Member, *, reason_and_duration=None):
        if member == ctx.author:
            await self.send_error(ctx, "You can't mute yourself, nya~! (≧▽≦)")
            return

        if member == ctx.guild.owner:
            await self.send_error(ctx, "I can't mute the server owner, nya~!")
            return

        if member == ctx.guild.me:
            await self.send_error(ctx, "I won't mute myself, nya~!")
            return

        if member.top_role >= ctx.guild.me.top_role:
            await self.send_error(ctx, "I can't mute someone with an equal or higher role than mine, nya~!")
            return

        duration = timedelta(minutes=5)
        reason = None

        if reason_and_duration:
            parts = reason_and_duration.split()

            dur = None
            dur_index = None
            for i, part in enumerate(parts):
                potential_duration = parse_duration(part)
                if potential_duration:
                    dur = potential_duration
                    dur_index = i
                    break
            
            if dur:
                duration = dur
                parts.pop(dur_index)
                reason = " ".join(parts) if parts else None
            else:
                reason = reason_and_duration

        if duration > timedelta(days=28):
            await self.send_error(ctx, "Maximum timeout duration is 28 days, nya~!")
            return

        try:
            await member.timeout(duration, reason=reason)

            dur_str = ""
            total_seconds = int(duration.total_seconds())
            days, remainder = divmod(total_seconds, 86400)
            hours, remainder = divmod(remainder, 3600)
            minutes, seconds = divmod(remainder, 60)
            if days > 0:
                dur_str += f"{days}d "
            if hours > 0:
                dur_str += f"{hours}h "
            if minutes > 0:
                dur_str += f"{minutes}m "
            if seconds > 0:
                dur_str += f"{seconds}s"
            dur_str = dur_str.strip()

            embed = discord.Embed(
                title="🔇 User Timed Out!",
                description=f"{member.mention} has been timed out for {dur_str}, nya~ 🐾",
                color=discord.Color.dark_gray()
            )
            embed.add_field(name="User", value=f"{member} (ID: {member.id})", inline=False)
            embed.add_field(name="Reason", value=reason or "No reason provided~", inline=False)
            embed.add_field(name="Muted by", value=f"{ctx.author} (ID: {ctx.author.id})", inline=False)
            embed.set_footer(text="Remember to be kind, nya~ ✨")

            await self.log_action(ctx, ctx.guild, embed)
            await ctx.send(embed=embed)

        except discord.Forbidden:
            await self.send_error(ctx, "I don't have permission to timeout this member... (；´д｀)ゞ")
        except discord.HTTPException as e:
            await self.send_error(ctx, f"Failed to timeout the member, meow. Error: {e}")


    @commands.command(name="unmute")
    @commands.has_permissions(moderate_members=True)
    async def unmute(self, ctx, member: discord.Member, *, reason=None):
        try:
            if member.timeout:
                await member.timeout(None, reason=reason)

                embed = discord.Embed(
                    title="🔊 User Untimed Out!",
                    description=f"{member.mention} is no longer timed out, nya~ 🐾",
                    color=discord.Color.green()
                )
                embed.add_field(name="User", value=f"{member} (ID: {member.id})", inline=False)
                embed.add_field(name="Reason", value=reason or "No reason provided~", inline=False)
                embed.add_field(name="Unmuted by", value=f"{ctx.author} (ID: {ctx.author.id})", inline=False)
                embed.set_footer(text="Be nice, okay? 🌸")

                await self.log_action(ctx, ctx.guild, embed)
                await ctx.send(embed=embed)
            else:
                await self.send_error(ctx, "That user is not currently timed out, nya~!")
        except discord.Forbidden:
            await self.send_error(ctx, "I don't have permission to remove timeout from this member... (｡•́︿•̀｡)")
        except discord.HTTPException as e:
            await self.send_error(ctx, f"Failed to remove timeout, nya~. Error: {e}")

    @mute.error
    @unmute.error
    async def mute_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.send_error(ctx, "You don’t have permission to use this command! ❌")
        elif isinstance(error, commands.MissingRequiredArgument):
            await self.send_error(ctx, "You're missing a required argument!\nPlease specify a user and optionally duration in minutes. 🐾\n\nExample usage:\n.mute @User 10m spamming\n.unmute @User")
        elif isinstance(error, commands.BadArgument):
            await self.send_error(ctx, "That doesn't look like a valid user or duration... Check again, nya~ 💢")
        else:
            print(f"Unexpected error in mute/unmute command: {error}")
            await self.send_error(ctx, "An unknown error occurred, nya~\n\nPlease try again later! ⚠️")