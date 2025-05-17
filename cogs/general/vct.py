import discord
from discord.ext import commands
from discord.ui import View, Button
import sqlite3
from datetime import datetime, timedelta

DB_FILE = "vc_tracking.db"

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

class VCTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = dict_factory
        self.create_tables()

        self.active_sessions = {}
        self.wait_trackers = {}

    def create_tables(self):
        c = self.conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                vc_channel TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                duration_seconds REAL NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS response_times (
                user_id TEXT PRIMARY KEY,
                average REAL NOT NULL,
                count INTEGER NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS wait_logs (
                user_id TEXT PRIMARY KEY,
                average REAL NOT NULL,
                count INTEGER NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS switch_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                from_vc TEXT NOT NULL,
                to_vc TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS vc_channels (
                user_id TEXT NOT NULL,
                vc_channel TEXT NOT NULL,
                total_seconds REAL NOT NULL,
                sessions INTEGER NOT NULL,
                PRIMARY KEY (user_id, vc_channel)
            )
        """)
        self.conn.commit()

    def update_average(self, table, user_id, new_value):
        c = self.conn.cursor()
        c.execute(f"SELECT average, count FROM {table} WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        if row:
            old_avg = row["average"]
            count = row["count"]
            new_count = count + 1
            new_avg = (old_avg * count + new_value) / new_count
            c.execute(f"UPDATE {table} SET average = ?, count = ? WHERE user_id = ?", (new_avg, new_count, user_id))
        else:
            c.execute(f"INSERT INTO {table} (user_id, average, count) VALUES (?, ?, ?)", (user_id, new_value, 1))
        self.conn.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = str(member.id)

        if before.channel is None and after.channel is not None:
            now = datetime.utcnow()
            self.active_sessions[user_id] = {
                "join": now,
                "waiting": True,
                "wait_start": now,
                "current_vc": after.channel.id
            }

            vc = after.channel
            if len(vc.members) == 1:
                self.wait_trackers[vc.id] = {
                    "start": now,
                    "user": user_id
                }
            elif len(vc.members) == 2 and vc.id in self.wait_trackers:
                wait_data = self.wait_trackers.pop(vc.id)
                elapsed = (now - wait_data["start"]).total_seconds()
                self.update_average("wait_logs", wait_data["user"], elapsed)

        elif before.channel is not None and after.channel is None:
            await self.handle_vc_leave(member, before.channel)

        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            await self.handle_vc_leave(member, before.channel)

            now = datetime.utcnow()
            self.active_sessions[user_id] = {
                "join": now,
                "waiting": True,
                "wait_start": now,
                "current_vc": after.channel.id
            }

            c = self.conn.cursor()
            c.execute("""
                INSERT INTO switch_logs (user_id, from_vc, to_vc, timestamp) VALUES (?, ?, ?, ?)
            """, (user_id, before.channel.name, after.channel.name, now.isoformat()))
            self.conn.commit()

        elif before.channel == after.channel:
            now = datetime.utcnow()
            for uid, session in list(self.active_sessions.items()):
                if uid == user_id:
                    continue
                vc = after.channel
                if any(m.id == int(uid) for m in vc.members):
                    if session["waiting"]:
                        response_time = (now - session["wait_start"]).total_seconds()
                        self.update_average("response_times", uid, response_time)
                        self.active_sessions[uid]["waiting"] = False

    async def handle_vc_leave(self, member, vc):
        user_id = str(member.id)
        if user_id not in self.active_sessions:
            return

        start_time = self.active_sessions[user_id]["join"]
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        vc_channel_name = vc.name if vc else "Unknown"

        c = self.conn.cursor()
        c.execute("""
            INSERT INTO sessions (user_id, vc_channel, start_time, end_time, duration_seconds)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, vc_channel_name, start_time.isoformat(), end_time.isoformat(), duration))

        c.execute("""
            SELECT total_seconds, sessions FROM vc_channels WHERE user_id = ? AND vc_channel = ?
        """, (user_id, vc_channel_name))
        row = c.fetchone()
        if row:
            total_seconds = row["total_seconds"] + duration
            sessions_count = row["sessions"] + 1
            c.execute("""
                UPDATE vc_channels SET total_seconds = ?, sessions = ? WHERE user_id = ? AND vc_channel = ?
            """, (total_seconds, sessions_count, user_id, vc_channel_name))
        else:
            c.execute("""
                INSERT INTO vc_channels (user_id, vc_channel, total_seconds, sessions) VALUES (?, ?, ?, ?)
            """, (user_id, vc_channel_name, duration, 1))

        self.conn.commit()
        del self.active_sessions[user_id]

        if vc and len(vc.members) == 0 and vc.id in self.wait_trackers:
            del self.wait_trackers[vc.id]

    @commands.command(name="vcstats", aliases=["vct", "vcs"])
    async def vc_stats(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        user_id = str(member.id)
        c = self.conn.cursor()

        c.execute("SELECT SUM(duration_seconds) AS total FROM sessions WHERE user_id = ?", (user_id,))
        row = c.fetchone()
        total_seconds = row["total"] or 0
        total = str(timedelta(seconds=int(total_seconds)))

        c.execute("SELECT average, count FROM wait_logs WHERE user_id = ?", (user_id,))
        wait_row = c.fetchone()
        avg_wait = f"{wait_row['average']:.2f} seconds" if wait_row and wait_row["count"] > 0 else "No wait time data"

        c.execute("SELECT COUNT(*) AS session_count FROM sessions WHERE user_id = ?", (user_id,))
        sessions_count = c.fetchone()["session_count"]

        embed = discord.Embed(
            title=f"VC Stats for {member.display_name}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Total VC Time", value=total, inline=False)
        embed.add_field(name="Avg Time Until Someone Joined", value=avg_wait, inline=False)
        embed.add_field(name="Sessions Tracked", value=str(sessions_count), inline=False)

        c.execute("SELECT vc_channel, total_seconds, sessions FROM vc_channels WHERE user_id = ?", (user_id,))
        rows = c.fetchall()
        if rows:
            vc_lines = []
            for r in rows:
                avg = r["total_seconds"] / r["sessions"]
                vc_lines.append(f"**{r['vc_channel']}**: {timedelta(seconds=int(avg))} avg over {r['sessions']} sessions")
            embed.add_field(name="VC Time per Channel", value="\n".join(vc_lines), inline=False)

        c.execute("SELECT from_vc, to_vc, timestamp FROM switch_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 5", (user_id,))
        switch_logs = c.fetchall()
        if switch_logs:
            switch_lines = [f"{s['timestamp']}: {s['from_vc']} → {s['to_vc']}" for s in reversed(switch_logs)]
            embed.add_field(name="Recent VC Switches", value="\n".join(switch_lines), inline=False)

        view = VCStatsView(self, ctx.author.id, member)
        await ctx.send(embed=embed, view=view)


class VCStatsView(View):
    def __init__(self, cog: VCTracker, requester_id: int, target_member: discord.Member):
        super().__init__()
        self.cog = cog
        self.requester_id = requester_id
        self.target_member = target_member

        if requester_id == target_member.id:
            self.add_item(VCResetButton(cog, target_member.id))

        self.add_item(VCLeaderboardButton(cog))


class VCResetButton(Button):
    def __init__(self, cog: VCTracker, user_id: int):
        super().__init__(label="🔁 Reset Stats", style=discord.ButtonStyle.danger)
        self.cog = cog
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("You can only reset **your own** VC stats.", ephemeral=True)

        c = self.cog.conn.cursor()
        user_id_str = str(self.user_id)
        c.execute("DELETE FROM sessions WHERE user_id = ?", (user_id_str,))
        c.execute("DELETE FROM response_times WHERE user_id = ?", (user_id_str,))
        c.execute("DELETE FROM wait_logs WHERE user_id = ?", (user_id_str,))
        c.execute("DELETE FROM switch_logs WHERE user_id = ?", (user_id_str,))
        c.execute("DELETE FROM vc_channels WHERE user_id = ?", (user_id_str,))
        self.cog.conn.commit()

        await interaction.response.send_message("✅ Your VC stats have been reset.", ephemeral=True)
        await interaction.message.delete()


class VCLeaderboardButton(Button):
    def __init__(self, cog: VCTracker):
        super().__init__(label="📊 Leaderboard", style=discord.ButtonStyle.primary)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        c = self.cog.conn.cursor()
        c.execute("""
            SELECT user_id, SUM(duration_seconds) AS total FROM sessions
            GROUP BY user_id ORDER BY total DESC LIMIT 10
        """)
        rows = c.fetchall()

        leaderboard = []
        for idx, r in enumerate(rows, 1):
            user = interaction.guild.get_member(int(r["user_id"]))
            name = user.display_name if user else f"<@{r['user_id']}>"
            total = str(timedelta(seconds=int(r["total"])))
            leaderboard.append(f"#{idx}: **{name}** — {total}")

        embed = discord.Embed(title="VC Time Leaderboard", color=discord.Color.gold())
        embed.description = "\n".join(leaderboard) if leaderboard else "No data yet."
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(VCTracker(bot))
