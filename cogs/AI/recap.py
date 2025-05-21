import discord
from discord.ext import commands
from discord.ui import View, Button
import os
import sqlite3
import traceback
from datetime import datetime

from openai import OpenAI

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
DB_PATH = "./Databases/AI_recap.db"

class Recap(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.recap_enabled = True
        self._recap_cooldowns = {}
        self.init_db()
        self.load_cooldowns()

    def init_db(self):
        os.makedirs("./Databases", exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recaps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER,
                    channel_id INTEGER,
                    author TEXT,
                    timestamp TEXT,
                    summary TEXT
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recap_cooldowns (
                    server_id INTEGER PRIMARY KEY,
                    last_used REAL
                )
            """)
            conn.commit()

    def load_cooldowns(self):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT server_id, last_used FROM recap_cooldowns")
            rows = cursor.fetchall()
            for server_id, last_used in rows:
                self._recap_cooldowns[server_id] = last_used

    def save_cooldown(self, guild_id: int, timestamp: float):
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recap_cooldowns (server_id, last_used)
                VALUES (?, ?)
                ON CONFLICT(server_id) DO UPDATE SET last_used=excluded.last_used
            """, (guild_id, timestamp))
            conn.commit()

    async def send_error(self, ctx, message):
        embed = discord.Embed(
            title="⚠️ An error occurred!",
            description=message,
            color=discord.Color.red()
        )
        embed.set_footer(text="Powered by Catnips!")
        await ctx.send(embed=embed)

    @commands.command(name='recap')
    @commands.has_permissions()
    async def recap(self, ctx, limit: int = None):
        if limit is None:
            await self.send_error(ctx, f"Please enter a number between **15 and 30**, nya~! 🐾\n\nNote that bot messages are not included in summary")
            return

        if not self.recap_enabled:
            await self.send_error(ctx, "Nyaa~ The recap feature is currently disabled! Ask a mod to turn it back on~ 💤")
            return

        if limit > 30 or limit < 15:
            await self.send_error(ctx, "Please enter a number between **15 and 30**! 🐾\n\nNote that bot messages are not included in summary")
            return

        now = datetime.utcnow().timestamp()
        last_used = self._recap_cooldowns.get(ctx.guild.id, 0)
        cooldown_seconds = 600
        if now - last_used < cooldown_seconds:
            remaining = int(cooldown_seconds - (now - last_used))
            await self.send_error(ctx, f"Nyaa~ The recap command is on cooldown for this server. Please wait {remaining} more seconds before trying again! 🐾")
            return

        async with ctx.typing():
            await ctx.send("Nyaa~ Summarizing the chat... Please wait a moment! 🐾")
            
        ignored_bot_messages = {
            "Nyaa~ Summarizing the chat... Please wait a moment! 🐾"
        }
        try:
            messages = [
                msg async for msg in ctx.channel.history(limit=limit)
                if (
                    msg.id != ctx.message.id
                    and msg.content not in ignored_bot_messages
                    and not (msg.author.bot and (msg.content.startswith('.recap') or msg.content.startswith('!recap')))
                )
            ]

            if len(messages) < 15:
                await self.send_error(ctx, f"You need a minimum of **15 messages** in the channel to run a recap, nya~! 🐾\n\nNote that bot messages are not included in summary")
                # for m in messages:
                    # print(f"{m.id} | {m.author} | {m.content[:30]}...")
                return

            convo = ""
            for msg in reversed(messages):
                if msg.author.bot:
                    continue
                content = msg.clean_content.replace("\n", " ")
                convo += f"{msg.author.display_name}: {content}\n"

            if not convo.strip():
                await self.send_error(ctx, "There's nothing to summarize, nya~ So quiet... 💤")
                return

            prompt = (
                "You're a cute, dramatic anime catgirl storyteller summarizing a chaotic Discord chat. "
                "Be expressive, adorable, and make it feel engaging like a livestream recap.\n\n"
                f"Chat Log:\n{convo}\n\nSummary:"
            )

            response = openai_client.chat.completions.create(
                model="gpt-4.1-nano",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=400,
                temperature=0.9,
            )
            self._recap_cooldowns[ctx.guild.id] = now
            summary = response.choices[0].message.content.strip()

            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO recaps (server_id, channel_id, author, timestamp, summary)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    ctx.guild.id,
                    ctx.channel.id,
                    str(ctx.author),
                    datetime.utcnow().isoformat(),
                    summary
                ))
                conn.commit()

            embed = discord.Embed(
                title="📝 Nyaa~ Chat Recap Time!",
                description=summary,
                color=discord.Color.pink()
            )
            embed.set_footer(text=f"Requested by {ctx.author.display_name} • Powered by Catnips")
            await ctx.send(embed=embed)
            self.save_cooldown(ctx.guild.id, now)

        except discord.DiscordException:
            await self.send_error(ctx, "Oops, something went wrong with Discord! Please try again later, nya~ 🐾")
        except Exception as openai_err:
            print(f"OpenAI or unexpected error: {openai_err}")
            traceback.print_exc()
            await self.send_error(ctx, "An error occurred while communicating with the AI, nya~ Please try again later! ⚠️")

    @commands.command(name="recaptoggle", aliases=["rt"])
    @commands.has_permissions(manage_messages=True)
    async def toggle_recap(self, ctx):
        self.recap_enabled = not self.recap_enabled
        state = "enabled" if self.recap_enabled else "disabled"
        color = discord.Color.green() if self.recap_enabled else discord.Color.red()

        embed = discord.Embed(
            title="🔧 Recap Toggled!",
            description=f"Recap feature is now **{state}**, nya~!",
            color=color
        )
        embed.set_footer(text="Powered by Catnips!")
        await ctx.send(embed=embed)

    @commands.command(name="recapview", aliases=["rv"])
    async def view_recaps(self, ctx):
        """View the most recent past chat summary for this channel"""
        try:
            with sqlite3.connect(DB_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT author, timestamp, summary
                    FROM recaps
                    WHERE server_id = ? AND channel_id = ?
                    ORDER BY id DESC
                    LIMIT 1
                """, (ctx.guild.id, ctx.channel.id))
                row = cursor.fetchone()

            if not row:
                await self.send_error(ctx, "No past recaps found for this channel, nya~! 🐾")
                return

            author, timestamp, summary = row
            embed = discord.Embed(
                title=f"🗂️ Most Recent Past Recap",
                description=summary,
                color=discord.Color.blurple()
            )
            timestamp_dt = datetime.fromisoformat(timestamp)
            embed.set_footer(text=f"Requested by {author} • {timestamp_dt.strftime('%Y-%m-%d %H:%M UTC+0')} | Powered by Catnips")
            await ctx.send(embed=embed)

        except Exception as e:
            await self.send_error(ctx, f"An error occurred: {e}")


        except discord.DiscordException:
            await self.send_error(ctx, "Oops, something went wrong with Discord! Please try again later, nya~ 🐾")
        except Exception as err:
            print(f"Error fetching recaps: {err}")
            traceback.print_exc()
            await self.send_error(ctx, "Oh nyo! An error occurred while fetching past recaps! Please try again later! ⚠️")

    @recap.error
    async def recap_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.send_error(ctx, "You don’t have permission to use this command! ❌")
        elif isinstance(error, commands.MissingRequiredArgument):
            await self.send_error(ctx, "You're missing a required argument!\nTry `.recap 30`, nya~ 🐾")
        elif isinstance(error, commands.BadArgument):
            await self.send_error(ctx, "Nyaa~ That doesn’t look like a valid number! Try something like `.recap 30` 🐾")
        else:
            traceback.print_exc()
            await self.send_error(ctx, "Oh nyo! An unknown error occurred! Please try again later! ⚠️")

    @toggle_recap.error
    async def toggle_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            await self.send_error(ctx, "Only mods can toggle the recap feature ❌")
        else:
            traceback.print_exc()
            await self.send_error(ctx, "Oh nyo! An unknown error occurred! Please try again later! ⚠️")