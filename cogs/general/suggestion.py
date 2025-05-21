import discord
from discord.ext import commands
from discord.ui import View, Select
import sqlite3
from typing import Optional

DB_FILE = "./Databases/Suggestion.db"

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS suggest_settings (
            guild_id TEXT PRIMARY KEY,
            channel_id INTEGER,
            count INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def has_manage_guild(obj: discord.Interaction | commands.Context) -> bool:
    if isinstance(obj, discord.Interaction):
        return obj.user.guild_permissions.manage_guild
    elif isinstance(obj, commands.Context):
        return obj.author.guild_permissions.manage_guild
    return False

class PersistentApproveRejectView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Approve", style=discord.ButtonStyle.success, custom_id="persistent_approve_button")
    async def approve_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._update_embed(interaction, "Approved", "✅")

    @discord.ui.button(label="Reject", style=discord.ButtonStyle.danger, custom_id="persistent_reject_button")
    async def reject_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._update_embed(interaction, "Rejected", "❌")

    @discord.ui.button(label="Maybe", style=discord.ButtonStyle.secondary, custom_id="persistent_maybe_button")
    async def maybe_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self._update_embed(interaction, "Maybe", "❓")

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not has_manage_guild(interaction):
            await interaction.response.send_message(
                "You don't have permission to perform this action.", ephemeral=True
            )
            return False
        return True

    async def _update_embed(self, interaction, status_text, emoji):
        await interaction.response.defer()

        embed = interaction.message.embeds[0]
        footer_text = embed.footer.text or ""
        footer_text = footer_text.split('|')[0].strip()

        embed.set_footer(
            text=f"{footer_text} | Marked as {emoji} {status_text} by {interaction.user.display_name}",
            icon_url=interaction.user.display_avatar.url
        )

        for item in self.children:
            item.disabled = True

        await interaction.message.edit(embed=embed, view=self)



class Suggest(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def get_suggest_channel_id(self, guild_id: int) -> Optional[int]:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT channel_id FROM suggest_settings WHERE guild_id = ?', (str(guild_id),))
        row = cursor.fetchone()
        conn.close()
        return row["channel_id"] if row and row["channel_id"] is not None else None

    def set_suggest_channel_id(self, guild_id: int, channel_id: int):
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT guild_id FROM suggest_settings WHERE guild_id = ?', (str(guild_id),))
        exists = cursor.fetchone()
        if exists:
            cursor.execute(
                'UPDATE suggest_settings SET channel_id = ? WHERE guild_id = ?',
                (channel_id, str(guild_id))
            )
        else:
            cursor.execute(
                'INSERT INTO suggest_settings (guild_id, channel_id, count) VALUES (?, ?, ?)',
                (str(guild_id), channel_id, 0)
            )
        conn.commit()
        conn.close()

    def increment_suggestion_count(self, guild_id: int) -> int:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT count FROM suggest_settings WHERE guild_id = ?', (str(guild_id),))
        row = cursor.fetchone()
        if row:
            new_count = row["count"] + 1
            cursor.execute('UPDATE suggest_settings SET count = ? WHERE guild_id = ?', (new_count, str(guild_id)))
        else:
            new_count = 1
            cursor.execute(
                'INSERT INTO suggest_settings (guild_id, channel_id, count) VALUES (?, ?, ?)',
                (str(guild_id), None, new_count)
            )
        conn.commit()
        conn.close()
        return new_count

    class SetChannelView(View):
        def __init__(self, cog, user_id, guild):
            super().__init__(timeout=60)
            self.cog = cog
            self.user_id = user_id
            self.guild = guild

            channels = [ch for ch in guild.channels if isinstance(ch, discord.TextChannel)]
            options = [discord.SelectOption(label=ch.name, value=str(ch.id)) for ch in channels[:25]]

            self.select = Select(placeholder="Modify Suggestion channel", options=options)
            self.select.callback = self.select_callback
            self.add_item(self.select)

        async def interaction_check(self, interaction: discord.Interaction) -> bool:
            if interaction.user.id != self.user_id:
                await interaction.response.send_message("This dropdown is not for you.", ephemeral=True)
                return False
            return True

        async def select_callback(self, interaction: discord.Interaction):
            channel_id = int(self.select.values[0])
            self.cog.set_suggest_channel_id(self.guild.id, channel_id)
            await interaction.response.edit_message(
                content=f"Suggestion channel set to <#{channel_id}> ✅",
                view=None
            )

        async def on_timeout(self):
            for item in self.children:
                item.disabled = True

    @commands.command(name="suggest")
    async def suggest(self, ctx, *, suggestion: str = None):
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server.")
            return

        if suggestion is None:
            embed = discord.Embed(
                title="✨ Missing Suggestion ✨",
                description="Please provide a suggestion after the command.\n\n"
                            "Example: `.suggest Add more emojis!`",
                color=0xFF69B4
            )
            view = self.SetChannelView(self, ctx.author.id, ctx.guild) if has_manage_guild(ctx) else None
            await ctx.send(embed=embed, view=view)
            return

        guild_id = ctx.guild.id
        channel_id = self.get_suggest_channel_id(guild_id)

        if channel_id is None:
            await ctx.send("Suggestion channel is not set. Please ask a server manager to set it using `.suggest`.")
            return

        channel = ctx.guild.get_channel(channel_id)
        if channel is None:
            await ctx.send("The suggestion channel set is invalid or I don't have access to it.\nPlease ask a server manager to set it using `.suggest`")
            return

        count = self.increment_suggestion_count(guild_id)

        embed = discord.Embed(
            title="🌸 New Suggestion 🌸",
            description=f"✨ **{suggestion}** ✨",
            color=0xFF69B4,
            timestamp=ctx.message.created_at
        )
        avatar_url = ctx.author.display_avatar.url
        embed.set_author(name=ctx.author.display_name, icon_url=avatar_url)
        embed.set_footer(text=f"Suggestion #{count} | Suggested by {ctx.author}", icon_url=avatar_url)

        msg = await channel.send(embed=embed)

        await msg.add_reaction("👍")
        await msg.add_reaction("👎")

        if has_manage_guild(ctx):
            view = PersistentApproveRejectView()
            await msg.edit(view=view)
        else:
            await ctx.send("Your suggestion has been sent! Thank you for your input.")