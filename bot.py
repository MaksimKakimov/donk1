import discord
from discord.ext import commands
from discord import app_commands
import datetime
import os
import re

# ---------------------- Variables ----------------------
TOKEN = os.environ.get("DISCORD_TOKEN")

# Channels
ANNOUNCE_CHANNEL_ID = int(os.environ.get("ANNOUNCE_CHANNEL_ID"))
FRIENDLY_CHANNEL_ID = int(os.environ.get("FRIENDLY_CHANNEL_ID"))
FRIENDLY_RESULT_CHANNEL_ID = int(os.environ.get("FRIENDLY_RESULT_CHANNEL_ID"))
LEAGUE_RESULT_CHANNEL_ID = int(os.environ.get("LEAGUE_RESULT_CHANNEL_ID"))
TRIAL_RESULT_CHANNEL_ID = int(os.environ.get("TRIAL_RESULT_CHANNEL_ID"))

# Roles
HOST_ROLE_ID = int(os.environ.get("HOST_ROLE_ID"))
B_TEAM_ROLE_ID = int(os.environ.get("B_TEAM_ROLE_ID"))
A_TEAM_ROLE_ID = int(os.environ.get("A_TEAM_ROLE_ID"))
MAIN_SUB_ROLE_ID = int(os.environ.get("MAIN_SUB_ROLE_ID"))
MAIN_TEAM_ROLE_ID = int(os.environ.get("MAIN_TEAM_ROLE_ID"))
FRIENDLY_PING_ROLE_ID = int(os.environ.get("FRIENDLY_PING_ROLE_ID"))

POSITIONS = ["GK", "LB", "RB", "CB", "LW", "RW", "ST"]

intents = discord.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

friendly_matches = {}  # {msg_id: {"host": id, "players": [], "positions_msg": id, "positions": {pos:user_id}, "link_sent": bool}}

# ---------------------- /match command ----------------------
@bot.tree.command(name="match", description="Send match schedule")
@app_commands.describe(team1="First team", team2="Second team", league="League name", date="Date in DD-MM-YYYY", time="Time in HH:MM")
async def match(interaction: discord.Interaction, team1: str, team2: str, league: str, date: str, time: str):
    try:
        match_datetime = datetime.datetime.strptime(f"{date} {time}", "%d-%m-%Y %H:%M")
        timestamp = f"<t:{int(match_datetime.timestamp())}:F>"
        embed = discord.Embed(title="📢 Match Announcement", color=0x2ecc71)
        embed.add_field(name="🏟 Teams", value=f"{team1} vs {team2}", inline=False)
        embed.add_field(name="🏆 League", value=league, inline=False)
        embed.add_field(name="📅 Date & Time", value=timestamp, inline=False)
        channel = bot.get_channel(ANNOUNCE_CHANNEL_ID)
        if channel:
            await channel.send(embed=embed)
            await interaction.response.send_message("✅ Announcement sent!", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Channel not found.", ephemeral=True)
    except ValueError:
        await interaction.response.send_message("❌ Wrong date/time format. Use DD-MM-YYYY HH:MM", ephemeral=True)

# ---------------------- /trialresult command ----------------------
@bot.tree.command(name="trialresult", description="Post trial result")
@app_commands.describe(nickname="Player nickname", position="Player position", shooting="Shooting rating", passing="Passing rating",
                       mossing="Mossing rating", dribbling="Dribbling rating (optional)", defending="Defending rating (optional)", result="Trial result role")
@app_commands.choices(result=[
    app_commands.Choice(name="B TEAM", value="B_TEAM"),
    app_commands.Choice(name="A TEAM", value="A_TEAM"),
    app_commands.Choice(name="MAIN TEAM SUBS", value="MAIN_SUB"),
    app_commands.Choice(name="MAIN TEAM", value="MAIN_TEAM"),
])
async def trialresult(interaction: discord.Interaction, nickname: str, position: str, shooting: str, passing: str,
                      mossing: str, result: app_commands.Choice[str], dribbling: str = None, defending: str = None):
    embed = discord.Embed(title="📝 Trial Result", color=0x3498db)
    embed.add_field(name="🎮 Nickname", value=nickname, inline=True)
    embed.add_field(name="📌 Position", value=position, inline=True)
    embed.add_field(name="⚽ Shooting", value=shooting, inline=True)
    embed.add_field(name="🎯 Passing", value=passing, inline=True)
    embed.add_field(name="🪂 Mossing", value=mossing, inline=True)
    if dribbling:
        embed.add_field(name="🌀 Dribbling", value=dribbling, inline=True)
    if defending:
        embed.add_field(name="🛡 Defending", value=defending, inline=True)
    result_role = {"B_TEAM": f"<@&{B_TEAM_ROLE_ID}>",
                   "A_TEAM": f"<@&{A_TEAM_ROLE_ID}>",
                   "MAIN_SUB": f"<@&{MAIN_SUB_ROLE_ID}>",
                   "MAIN_TEAM": f"<@&{MAIN_TEAM_ROLE_ID}>"}[result.value]
    embed.add_field(name="📊 Result", value=result_role, inline=False)
    channel = bot.get_channel(TRIAL_RESULT_CHANNEL_ID)
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Trial result posted!", ephemeral=True)

# ---------------------- /friendlyresult command ----------------------
@bot.tree.command(name="friendlyresult", description="Post friendly match result")
@app_commands.describe(score="Match score (e.g. 3-2)", goals="Goals in format: @User:2 @Another:1",
                       assists="Assists in format: @User:1 @Another:2", motm="Man of the Match (@mention)", dotm="Defender of the Match (@mention)")
async def friendlyresult(interaction: discord.Interaction, score: str, goals: str, assists: str, motm: str, dotm: str):
    def parse_stats(raw: str):
        stats = {}
        for part in raw.split():
            if ":" in part:
                user, num = part.split(":", 1)
                stats[user] = int(num)
            else:
                stats[part] = stats.get(part, 0) + 1
        return stats
    def format_stats(stats: dict):
        return ", ".join([f"{user} ({count})" for user, count in stats.items()]) if stats else "—"
    embed = discord.Embed(title="⚡ Friendly Match Result", color=0xf1c40f)
    embed.add_field(name="📊 Score", value=score, inline=False)
    embed.add_field(name="⚽ Goals", value=format_stats(parse_stats(goals)), inline=False)
    embed.add_field(name="🎯 Assists", value=format_stats(parse_stats(assists)), inline=False)
    embed.add_field(name="🏅 MOTM", value=motm, inline=True)
    embed.add_field(name="🛡 DOTM", value=dotm, inline=True)
    channel = bot.get_channel(FRIENDLY_RESULT_CHANNEL_ID)
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ Friendly result posted!", ephemeral=True)

# ---------------------- /leagueresult command ----------------------
@bot.tree.command(name="leagueresult", description="Post league match result")
@app_commands.describe(team1="First team", team2="Second team", score="Match score (e.g. 3-2)",
                       goals="Goals in format: @User:2 @Another:1", assists="Assists in format: @User:1 @Another:2",
                       motm="Man of the Match (@mention)", dotm="Defender of the Match (@mention)")
async def leagueresult(interaction: discord.Interaction, team1: str, team2: str, score: str, goals: str, assists: str, motm: str, dotm: str):
    def parse_stats(raw: str):
        stats = {}
        for part in raw.split():
            if ":" in part:
                user, num = part.split(":", 1)
                stats[user] = int(num)
            else:
                stats[part] = stats.get(part, 0) + 1
        return stats
    def format_stats(stats: dict):
        return ", ".join([f"{user} ({count})" for user, count in stats.items()]) if stats else "—"
    embed = discord.Embed(title="🏆 League Match Result", color=0xe74c3c)
    embed.add_field(name="⚔ Teams", value=f"{team1} vs {team2}", inline=False)
    embed.add_field(name="📊 Score", value=score, inline=False)
    embed.add_field(name="⚽ Goals", value=format_stats(parse_stats(goals)), inline=False)
    embed.add_field(name="🎯 Assists", value=format_stats(parse_stats(assists)), inline=False)
    embed.add_field(name="🏅 MOTM", value=motm, inline=True)
    embed.add_field(name="🛡 DOTM", value=dotm, inline=True)
    channel = bot.get_channel(LEAGUE_RESULT_CHANNEL_ID)
    await channel.send(embed=embed)
    await interaction.response.send_message("✅ League result posted!", ephemeral=True)

# ---------------------- /friendly command ----------------------
@bot.tree.command(name="friendly", description="Start a friendly match")
async def friendly(interaction: discord.Interaction):
    author = interaction.user
    if HOST_ROLE_ID not in [role.id for role in author.roles]:
        await interaction.response.send_message("❌ You need the host role to start a friendly match.", ephemeral=True)
        return
    text = (
        "✅ **FRIENDLY MATCH** ✅\n\n"
        f"🔥 **HOST:** {author.mention}\n"
        f"👥 **PLAYERS NEEDED:** 7\n"
        f"🎮 **PLAYERS:** —"
    )
    channel = bot.get_channel(FRIENDLY_CHANNEL_ID)
    msg = await channel.send(text)
    friendly_matches[msg.id] = {"host": author.id, "players": [], "positions_msg": None, "positions": {pos: None for pos in POSITIONS}, "link_sent": False}
    await interaction.response.send_message("✅ Friendly match created!", ephemeral=True)

# ---------------------- Reaction events ----------------------
@bot.event
async def on_reaction_add(reaction, user):
    if user.bot: return
    msg_id = reaction.message.id
    if msg_id not in friendly_matches: return
    match = friendly_matches[msg_id]
    if user.id in match["players"]: return
    match["players"].append(user.id)

    players_mentions = ", ".join([f"<@{pid}>" for pid in match["players"]])
    players_needed = max(7 - len(match["players"]), 0)
    host_mention = f"<@{match['host']}>"
    text = f"✅ **FRIENDLY MATCH** ✅\n\n🔥 **HOST:** {host_mention}\n👥 **PLAYERS NEEDED:** {players_needed}\n🎮 **PLAYERS:** {players_mentions or '—'}"
    await reaction.message.edit(content=text)

    if len(match["players"]) == 7 and not match["positions_msg"]:
        pos_text = "⚡ **POSITIONS ASSIGNMENT** ⚡\n\n"
        for pos in POSITIONS:
            pos_text += f"{pos}: None\n"
        pos_msg = await reaction.message.channel.send(pos_text)
        match["positions_msg"] = pos_msg.id
        for idx, player_id in enumerate(match["players"]):
            match["positions"][POSITIONS[idx]] = player_id
        updated_text = "⚡ **POSITIONS ASSIGNMENT** ⚡\n\n"
        for pos, pid in match["positions"].items():
            mention = f"<@{pid}>" if pid else "None"
            updated_text += f"{pos}: {mention}\n"
        await pos_msg.edit(content=updated_text)

@bot.event
async def on_reaction_remove(reaction, user):
    if user.bot: return
    msg_id = reaction.message.id
    if msg_id not in friendly_matches: return
    match = friendly_matches[msg_id]
    if user.id not in match["players"]: return
    match["players"].remove(user.id)

    players_mentions = ", ".join([f"<@{pid}>" for pid in match["players"]])
    players_needed = max(7 - len(match["players"]), 0)
    host_mention = f"<@{match['host']}>"
    text = f"✅ **FRIENDLY MATCH** ✅\n\n🔥 **HOST:** {host_mention}\n👥 **PLAYERS NEEDED:** {players_needed}\n🎮 **PLAYERS:** {players_mentions or '—'}"
    await reaction.message.edit(content=text)

    if match["positions_msg"]:
        for pos, pid in match["positions"].items():
            if pid == user.id:
                match["positions"][pos] = None
        pos_msg = await reaction.message.channel.fetch_message(match["positions_msg"])
        updated_text = "⚡ **POSITIONS ASSIGNMENT** ⚡\n\n"
        for pos, pid in match["positions"].items():
            mention = f"<@{pid}>" if pid else "None"
            updated_text += f"{pos}: {mention}\n"
        await pos_msg.edit(content=updated_text)

# ---------------------- Roblox link listener ----------------------
@bot.event
async def on_message(message):
    if message.author.bot: return
    if message.channel.id != FRIENDLY_CHANNEL_ID: return
    if re.search(r"https?://(?:www\.)?roblox\.com", message.content, re.I):
        match = None
        for m in friendly_matches.values():
            if m["host"] == message.author.id and len(m["players"]) == 7 and not m["link_sent"]:
                match = m
                break
        if match:
            await message.delete()
            pos_msg = await message.channel.fetch_message(match["positions_msg"])
            players_text = ", ".join([f"<@{pid}>" for pid in match["players"]])
            text = f"🎮 **FRIENDLY MATCH READY!** 🎮\n\n🔥 **HOST:** <@{match['host']}>\n👥 **PLAYERS:** {players_text}\n🗂 **POSITIONS:**\n"
            for pos, pid in match["positions"].items():
                text += f"{pos}: <@{pid}>\n"
            text += f"\n🌐 **GAME LINK:** {message.content}\n\n🔔 <@&{FRIENDLY_PING_ROLE_ID}>"
            await message.channel.send(text)
            match["link_sent"] = True
    await bot.process_commands(message)

# ---------------------- Bot start ----------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await bot.tree.sync()
        print(f"Slash commands synced: {len(synced)}")
    except Exception as e:
        print(e)

bot.run(TOKEN)
