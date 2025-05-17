import discord
from discord.ext import commands
from discord.ui import View, Button
import json
import os
from datetime import datetime, timedelta


class VCTracker(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.data_file = "vc_tracking.json"
        self.tracking_data = self.load_data()
        self.active_sessions = {}
        self.wait_trackers = {}

    def load_data(self):
        if not os.path.exists(self.data_file):
            return {}
        with open(self.data_file, "r") as f:
            return json.load(f)

    def save_data(self):
        with open(self.data_file, "w") as f:
            json.dump(self.tracking_data, f, indent=4)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        user_id = str(member.id)

        # Join VC
        if before.channel is None and after.channel is not None:
            self.active_sessions[user_id] = {
                "join": datetime.utcnow(),
                "waiting": True,
                "wait_start": datetime.utcnow()
            }

            vc = after.channel
            if len(vc.members) == 1:
                self.wait_trackers[vc.id] = {
                    "start": datetime.utcnow(),
                    "user": user_id
                }
            elif len(vc.members) == 2 and vc.id in self.wait_trackers:
                wait_data = self.wait_trackers.pop(vc.id)
                elapsed = (datetime.utcnow() - wait_data["start"]).total_seconds()
                tracking = self.tracking_data.setdefault(wait_data["user"], {
                    "total_time_seconds": 0,
                    "sessions": [],
                    "response_times": [],
                    "vc_channels": {},
                    "wait_logs": []
                })
                tracking["wait_logs"].append(elapsed)
                self.save_data()

        # Leave VC
        elif before.channel is not None and after.channel is None:
            await self.handle_vc_leave(member, before.channel)

        # Switch VC
        elif before.channel is not None and after.channel is not None and before.channel.id != after.channel.id:
            await self.handle_vc_leave(member, before.channel)
            self.active_sessions[user_id] = {
                "join": datetime.utcnow(),
                "waiting": True,
                "wait_start": datetime.utcnow()
            }

        # Same VC (check if someone joined)
        elif before.channel == after.channel:
            for uid, session in list(self.active_sessions.items()):
                if uid == user_id:
                    continue
                vc = after.channel
                if any(m.id == int(uid) for m in vc.members):
                    if session["waiting"]:
                        response_time = (datetime.utcnow() - session["wait_start"]).total_seconds()
                        self.tracking_data.setdefault(uid, {
                            "total_time_seconds": 0,
                            "sessions": [],
                            "response_times": [],
                            "vc_channels": {},
                            "wait_logs": []
                        })
                        self.tracking_data[uid]["response_times"].append(response_time)
                        self.active_sessions[uid]["waiting"] = False
                        self.save_data()

    async def handle_vc_leave(self, member, vc):
        user_id = str(member.id)

        if user_id in self.active_sessions:
            start_time = self.active_sessions[user_id]["join"]
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            vc_channel_name = vc.name if vc else "Unknown"

            if user_id not in self.tracking_data:
                self.tracking_data[user_id] = {
                    "total_time_seconds": 0,
                    "sessions": [],
                    "response_times": [],
                    "vc_channels": {},
                    "wait_logs": []
                }

            self.tracking_data[user_id]["total_time_seconds"] += duration
            self.tracking_data[user_id]["sessions"].append({
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_seconds": duration,
                "vc_channel": vc_channel_name
            })

            vc_data = self.tracking_data[user_id]["vc_channels"].setdefault(vc_channel_name, {
                "total_seconds": 0,
                "sessions": 0
            })
            vc_data["total_seconds"] += duration
            vc_data["sessions"] += 1

            del self.active_sessions[user_id]
            self.save_data()

        if vc and len(vc.members) == 0 and vc.id in self.wait_trackers:
            del self.wait_trackers[vc.id]

    @commands.command(name="vcstats", aliases=["vct", "vcs"])
    async def vc_stats(self, ctx, member: discord.Member = None):
        if member is None:
            member = ctx.author

        user_id = str(member.id)
        data = self.tracking_data.get(user_id)

        if not data:
            return await ctx.send(f"No VC data found for {member.display_name}.")

        total = str(timedelta(seconds=int(data["total_time_seconds"])))
        avg_response = (
            f"{(sum(data['response_times']) / len(data['response_times'])):.2f} seconds"
            if data["response_times"] else "No data"
        )
        avg_wait = (
            f"{(sum(data['wait_logs']) / len(data['wait_logs'])):.2f} seconds"
            if data["wait_logs"] else "No wait time data"
        )

        embed = discord.Embed(
            title=f"VC Stats for {member.display_name}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Total VC Time", value=total, inline=False)
        embed.add_field(name="Avg Time Until Someone Joined", value=avg_wait, inline=False)
        embed.add_field(name="Avg Time Someone Joins You (Interaction)", value=avg_response, inline=False)
        embed.add_field(name="Sessions Tracked", value=str(len(data["sessions"])), inline=False)

        vc_channels = data.get("vc_channels", {})
        if vc_channels:
            vc_lines = []
            for ch_name, ch_data in vc_channels.items():
                avg = ch_data["total_seconds"] / ch_data["sessions"]
                vc_lines.append(f"**{ch_name}**: {timedelta(seconds=int(avg))} avg over {ch_data['sessions']} sessions")
            embed.add_field(name="VC Time per Channel", value="\n".join(vc_lines), inline=False)

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

        user_id_str = str(self.user_id)
        if user_id_str in self.cog.tracking_data:
            del self.cog.tracking_data[user_id_str]
            self.cog.save_data()
            await interaction.response.send_message("✅ Your VC stats have been reset.", ephemeral=True)
        else:
            await interaction.response.send_message("No stats found to reset.", ephemeral=True)


class VCLeaderboardButton(Button):
    def __init__(self, cog: VCTracker):
        super().__init__(label="🏆 Show Leaderboard", style=discord.ButtonStyle.primary)
        self.cog = cog

    async def callback(self, interaction: discord.Interaction):
        tracking_data = self.cog.tracking_data
        if not tracking_data:
            return await interaction.response.send_message("No leaderboard data available.", ephemeral=True)

        sorted_data = sorted(tracking_data.items(), key=lambda x: x[1]["total_time_seconds"], reverse=True)[:10]

        embed = discord.Embed(title="VC Leaderboard", color=discord.Color.gold())
        for i, (user_id, data) in enumerate(sorted_data, start=1):
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member else f"User {user_id}"
            time_str = str(timedelta(seconds=int(data["total_time_seconds"])))
            embed.add_field(name=f"{i}. {name}", value=f"Time: {time_str}", inline=False)

        await interaction.response.send_message(embed=embed, ephemeral=True)
