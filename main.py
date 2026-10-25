import os
import aiohttp
import discord
from datetime import datetime, timezone
from discord import app_commands
from discord.ext import commands
from keep_alive import keep_alive

# ================= CONFIGURATION =================
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_KEY = os.getenv("API_KEY", "TX999_API_5a1fc087033d8a5685305a288e22ffb2")
APP_ID = os.getenv("APP_ID", "9f087d585fbd666572fc24b7")
BASE_URL = "https://prtvshow.online/api_admin.php"

# Security & ID Whitelists
ALLOWED_GUILD_ID = 1525181999147388958
PRIMARY_OWNER_ID = 1525179499602509977
AUTHORIZED_USERS = {1525179499602509977, 1209489335590723654}

# Designated Channels
KEY_GEN_CHANNEL_ID = 1546969770924966029
AUDIT_LOG_CHANNEL_ID = 1547688035796254941

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

# ================= AUDIT LOGGER HELPER =================
async def send_audit_log(client: commands.Bot, title: str, user: discord.User, fields: dict, color: int = 0x2B2D31):
    try:
        log_channel = client.get_channel(AUDIT_LOG_CHANNEL_ID)
        if not log_channel:
            log_channel = await client.fetch_channel(AUDIT_LOG_CHANNEL_ID)
        
        if log_channel:
            embed = discord.Embed(
                title=f"🛡️ Audit Log | {title}",
                color=color,
                timestamp=datetime.now(timezone.utc)
            )
            role_tag = "👑 Main Admin" if user.id == PRIMARY_OWNER_ID else "🔑 Authorized Reseller"
            embed.set_author(name=f"{user.name} ({role_tag})", icon_url=user.display_avatar.url)
            
            for key, val in fields.items():
                embed.add_field(name=key, value=str(val), inline=True)
            
            embed.set_footer(text=f"User ID: {user.id}")
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f"[Audit Log Error]: {e}")

# ================= PERMISSION VERIFIER =================
async def verify_access(interaction: discord.Interaction, enforce_channel: bool = True) -> bool:
    # 1. Guild Check
    if interaction.guild_id != ALLOWED_GUILD_ID:
        embed = discord.Embed(
            title="⛔ Access Denied | Server Restricted",
            description="This bot is locked to a private server.\nPlease contact Super Admin **PERSISTX** for assistance.",
            color=0xED4245
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    # 2. User Whitelist Check
    if interaction.user.id not in AUTHORIZED_USERS:
        embed = discord.Embed(
            title="⛔ Access Denied | Unauthorized Access",
            description="You do not have authorization to use this bot.\n\n**Please contact Super Admin PERSISTX for access.**",
            color=0xED4245
        )
        embed.set_footer(text=f"Unauthorized User ID: {interaction.user.id}")
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    # 3. Channel Check
    if enforce_channel and interaction.channel_id != KEY_GEN_CHANNEL_ID:
        gen_ch = f"<#{KEY_GEN_CHANNEL_ID}>"
        embed = discord.Embed(
            title="⚠️ Channel Restriction",
            description=f"License generation commands can only be executed in {gen_ch}.",
            color=0xFEE75C
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    return True

# ================= INTERACTIVE VIEWS =================

# Key Buttons View
class KeyActionView(discord.ui.View):
    def __init__(self, key: str):
        super().__init__(timeout=None)
        self.key = key

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in AUTHORIZED_USERS:
            embed = discord.Embed(
                title="⛔ Action Denied",
                description="You do not have permission to manage this license.\n\n**Please contact Super Admin PERSISTX for access.**",
                color=0xED4245
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Reset HWID", style=discord.ButtonStyle.primary, custom_id="btn_reset_hwid")
    async def reset_hwid_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "reset_hwid", "key": self.key})
        status_text = res.get("message", "HWID reset successfully.") if res.get("success") else res.get("message", "Failed to reset HWID.")
        
        await send_audit_log(
            interaction.client,
            title="HWID Reset Action",
            user=interaction.user,
            fields={"Key": f"`{self.key}`", "Status": "Success" if res.get("success") else "Failed", "Detail": status_text},
            color=0x3498DB if res.get("success") else 0xE74C3C
        )
        await interaction.followup.send(f"**[{self.key}]** {status_text}", ephemeral=True)

    @discord.ui.button(label="Ban", style=discord.ButtonStyle.danger, custom_id="btn_ban_key")
    async def ban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "ban_key", "key": self.key})
        status_text = res.get("message", "Key has been banned.") if res.get("success") else res.get("message", "Failed to ban key.")
        
        await send_audit_log(
            interaction.client,
            title="License Key Banned",
            user=interaction.user,
            fields={"Key": f"`{self.key}`", "Status": "Banned", "Detail": status_text},
            color=0xE74C3C
        )
        await interaction.followup.send(f"**[{self.key}]** {status_text}", ephemeral=True)

    @discord.ui.button(label="Unban", style=discord.ButtonStyle.success, custom_id="btn_unban_key")
    async def unban_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "unban_key", "key": self.key})
        status_text = res.get("message", "Key has been unbanned.") if res.get("success") else res.get("message", "Failed to unban key.")
        
        await send_audit_log(
            interaction.client,
            title="License Key Unbanned",
            user=interaction.user,
            fields={"Key": f"`{self.key}`", "Status": "Unbanned", "Detail": status_text},
            color=0x2ECC71
        )
        await interaction.followup.send(f"**[{self.key}]** {status_text}", ephemeral=True)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.secondary, custom_id="btn_delete_key")
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "delete_key", "key": self.key})
        status_text = res.get("message", "Key has been deleted.") if res.get("success") else res.get("message", "Failed to delete key.")
        
        await send_audit_log(
            interaction.client,
            title="License Key Deleted",
            user=interaction.user,
            fields={"Key": f"`{self.key}`", "Status": "Deleted", "Detail": status_text},
            color=0x95A5A6
        )
        await interaction.followup.send(f"**[{self.key}]** {status_text}", ephemeral=True)

# UID Quick Delete View
class UIDActionView(discord.ui.View):
    def __init__(self, uid: str):
        super().__init__(timeout=None)
        self.uid = uid

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id not in AUTHORIZED_USERS:
            embed = discord.Embed(
                title="⛔ Action Denied",
                description="You do not have permission to manage this UID.\n\n**Please contact Super Admin PERSISTX for access.**",
                color=0xED4245
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return False
        return True

    @discord.ui.button(label="🗑️ Remove / Delete UID", style=discord.ButtonStyle.danger, custom_id="btn_delete_uid")
    async def delete_uid_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)
        res = await request_api({"action": "remove_uid", "uid": self.uid})
        
        if res.get("success"):
            await send_audit_log(
                interaction.client,
                title="UID Removed",
                user=interaction.user,
                fields={"UID": f"`{self.uid}`", "Status": "Removed via Button"},
                color=0xE74C3C
            )
            await interaction.followup.send(f"✅ Player UID `{self.uid}` has been removed.", ephemeral=True)
            self.delete_uid_btn.disabled = True
            await interaction.edit_original_response(view=self)
        else:
            err = res.get("message", "Failed to remove UID.")
            await interaction.followup.send(f"❌ Error: {err}", ephemeral=True)

# ================= BOT INITIALIZATION =================
intents = discord.Intents.default()
intents.message_content = True

class ResellerBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        target_guild = discord.Object(id=ALLOWED_GUILD_ID)
        self.tree.copy_global_to(guild=target_guild)
        synced = await self.tree.sync(guild=target_guild)
        print(f">>> [SUCCESS] Synced {len(synced)} command(s) exclusively to Guild: {ALLOWED_GUILD_ID}")

bot = ResellerBot()

@bot.event
async def on_ready():
    print(f">>> Logged in as: {bot.user} (ID: {bot.user.id})")

# Manual Sync Command (Restricted to Primary Owner only)
@bot.command(name="sync")
async def manual_sync(ctx):
    if ctx.author.id != PRIMARY_OWNER_ID or ctx.guild.id != ALLOWED_GUILD_ID:
        return
    target_guild = discord.Object(id=ALLOWED_GUILD_ID)
    bot.tree.copy_global_to(guild=target_guild)
    synced = await bot.tree.sync(guild=target_guild)
    await ctx.send(f"✅ System commands synced: `{len(synced)}` commands active on target server.")

# ================= SLASH COMMANDS =================

# 1. GENERATE PACKAGE KEY
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
    if not await verify_access(interaction, enforce_channel=True):
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

    if extracted_key:
        embed = discord.Embed(title="🔑 Package License Key Generated", color=0x2ECC71)
        embed.add_field(name="Package Name", value=f"**{package.name.upper()}**", inline=True)
        embed.add_field(name="Duration", value=f"{days} Days" if days > 0 else "Lifetime", inline=True)
        embed.add_field(name="Count", value="1", inline=True)
        embed.add_field(name="Keys", value=f"```{extracted_key}```", inline=False)
        
        view = KeyActionView(key=str(extracted_key).strip())
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
        # Send Audit Log
        await send_audit_log(
            interaction.client,
            title="Key Generated",
            user=interaction.user,
            fields={
                "Package": package.name,
                "Duration": f"{days} Days" if days > 0 else "Lifetime",
                "Key": f"`{extracted_key}`",
                "Note": note if note else "None"
            },
            color=0x2ECC71
        )
    else:
        err_msg = data.get("message", "API did not return a valid key.")
        embed = discord.Embed(title="❌ Key Generation Failed", description=f"**Error:** {err_msg}", color=0xE74C3C)
        await interaction.followup.send(embed=embed, ephemeral=True)

# 2. FREE FIRE UID WHITELIST
@bot.tree.command(name="whitelist", description="Whitelist a Free Fire player UID")
@app_commands.describe(
    uid="Player numeric Free Fire UID",
    region="Server region (Default: IND)",
    days="Whitelist duration (Default: 30, 0 for Lifetime)"
)
async def whitelist(interaction: discord.Interaction, uid: str, region: str = "IND", days: int = 30):
    if not await verify_access(interaction, enforce_channel=True):
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

    view = UIDActionView(uid=uid.strip()) if data.get("success") else None
    await interaction.followup.send(embed=embed, view=view, ephemeral=True)

    # Send Audit Log
    await send_audit_log(
        interaction.client,
        title="UID Whitelisted",
        user=interaction.user,
        fields={
            "UID": f"`{uid}`",
            "Region": region.upper(),
            "Duration": f"{days} Days" if days > 0 else "Lifetime",
            "Status": "Success" if data.get("success") else "Failed"
        },
        color=0x3498DB if data.get("success") else 0xE74C3C
    )

# 3. DIRECT REMOVE/DELETE UID
@bot.tree.command(name="removeuid", description="Remove/Delete a Free Fire UID from whitelist")
@app_commands.describe(uid="Player numeric Free Fire UID to remove")
async def removeuid(interaction: discord.Interaction, uid: str):
    if not await verify_access(interaction, enforce_channel=True):
        return

    await interaction.response.defer(ephemeral=True)

    params = {"action": "remove_uid", "uid": uid.strip()}
    data = await request_api(params)

    embed = discord.Embed(title="UID Removal Status", color=0x2ECC71 if data.get("success") else 0xE74C3C)
    embed.add_field(name="UID", value=uid.strip(), inline=True)
    embed.add_field(name="Result", value=data.get("message", "Action processed"), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

    # Send Audit Log
    await send_audit_log(
        interaction.client,
        title="UID Removed Manually",
        user=interaction.user,
        fields={"UID": f"`{uid}`", "Result": data.get("message", "Executed")},
        color=0xE74C3C
    )

# 4. GENERATE LIB BYPASS KEY (V1 & V2)
@bot.tree.command(name="genlib", description="Generate a Lib Bypass key")
@app_commands.describe(
    custom_key="Custom username/key label",
    version="Engine Version (v1 or v2)",
    days="Duration in days (Default: 30, 0 for Lifetime)"
)
@app_commands.choices(version=[
    app_commands.Choice(name="Version 1 (V1)", value="v1"),
    app_commands.Choice(name="Version 2 (V2)", value="v2")
])
async def genlib(interaction: discord.Interaction, custom_key: str, version: app_commands.Choice[str] = None, days: int = 30):
    if not await verify_access(interaction, enforce_channel=True):
        return

    await interaction.response.defer(ephemeral=True)

    selected_version = version.value if version else "v1"

    params = {
        "action": "generate_lib_key",
        "lib_version": selected_version,
        "days": days,
        "custom_key": custom_key.strip()
    }
    data = await request_api(params)

    embed = discord.Embed(title="Lib Bypass Key Generated", color=0x9B59B6 if data.get("success") else 0xE74C3C)
    embed.add_field(name="Engine", value=selected_version.upper(), inline=True)
    embed.add_field(name="Target User", value=custom_key, inline=True)
    embed.add_field(name="Duration", value=f"{days} Days" if days > 0 else "Lifetime", inline=True)

    if data.get("success"):
        key = data.get("key") or custom_key
        embed.add_field(name="Key", value=f"```{key}```", inline=False)
        view = KeyActionView(key=str(key).strip())
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        
        # Send Audit Log
        await send_audit_log(
            interaction.client,
            title="Lib Bypass Key Generated",
            user=interaction.user,
            fields={
                "Engine": selected_version.upper(),
                "Target User": custom_key,
                "Duration": f"{days} Days" if days > 0 else "Lifetime",
                "Key": f"`{key}`"
            },
            color=0x9B59B6
        )
    else:
        embed.add_field(name="Error", value=data.get("message", "Failed to generate key"), inline=False)
        await interaction.followup.send(embed=embed, ephemeral=True)

# 5. RESET HWID DIRECT COMMAND
@bot.tree.command(name="resethwid", description="Reset HWID lock for a key")
@app_commands.describe(key="License key to reset")
async def resethwid(interaction: discord.Interaction, key: str):
    if not await verify_access(interaction, enforce_channel=False):
        return

    await interaction.response.defer(ephemeral=True)

    params = {"action": "reset_hwid", "key": key.strip()}
    data = await request_api(params)

    embed = discord.Embed(title="HWID Reset Status", color=0x2ECC71 if data.get("success") else 0xE74C3C)
    embed.add_field(name="Key", value=f"`{key.strip()}`", inline=False)
    embed.add_field(name="Result", value=data.get("message", "Action completed"), inline=False)

    await interaction.followup.send(embed=embed, ephemeral=True)

    # Send Audit Log
    await send_audit_log(
        interaction.client,
        title="Direct HWID Reset",
        user=interaction.user,
        fields={"Key": f"`{key}`", "Result": data.get("message", "Executed")},
        color=0x3498DB
    )

# ================= RUN SERVER & BOT =================
keep_alive()

if TOKEN:
    bot.run(TOKEN)
else:
    print("Error: DISCORD_BOT_TOKEN environment variable is missing.")
