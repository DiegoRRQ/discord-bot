import discord
import os
import time
import random

PXGHOUL_ID = 1278727608065986685
COOLDOWN_SECONDS = 60

KEY_TRIGGERS = ["key", "keys"]
KEY_RESPONSE = (
    "All the keys for Diego's scripts can be found in "
    "https://discord.com/channels/1458595915463000147/1459979110481793188"
)

# Randomized responses by status
RESPONSES = {
    "offline": [
        "Diego is currently offline, please be patient!",
        "Diego is offline right now, he’ll respond when he’s back.",
    ],
    "online": [
        "Diego will respond as soon as he can, please be patient.",
        "Diego is around and will reply when he can.",
    ],
    "idle": [
        "Diego will respond as soon as he can, please be patient.",
        "Diego may be away, but he’ll get back to you.",
    ],
    "dnd": [
        "Diego is currently busy, please be patient and do not @ him again.",
        "Diego is busy right now, please avoid pinging him.",
    ],
}

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)

# State
ping_cooldowns = {}
bot_enabled = True

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    global bot_enabled

    if message.author == client.user:
        return

    msg = message.content.lower()

    # -------- OWNER-ONLY COMMANDS --------
    if message.author.id == PXGHOUL_ID:
        if msg == "!bot off":
            bot_enabled = False
            await message.reply("✅ Bot disabled.")
            return

        if msg == "!bot on":
            bot_enabled = True
            await message.reply("✅ Bot enabled.")
            return

        if msg == "!status":
            state = "enabled" if bot_enabled else "disabled"
            await message.reply(f"ℹ️ Bot is currently **{state}**.")
            return

    if not bot_enabled:
        return

    # -------- KEY / KEYS HANDLER --------
    if any(word in msg.split() for word in KEY_TRIGGERS):
        await message.reply(KEY_RESPONSE)
        return

    # -------- PXGHOUL MENTION HANDLER (WITH COOLDOWN) --------
    if PXGHOUL_ID in [user.id for user in message.mentions]:
        now = time.time()
        last_ping = ping_cooldowns.get(message.author.id, 0)

        if now - last_ping < COOLDOWN_SECONDS:
            return  # silently ignore spam

        ping_cooldowns[message.author.id] = now

        member = message.guild.get_member(PXGHOUL_ID)
        if not member:
            return

        status = member.status

        if status == discord.Status.offline:
            response = random.choice(RESPONSES["offline"])
        elif status == discord.Status.dnd:
            response = random.choice(RESPONSES["dnd"])
        elif status == discord.Status.idle:
            response = random.choice(RESPONSES["idle"])
        else:
            response = random.choice(RESPONSES["online"])

        await message.reply(response)

client.run(os.environ["DISCORD_TOKEN"])
