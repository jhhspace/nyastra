import discord
from discord.ext import commands
from discord.ui import View, Button

def chunked_fields(fields, size=6):
    for i in range(0, len(fields), size):
        yield fields[i:i + size]

class HelpView(View):
    def __init__(self, author: discord.User):
        super().__init__(timeout=60)
        self.author = author
        self.page = 0
        self.embeds = []
        self.paginated_mode = False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.author.id:
            await interaction.response.send_message("だめ! This is not your menu!", ephemeral=True)
            return False
        return True

    async def update_paginator_visibility(self):
        self.previous_page.disabled = not self.paginated_mode
        self.next_page.disabled = not self.paginated_mode

    @discord.ui.button(label="◀", style=discord.ButtonStyle.secondary, row=0)
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if self.paginated_mode:
            self.page = (self.page - 1) % len(self.embeds)
            await interaction.response.edit_message(embed=self.embeds[self.page], view=self)

    @discord.ui.button(label="▶", style=discord.ButtonStyle.secondary, row=0)
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if self.paginated_mode:
            self.page = (self.page + 1) % len(self.embeds)
            await interaction.response.edit_message(embed=self.embeds[self.page], view=self)


    @discord.ui.button(label="General", style=discord.ButtonStyle.primary, row=1)
    async def general_button(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🌸 General Commands",
            description="Nyaa~ here are the general commands!",
            color=discord.Color.pink()
        )
        embed.add_field(name=".help", value="Get a list of all commands.", inline=False)
        embed.add_field(name=".ping", value="Check the bot's latency.", inline=False)
        embed.add_field(name=".suggest <suggestion>", value="Setup suggestion channel in your server!", inline=False)

        self.paginated_mode = False
        await self.update_paginator_visibility()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Fun", style=discord.ButtonStyle.primary, row=1)
    async def fun_button(self, interaction: discord.Interaction, button: Button):
        all_fields = [
            (".pat", "Pat someone"), 
            (".hug", "Hug someone"), 
            (".kiss", "Kiss someone"),
            (".slap", "Slap someone"), 
            (".poke", "Poke someone"), 
            (".bite", "Bite someone"),
            (".smug", "Smug at someone"), 
            (".dance", "Dance dance dance like MMD"), 
            (".cry", "Cry out loud"),
            (".blush", "Blush at someone"),
            (".wink", "Wink at someone"),
            (".wave", "Wave at someone"),
            (".smile", "Smile at someone"),
            (".angry", "Get angry at someone"),
            (".happy", "Be happy"),
            (".sad", "Be sad"),
            (".confused", "Be confused at someone"),
            (".pout", "Pout at someone"),
            (".sigh", "Sigh at someone"),
            (".facepalm", "Facepalm at someone"),
            (".shrug", "Shrug at someone"),
            (".yawn", "n-nya~ yawn out loud"),
            (".sneeze", "Sneeze out loud!"),
            (".sleep", "Go to sleep!"),
            (".shout", "Shout at someone"),
            (".laugh", "Laugh at someone"),
            (".8b", "Ask Nyastra a question!")
        ]

        self.embeds = []
        for i, chunk in enumerate(chunked_fields(all_fields, size=6), start=1):
            embed = discord.Embed(
                title=f"🎉 Fun Commands (Page {i})",
                description="Nyaa~ have fun with these!",
                color=discord.Color.pink()
            )
            for name, value in chunk:
                embed.add_field(name=name, value=value, inline=False)
            embed.set_footer(text=f"Page {i} of {len(list(chunked_fields(all_fields, size=6)))}")
            self.embeds.append(embed)

        self.page = 0
        self.paginated_mode = True
        await self.update_paginator_visibility()
        await interaction.response.edit_message(embed=self.embeds[0], view=self)

    @discord.ui.button(label="Moderation", style=discord.ButtonStyle.primary, row=1)
    async def moderation_button(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🛡️ Moderation Commands",
            description="Commands to help you keep your server safe!",
            color=discord.Color.red()
        )
        embed.add_field(name=".setlogchannel [#channel]", value="Set a channel for moderation logs.", inline=False)
        embed.add_field(name=".ban <user>", value="Ban a user from the server.", inline=False)
        embed.add_field(name=".unban <user>", value="Unban a user from the server.", inline=False)
        embed.add_field(name=".kick <user>", value="Kick a user from the server.", inline=False)
        embed.add_field(name=".mute <user>", value="Mute a user.", inline=False)
        embed.add_field(name=".unmute <user>", value="Unmute a user.", inline=False)
        embed.add_field(name=".warn <user>", value="Warn a user.", inline=False)
        embed.add_field(name=".unwarn <Warning ID>", value="Unwarn a user.", inline=False)
        embed.add_field(name=".warnings <user>", value="Check warnings of a user.", inline=False)

        self.paginated_mode = False
        await self.update_paginator_visibility()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="AI", style=discord.ButtonStyle.primary, row=1)
    async def moderation_button(self, interaction: discord.Interaction, button: Button):
        embed = discord.Embed(
            title="🛡️ AI Commands",
            description="Commands to help you keep your server safe!",
            color=discord.Color.red()
        )
        embed.add_field(name=".recap [15-30]", value="Summarise your whole chat! Up to 30 messages", inline=False)
        embed.add_field(name=".rv", value="View the most recent summarized recap generated in the specific channel", inline=False)
        embed.add_field(name=".rt", value="Toggle whether recap is allowed to be used in your server", inline=False)


        self.paginated_mode = False
        await self.update_paginator_visibility()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="❌ Close", style=discord.ButtonStyle.danger, row=1)
    async def close_button(self, interaction: discord.Interaction, button: Button):
        await interaction.message.delete()
        self.stop()


class HelpCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='help')
    async def help_command(self, ctx):
        embed = discord.Embed(
            title="Nyaa~ Help Menu",
            description="Use the buttons below to explore categories! 🐾",
            color=discord.Color.pink()
        )
        embed.add_field(name="Welcome!", value="Click the buttons below to see available commands!", inline=False)
        embed.set_footer(text="This menu will timeout in 60 seconds when no activity is detected")

        view = HelpView(ctx.author)
        await view.update_paginator_visibility()
        await ctx.send(embed=embed, view=view)