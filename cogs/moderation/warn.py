import discord
from discord.ext import commands, tasks
import sqlite3
import os
from datetime import datetime, timedelta
import uuid
import re

class Warn(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        os.makedirs('./Databases', exist_ok=True)
        self.db = sqlite3.connect('./Databases/Warn.db', check_same_thread=False)
        self.cursor = self.db.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS warnings (
            warn_id TEXT PRIMARY KEY NOT NULL,
            guild_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            moderator_id INTEGER NOT NULL,
            reason TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            duration INTEGER
        )''')
        self.db.commit()

        self.ban_db = sqlite3.connect('./Databases/Ban.db', check_same_thread=False)
        self.ban_cursor = self.ban_db.cursor()
        self.check_expired_warnings.start()

    def get_log_channel(self, guild_id):
        self.ban_cursor.execute('SELECT channel_id FROM log_channels WHERE guild_id = ?', (guild_id,))
        result = self.ban_cursor.fetchone()
        if result:
            return int(result[0])
        return None

    def format_embed(self, title, description, color=discord.Color.orange()):
        return discord.Embed(
            title=f"🌸 {title}", description=description, color=color
        ).set_footer(text="Nyastra Moderation")

    def parse_duration(self, duration_str):
        duration_str = duration_str.lower()
        pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
        match = re.fullmatch(pattern, duration_str)
        if not match:
            return None

        days, hours, minutes, seconds = match.groups(default='0')
        try:
            total_seconds = int(days) * 86400 + int(hours) * 3600 + int(minutes) * 60 + int(seconds)
            return total_seconds if total_seconds > 0 else None
        except ValueError:
            return None

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, args=None):
        if not args:
            reason = "No reason provided"
            duration = None
            duration_str = None
        else:
            parts = args.split()
            duration = None
            duration_str = None
            for i, part in enumerate(parts):
                if re.fullmatch(r'\d+[smhd]', part.lower()):
                    duration = self.parse_duration(part)
                    if duration is None:
                        return await ctx.send(embed=self.format_embed(
                            "Invalid Duration",
                            "Duration must be a valid time like `30s`, `15m`, `2h`, or `1d`, nya~",
                            discord.Color.red()
                        ))
                    duration_str = part
                    parts.pop(i)
                    break
            reason = " ".join(parts).strip() if parts else "No reason provided"

        warn_id = str(uuid.uuid4())[:8]
        now = datetime.utcnow()
        self.cursor.execute('INSERT INTO warnings VALUES (?, ?, ?, ?, ?, ?, ?)',
            (warn_id, ctx.guild.id, member.id, ctx.author.id, reason, now.isoformat(), duration))
        self.db.commit()

        embed = self.format_embed(
            "User Warned",
            f"**👤 User:** {member.mention} (`{member.id}`)\n"
            f"**🛡️ Moderator:** {ctx.author.mention}\n"
            f"**📄 Reason:** {reason}\n"
            f"**⏳ Duration:** {'∞' if duration is None else duration_str}\n"
            f"**🆔 Warning ID:** `{warn_id}`"
        )
        await ctx.send(embed=embed)

        log_channel_id = self.get_log_channel(ctx.guild.id)
        if log_channel_id:
            log_channel = ctx.guild.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def unwarn(self, ctx, warn_id: str):
        self.cursor.execute('SELECT * FROM warnings WHERE warn_id = ?', (warn_id,))
        row = self.cursor.fetchone()

        if not row:
            return await ctx.send(embed=self.format_embed("Not Found", f"No warning found with ID `{warn_id}`, nya~", discord.Color.red()))

        self.cursor.execute('DELETE FROM warnings WHERE warn_id = ?', (warn_id,))
        self.db.commit()

        user_id = row[2]
        reason = row[4]

        embed = self.format_embed(
            "Warning Removed",
            f"**🆔 Warning ID:** `{warn_id}`\n"
            f"**👤 User:** <@{user_id}> (`{user_id}`)\n"
            f"**📄 Reason:** {reason}\n"
            f"**🛡️ Unwarned by:** {ctx.author.mention}"
        )
        await ctx.send(embed=embed)

        log_channel_id = self.get_log_channel(ctx.guild.id)
        if log_channel_id:
            log_channel = ctx.guild.get_channel(log_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)

    @commands.command(aliases=["warnings"])
    async def warns(self, ctx, user: discord.User = None):
        user = user or ctx.author
        now = datetime.utcnow()

        self.cursor.execute('SELECT * FROM warnings WHERE guild_id = ? AND user_id = ?', (ctx.guild.id, user.id))
        all_warnings = self.cursor.fetchall()

        filtered = []
        for row in all_warnings:
            warn_time = datetime.fromisoformat(row[5])
            duration = row[6]
            expired = duration and (now > warn_time + timedelta(seconds=duration))
            if not expired:
                filtered.append(row)

        if not filtered:
            return await ctx.send(embed=self.format_embed("No Active Warnings", f"{user.mention} has no active warnings, nya~"))

        embed = self.format_embed("Warnings", f"Active warnings for {user.mention}:")
        for row in filtered[:10]:
            warn_id = row[0]
            mod_id = row[3]
            reason = row[4]
            timestamp = row[5]
            duration = row[6]
            embed.add_field(
                name=f"🆔 {warn_id} - ⚠️ Active",
                value=f"📄 **Reason:** {reason}\n🛡️ <@{mod_id}>\n🕒 <t:{int(datetime.fromisoformat(timestamp).timestamp())}:R>\n⏳ Duration: {'∞' if not duration else str(duration)+'s'}",
                inline=False
            )
        await ctx.send(embed=embed)



    @tasks.loop(minutes=5)
    async def check_expired_warnings(self):
        now = datetime.utcnow()
        self.cursor.execute('SELECT warn_id, timestamp, duration FROM warnings WHERE duration IS NOT NULL')
        rows = self.cursor.fetchall()
        for warn_id, timestamp_str, duration in rows:
            timestamp = datetime.fromisoformat(timestamp_str)
            if now > timestamp + timedelta(seconds=duration):
                pass

    @warn.error
    @unwarn.error
    @warns.error
    async def warn_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=self.format_embed("Missing Argument", "You're missing a required argument, nya~!"))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=self.format_embed("Permission Denied", "You don't have permission to use this command, nya~!"))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=self.format_embed("Invalid Argument", "That doesn't seem like a valid input, nya~"))
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(embed=self.format_embed("Internal Error", f"Something went wrong:\n```{error.original}```", discord.Color.red()))
        else:
            await ctx.send(embed=self.format_embed("Unknown Error", f"Unexpected error:\n```{error}```", discord.Color.red()))
