import os
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# Environment configuration
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_KEY = os.getenv("API_KEY", "TX999_API_5a1fc087033d8a5685305a288e22ffb2")
APP_ID = os.getenv("APP_ID", "9f087d585fbd666572fc24b7")
BASE_URL = "https://prtvshow.online/api_admin.php"

# Package IDs mapping
PACKAGES = {
    "Basic Panel": "e52c1515c53453b85d0d4e87",
    "Aimsilent Exe": "affc8da8fd5ace99981ab877",
    "UID Bypass": "cb921031dc43197e8ccb6828",
    "External Panel": "3d1c6c948b4715fbd2fada2d",
    "Pvt Aimkill": "d4f0ce93349f236711344cb5",
    "Vault Panel": "154d1edaddd7203fbfd847f4",
    "Lib Bypass": "db3b90e8134ec738b94a9b05",
    "FPS Booster": "2411bc9db9f9a66c6e876ad2",
    "Silent Kill": "442eeb4396fbc11d19c4b817",
    "Kernel Root": "e75e66eec77acc331098a0ad"
}

# Intents configuration
intents = discord.Intents.default()
intents.message_content = True  # Prefix commands ke liye

class ResellerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Global sync register karta hai
        await self.tree.sync()
        print(">>> Global command tree prepared.")

bot = ResellerBot()

# HTTP Request Helper
async def request_api(params: dict) -> dict:
    params["api_key"] = API_KEY
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(BASE_URL, params=params, timeout=10) as resp:
                return await resp.json(content_type=None)
        except Exception as e:
            return {"success": False, "message": f"Connection Error: {str(e)}"}

@bot.event
async def on_ready():
    print(f">>> Logged in as: {bot.user} (ID: {bot.user.id})")
    
    # Jin servers me bot present hai, un sabhi me turant commands push karna
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f">>> [SUCCESS] Synced {len(synced)} command(s) to server: {guild.name} (ID: {guild.id})")
        except Exception as e:
            print(f">>> [ERROR] Could not sync to server {guild.name}: {e}")

# Manual sync command (Chat me `!sync` type karke run karne ke liye)
@bot.command(name="sync")
@commands.has_permissions(administrator=True)
async def manual_sync(ctx):
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"Commands forcefully synced: `{len(synced)}` commands are ready!")
    except Exception as e:
        await ctx.send(f"Sync failed: `{e}`")

# ─────────────────────────────────────────────────────────────
# 1. Standard License Key Generator
# ─────────────────────────────────────────────────────────────
@bot.tree.command(name="genkey", description="Generate a standard license key")
@app_commands.describe(
    package="Select the software package",
    days="Duration in days (0 for Lifetime)",
    note="Customer note or username"
)
@app_commands.choices(package=[
    app_commands.Choice(name=name, value=pkg_id) for name, pkg_id in PACKAGES.items()
])
async def genkey(interaction: discord.Interaction, package: app_commands.Choice[str], days: int = 30, note: str = ""):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permission denied.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    params = {
        "action": "generate_key",
        "app_id": APP_ID,
        "package_id": package.value,
        "days": days,
        "note": note
    }
    data = await request_api(params)

    embed = discord.Embed(title="Key Generation Result", color=0x2ECC71 if data.get("success") else 0xE74C3C)
    embed.add_field(name="Package", value=package.name, inline=True)
    embed.add_field(name="Duration", value=f"{days} Days" if days > 0 else "Lifetime", inline=True)

    if data.get("success"):
        key = data.get("key") or data.get("license_key") or data.get("data", {}).get("key", "N/A")
        embed.add_field(name="License Key", value=f"```{key}```", inline=False)
        if note:
            embed.add_field(name="Reference Note", value=note, inline=False)
    else:
        embed.add_field(name="Error", value=data.get("message", "API request failed"), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

# ─────────────────────────────────────────────────────────────
# 2. Free Fire UID Whitelist Command
# ─────────────────────────────────────────────────────────────
@bot.tree.command(name="whitelist", description="Whitelist a Free Fire player UID")
@app_commands.describe(
    uid="In-game numeric UID",
    region="Account region code (Default: IND)",
    days="Whitelist duration in days (0 for Lifetime)"
)
async def whitelist(interaction: discord.Interaction, uid: str, region: str = "IND", days: int = 30):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permission denied.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    params = {
        "action": "whitelist_uid",
        "uid": uid.strip(),
        "region": region.upper(),
        "days": days
    }
    data = await request_api(params)

    embed = discord.Embed(title="UID Whitelist Status", color=0x3498DB if data.get("success") else 0xE74C3C)
    embed.add_field(name="UID", value=uid, inline=True)
    embed.add_field(name="Region", value=region.upper(), inline=True)
    embed.add_field(name="Duration", value=f"{days} Days" if days > 0 else "Lifetime", inline=True)
    embed.add_field(name="Result", value=data.get("message", "Operation processed"), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

# ─────────────────────────────────────────────────────────────
# 3. Lib Bypass Key Generator
# ─────────────────────────────────────────────────────────────
@bot.tree.command(name="genlib", description="Generate a Lib Bypass key")
@app_commands.describe(
    custom_key="Custom username/key name",
    days="Duration in days (Default: 30, 0 for Lifetime)"
)
async def genlib(interaction: discord.Interaction, custom_key: str, days: int = 30):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permission denied.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    params = {
        "action": "generate_lib_key",
        "lib_version": "v1",
        "days": days,
        "custom_key": custom_key.strip()
    }
    data = await request_api(params)

    embed = discord.Embed(title="Lib Bypass Key Generated", color=0x9B59B6 if data.get("success") else 0xE74C3C)
    embed.add_field(name="Engine", value="V1", inline=True)
    embed.add_field(name="Target User", value=custom_key, inline=True)
    embed.add_field(name="Duration", value=f"{days} Days" if days > 0 else "Lifetime", inline=True)

    if data.get("success"):
        key = data.get("key") or custom_key
        embed.add_field(name="Key", value=f"```{key}```", inline=False)
    else:
        embed.add_field(name="Error", value=data.get("message", "Failed to generate key"), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

# ─────────────────────────────────────────────────────────────
# 4. Key Management (Reset HWID)
# ─────────────────────────────────────────────────────────────
@bot.tree.command(name="resethwid", description="Reset HWID lock for a license key")
@app_commands.describe(key="License key string")
async def resethwid(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permission denied.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    params = {
        "action": "reset_lib_hwid" if "lib" in key.lower() else "reset_hwid",
        "key": key.strip()
    }
    data = await request_api(params)

    embed = discord.Embed(title="HWID Reset Status", color=0x2ECC71 if data.get("success") else 0xE74C3C)
    embed.add_field(name="Key", value=f"`{key.strip()}`", inline=False)
    embed.add_field(name="Response", value=data.get("message", "Action completed"), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

# Start web server & Discord client
keep_alive()
if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_BOT_TOKEN environment variable is not set.")
