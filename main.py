import os
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# ================= CONFIGURATION =================
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_KEY = os.getenv("API_KEY", "TX999_API_5a1fc087033d8a5685305a288e22ffb2")
APP_ID = os.getenv("APP_ID", "9f087d585fbd666572fc24b7")
BASE_URL = "https://prtvshow.online/api_admin.php"

# Packages mapping (Panel Package IDs)
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

# ================= API HELPER =================
async def request_api(params: dict) -> dict:
    params["api_key"] = API_KEY
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(BASE_URL, params=params, timeout=12) as resp:
                try:
                    return await resp.json(content_type=None)
                except Exception:
                    raw_text = await resp.text()
                    return {"success": False, "message": f"Non-JSON response: {raw_text[:200]}"}
        except Exception as e:
            return {"success": False, "message": f"Connection error: {str(e)}"}

# ================= INTERACTIVE BUTTONS =================
class KeyActionView(discord.ui.View):
    def __init__(self, key: str):
        super().__init__(timeout=None)
        self.key = key

    @discord.ui.button(label="Reset HWID", style=discord.ButtonStyle.primary, custom_id="btn_reset_hwid")
    async def reset_hwid_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "reset_hwid", "key": self.key})
        status_text = res.get("message", "HWID reset successfully.") if res.get("success") else res.get("message", "Failed to reset HWID.")
        await interaction.followup.send(f"**[{self.key}]** {status_text}", ephemeral=True)

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger, custom_id="btn_ban_key")
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "ban_key", "key": self.key})
        status_text = res.get("message", "Key has been banned.") if res.get("success") else res.get("message", "Failed to ban key.")
        await interaction.followup.send(f"**[{self.key}]** {status_text}", ephemeral=True)

    @discord.ui.button(label="Unban", style=discord.ButtonStyle.success, custom_id="btn_unban_key")
    async def unban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "unban_key", "key": self.key})
        status_text = res.get("message", "Key has been unbanned.") if res.get("success") else res.get("message", "Failed to unban key.")
        await interaction.followup.send(f"**[{self.key}]** {status_text}", ephemeral=True)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.secondary, custom_id="btn_delete_key")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "delete_key", "key": self.key})
        status_text = res.get("message", "Key has been deleted.") if res.get("success") else res.get("message", "Failed to delete key.")
        await interaction.followup.send(f"**[{self.key}]** {status_text}", ephemeral=True)

# ================= BOT INITIALIZATION =================
intents = discord.Intents.default()
intents.message_content = True

class ResellerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        await self.tree.sync()
        print(">>> Global commands indexed.")

bot = ResellerBot()

@bot.event
async def on_ready():
    print(f">>> Logged in as: {bot.user} (ID: {bot.user.id})")
    for guild in bot.guilds:
        try:
            bot.tree.copy_global_to(guild=guild)
            synced = await bot.tree.sync(guild=guild)
            print(f">>> [SUCCESS] Synced {len(synced)} command(s) to server: {guild.name}")
        except Exception as e:
            print(f">>> [ERROR] Sync failed for {guild.name}: {e}")

@bot.command(name="sync")
@commands.has_permissions(administrator=True)
async def manual_sync(ctx):
    try:
        bot.tree.copy_global_to(guild=ctx.guild)
        synced = await bot.tree.sync(guild=ctx.guild)
        await ctx.send(f"✅ Commands forcefully synced: `{len(synced)}` commands active!")
    except Exception as e:
        await ctx.send(f"❌ Sync failed: `{e}`")

# ================= SLASH COMMANDS =================

# 1. GENERATE PACKAGE LICENSE KEY
@bot.tree.command(name="genkey", description="Generate a package license key")
@app_commands.describe(
    package="Select the software package",
    days="Duration in days (Default: 1, 0 for Lifetime)",
    note="Customer note (Optional)"
)
@app_commands.choices(package=[
    app_commands.Choice(name=name, value=pkg_id) for name, pkg_id in PACKAGES.items()
])
async def genkey(interaction: discord.Interaction, package: app_commands.Choice[str], days: int = 1, note: str = ""):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permission denied.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    params = {
        "action": "generate_key",
        "app_id": APP_ID,
        "package_id": package.value,
        "days": days,
        "amount": 1,
        "note": note
    }
    
    data = await request_api(params)
    print("API RESPONSE DEBUG:", data)

    # Key Extraction Logic (Handles strings, arrays, and nested structures)
    extracted_key = None
    if isinstance(data, dict):
        if data.get("key"):
            extracted_key = data.get("key")
        elif data.get("keys"):
            raw_keys = data.get("keys")
            extracted_key = raw_keys[0] if isinstance(raw_keys, list) and raw_keys else str(raw_keys)
        elif data.get("license_key"):
            extracted_key = data.get("license_key")
        elif data.get("data"):
            inner = data.get("data")
            if isinstance(inner, dict):
                extracted_key = inner.get("key") or (inner.get("keys")[0] if isinstance(inner.get("keys"), list) and inner.get("keys") else inner.get("keys"))
            elif isinstance(inner, list) and inner:
                extracted_key = inner[0]

    # Success Embed Matching Image 2
    if extracted_key:
        embed = discord.Embed(
            title="🔑 Package License Key Generated",
            color=0x2ECC71
        )
        embed.add_field(name="Package Name", value=f"**{package.name.upper()}**", inline=True)
        embed.add_field(name="Duration", value=f"{days} Days" if days > 0 else "Lifetime", inline=True)
        embed.add_field(name="Count", value="1", inline=True)
        embed.add_field(name="Keys", value=f"```{extracted_key}```", inline=False)
        
        view = KeyActionView(key=str(extracted_key).strip())
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        err_msg = data.get("message", "API did not return a valid license key.")
        embed = discord.Embed(
            title="❌ Key Generation Failed",
            description=f"**Error:** {err_msg}",
            color=0xE74C3C
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

# 2. FREE FIRE UID WHITELIST
@bot.tree.command(name="whitelist", description="Whitelist a Free Fire player UID")
@app_commands.describe(
    uid="Player numeric Free Fire UID",
    region="Server region (Default: IND)",
    days="Whitelist duration (Default: 30, 0 for Lifetime)"
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

    embed = discord.Embed(
        title="UID Whitelist Status",
        color=0x3498DB if data.get("success") else 0xE74C3C
    )
    embed.add_field(name="UID", value=uid, inline=True)
    embed.add_field(name="Region", value=region.upper(), inline=True)
    embed.add_field(name="Duration", value=f"{days} Days" if days > 0 else "Lifetime", inline=True)
    embed.add_field(name="Result", value=data.get("message", "Processed successfully"), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

# 3. GENERATE LIB BYPASS KEY
@bot.tree.command(name="genlib", description="Generate a Lib Bypass key")
@app_commands.describe(
    custom_key="Custom username/key label",
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

    embed = discord.Embed(
        title="Lib Bypass Key Generated",
        color=0x9B59B6 if data.get("success") else 0xE74C3C
    )
    embed.add_field(name="Engine", value="V1", inline=True)
    embed.add_field(name="Target User", value=custom_key, inline=True)
    embed.add_field(name="Duration", value=f"{days} Days" if days > 0 else "Lifetime", inline=True)

    if data.get("success"):
        key = data.get("key") or custom_key
        embed.add_field(name="Key", value=f"```{key}```", inline=False)
        view = KeyActionView(key=str(key).strip())
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
    else:
        embed.add_field(name="Error", value=data.get("message", "Failed to generate key"), inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

# 4. RESET HWID DIRECT COMMAND
@bot.tree.command(name="resethwid", description="Reset HWID lock for a key")
@app_commands.describe(key="License key to reset")
async def resethwid(interaction: discord.Interaction, key: str):
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("Permission denied.", ephemeral=True)
        return

    await interaction.response.defer(ephemeral=True)

    params = {
        "action": "reset_hwid",
        "key": key.strip()
    }
    data = await request_api(params)

    embed = discord.Embed(
        title="HWID Reset Status",
        color=0x2ECC71 if data.get("success") else 0xE74C3C
    )
    embed.add_field(name="Key", value=f"`{key.strip()}`", inline=False)
    embed.add_field(name="Result", value=data.get("message", "Action completed"), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

# ================= RUN SERVER & BOT =================
keep_alive()

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_BOT_TOKEN environment variable is missing.")
