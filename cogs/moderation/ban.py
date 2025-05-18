import discord
from discord.ext import commands
import sqlite3
import aiosqlite

DB_FILE = "./Databases/Ban.db"

class BanUnban(commands.Cog):
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

    def set_log_channel_id(self, guild_id, channel_id):
        self.cursor.execute('REPLACE INTO log_channels (guild_id, channel_id) VALUES (?, ?)', (guild_id, channel_id))
        self.db.commit()

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
            await self.send_error(ctx, "The configured log channel was deleted, nya~!\nPlease set a new one with `.setlogchannel [#channel]`")
            return
        await channel.send(embed=embed)

    @commands.command(name="setlogchannel", aliases=["setlog", "slc"])
    @commands.has_permissions(administrator=True)
    async def set_log_channel(self, ctx, channel: discord.TextChannel):
        self.set_log_channel_id(ctx.guild.id, channel.id)
        embed = discord.Embed(
            title="🐾 Log Channel Set!",
            description=f"Logs will now be sent to {channel.mention}, nya~",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.User, *, reason=None):
        if user == ctx.author:
            await self.send_error(ctx, "You can't ban yourself, nya~! (≧▽≦)")
            return
        
        try:
            bans = []
            async for ban_entry in ctx.guild.bans():
                bans.append(ban_entry)
            if any(ban_entry.user.id == user.id for ban_entry in bans):
                await self.send_error(ctx, "That user is already banned, nya~!")
                return
        except discord.Forbidden:
            pass
        
        try:
            await ctx.guild.ban(user, reason=reason)
            embed = discord.Embed(
                title="😾 Nya! A User Has Been Banned!",
                description="Justice has been served, nya~ 💢",
                color=discord.Color.magenta()
            )
            embed.add_field(name="User", value=f"{user} (ID: {user.id})", inline=False)
            embed.add_field(name="Reason", value=reason or "No reason provided~", inline=False)
            embed.add_field(name="Banned by", value=f"{ctx.author} (ID: {ctx.author.id})", inline=False)
            embed.set_footer(text="Stay pawsitive and follow the rules~ ✨🐾")

            await self.log_action(ctx, ctx.guild, embed)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await self.send_error(ctx, "User not found, nya...")
        except discord.Forbidden:
            await self.send_error(ctx, "I don't have permission to ban this user... (；´д｀)ゞ\n\nMake sure the user isn't an Admin\nOR\nMake sure I have the `Ban Members` permission, nya~!")
        except discord.HTTPException as e:
            await self.send_error(ctx, f"Couldn't ban the user, meow. Error: {e}")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason=None):
        try:
            user = await self.bot.fetch_user(user_id)
            await ctx.guild.unban(user, reason=reason)
            embed = discord.Embed(
                title="ฅ^•ﻌ•^ฅ A User Has Been Forgiven!",
                description="The neko council lifts the ban~ 🐾",
                color=discord.Color.purple()
            )
            embed.add_field(name="User", value=f"{user} (ID: {user.id})", inline=False)
            embed.add_field(name="Reason", value=reason or "Forgiven without reason~", inline=False)
            embed.add_field(name="Unbanned by", value=f"{ctx.author} (ID: {ctx.author.id})", inline=False)
            embed.set_footer(text="Be a good human, okay~? 🌸")

            await self.log_action(ctx, ctx.guild, embed)
            await ctx.send(embed=embed)
        except discord.NotFound:
            await self.send_error(ctx, "User isn't banned..? nya?")
        except discord.Forbidden:
            await self.send_error(ctx, "I don't have permission to unban them... (｡•́︿•̀｡)\n\nMake sure I have the `Ban Members` permission, nya~!")
        except discord.HTTPException as e:
            await self.send_error(ctx, f"Something went wrong, nya~ Error: {e}")

    async def send_error(self, ctx, message):
        embed = discord.Embed(
            title="❌ Error. oh nyo~!",
            description=message,
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)

    @ban.error
    @unban.error
    async def user_command_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.send_error(ctx, "You don’t have permission to use this command! ❌")
        elif isinstance(error, commands.MissingRequiredArgument):
            await self.send_error(ctx, "You're missing a required argument!\nPlease provide a User or User ID. 🐾\n\nExample usage:\n.ban <@898569996949676052> bad boy!\n.ban 898569996949676052 bad boy!")
        elif isinstance(error, commands.BadArgument):
            await self.send_error(ctx, "That doesn't look like a valid user or ID... Check again, nya~ 💢")
        elif isinstance(error, commands.MemberNotFound):
            await self.send_error(ctx, "User not found! Please give me a valid user, please~ 🐾")
        else:
            print(f"Unexpected error: {error}")
            await self.send_error(ctx, "An unknown error occurred, nya~\n\nPlease try again later! ⚠️")

    @set_log_channel.error
    async def setlogchannel_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.send_error(ctx, "You don’t have permission to use this command! ❌")
        elif isinstance(error, commands.MissingRequiredArgument):
            await self.send_error(ctx, "You need to specify a text channel to set as the log channel!\nUsage: `.setlogchannel #channel`")
        elif isinstance(error, commands.BadArgument):
            await self.send_error(ctx, "Please mention a valid text channel, nya~ 🐾")
        else:
            print(f"Unexpected error in setlogchannel: {error}")
            await self.send_error(ctx, "An unknown error occurred in setlogchannel, nya~\n\nPlease try again later! ⚠️")
