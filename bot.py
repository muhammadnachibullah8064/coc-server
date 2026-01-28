import os

import discord
import requests
from discord.ext import commands
from dotenv import load_dotenv

# load env
load_dotenv()

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
API_BASE = os.getenv("API_BASE_URL")

if not DISCORD_BOT_TOKEN or not API_BASE:
    raise RuntimeError("Missing DISCORD_BOT_TOKEN or API_BASE_URL in .env")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)

HERO_CHANNEL_NAME = "hero"  # exact channel name
HERO_EQUIPMENT_CHANNEL = "hero-equipment"


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    HERO_EQUIPMENT_CHANNEL = "hero-equipment"


@bot.event
async def on_message(message):
    if message.author.bot:
        return

    # 🔧 HERO EQUIPMENT CHANNEL
    if message.channel.name == HERO_EQUIPMENT_CHANNEL:
        raw = message.content.strip()
        if not raw.startswith("#"):
            return

        tag = raw.replace("#", "")

        try:
            r = requests.get(
                f"{API_BASE}/hero/equipment/calc/{tag}",
                timeout=20
            )
            r.raise_for_status()
            data = r.json()
        except Exception:
            await message.reply("❌ Failed to fetch equipment data")
            return

        heroes = data.get("heroes", {})
        if not heroes:
            await message.reply("No equipment data found.")
            return

        for hero, equipment_map in heroes.items():
            msg = [f"⚙️ **Hero Equipment – {hero}**\n"]

            for eq_name, info in equipment_map.items():
                cur = info["current"]
                mx = info["max"]
                total = info.get("total", {})

                if cur >= mx:
                    msg.append(
                        f"• **{eq_name}**: {cur} / {mx}  MAXED ✅"
                    )
                else:
                    msg.append(
                        f"• **{eq_name}**: {cur} / {mx}\n"
                        f"  ➜ Full max need → "
                        f"🟡 {total.get('shiny',0)}  "
                        f"🔵 {total.get('glowy',0)}  "
                        f"⭐ {total.get('starry',0)}"
                    )

            await message.reply("\n".join(msg))
        return


    if message.channel.name != HERO_CHANNEL_NAME:
        return

    raw = message.content.strip()
    if not raw.startswith("#"):
        return

    tag = raw.replace("#", "")

    try:
        r = requests.get(f"{API_BASE}/hero/calc/{tag}", timeout=20)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print("API ERROR:", e)
        await message.reply("❌ Failed to calculate hero upgrade time")
        return

    lines = ["👑 **Hero Upgrade Progress**\n"]

    # 🏠 Home Village
    lines.append("🏠 **Home Village Heroes**")
    for name, info in data.get("home", {}).items():
        if info["remainingLevels"] == 0:
            lines.append(f"• **{name}**: MAXED ✅")
        else:
            t = info["time"]
            lines.append(
                f"• **{name}**: {info['current']} / {info['max']}  "
                f"(⏳ {t['days']}d {t['hours']}h, {info['remainingLevels']} lv left)"
            )

    # 🏗️ Builder Base
    lines.append("\n🏗️ **Builder Base Heroes**")
    for name, info in data.get("builder", {}).items():
        t = info["time"]

        if info["remainingLevels"] == 0:
            lines.append(f"• **{name}**: MAXED ✅")
        else:
            lines.append(
                f"• **{name}**: {info['current']} / {info['max']}  "
                f"(⏳ {t['days']}d {t['hours']}h, {info['remainingLevels']} lv left)"
            )

    await message.reply("\n".join(lines))
    # ⬇️ IMPORTANT: keep old logic alive
    await bot.process_commands(message)


bot.run(DISCORD_BOT_TOKEN)
