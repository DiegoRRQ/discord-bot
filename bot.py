import discord
import os
import time
import random
import asyncio
from datetime import datetime

PXGHOUL_ID = 1278727608065986685
COOLDOWN_SECONDS = 60
MAX_PINGS = 3

FAKE_REPLY_CHANCE = 0.25
WEBHOOK_REPLY_CHANCE = 0.40  # webhook impersonation chance

KEY_TRIGGERS = ["key", "keys"]
KEY_RESPONSE = (
    "All the keys for Diego's scripts can be found in "
    "https://discord.com/channels/1458595915463000147/1459979110481793188"
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True
intents.dm_messages = True

client = discord.Client(intents=intents)

# ---- STATE ----
ping_cooldowns = {}
ping_counts = {}
ignored_users = set()

bot_enabled = True
ghost_mode = False
current_mood = "chill"
last_online_time = None
last_impersonated_user = None

RESPONSES = {
    "chill": {
        "offline": [
            "Diego is offline right now, please be patient.",
            "Diego’s not online at the moment."
        ],
        "online": [
            "Diego will respond when he can.",
            "He’ll get back to you shortly."
        ],
        "dnd": [
            "Diego is busy right now."
        ]
    },
    "busy": {
        "offline": [
            "Diego is offline."
        ],
        "online": [
            "Diego is busy, please wait."
        ],
        "dnd": [
            "Diego is currently busy. Do not ping again."
        ]
    },
    "menace": {
        "offline": [
            "He’s offline. Don’t wait up."
        ],
        "online": [
            "He saw it. He’ll respond if needed."
        ],
        "dnd": [
            "Do not ping him again."
        ]
    }
}

FAKE_REPLIES = [
    "yeah give me a bit",
    "one sec",
    "i’ll check soon",
    "busy rn",
    "give me a minute"
]

# ---------- WEBHOOK HELPERS ----------

async def get_or_create_webhook(channel):
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == "pxghoul-ghost":
            return webhook
    return await channel.create_webhook(name="pxghoul-ghost")


async def fake_typing_delay(channel):
    delay = random.uniform(2.0, 6.0)
    async with channel.typing():
        await asyncio.sleep(delay)


async def send_as_pxghoul(message, content):
    member = message.guild.get_member(PXGHOUL_ID)
    if not member:
        return

    await fake_typing_delay(message.channel)

    webhook = await get_or_create_webhook(message.channel)
    await webhook.send(
        content=content,
        username=member.display_name,
        avatar_url=member.display_avatar.url
    )

# ---------- EVENTS ----------

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_presence_update(before, after):
    global last_online_time
    if after.id == PXGHOUL_ID:
        if after.status == discord.Status.offline:
            last_online_time = datetime.utcnow()
        elif before.status == discord.Status.offline:
            last_online_time = None

@client.event
async def on_message(message):
    global ghost_mode, current_mood, last_impersonated_user

    if message.author == client.user:
        return

    msg = message.content.lower()

    # ---- OWNER COMMANDS ----
    if message.author.id == PXGHOUL_ID:
        if msg == "!ghost on":
            ghost_mode = True
            await message.reply("👻 Ghost mode enabled.")
            return

        if msg == "!ghost off":
            ghost_mode = False
            await message.reply("👻 Ghost mode disabled.")
            return

        if msg.startswith("!mood "):
            mood = msg.split(" ", 1)[1]
            if mood in RESPONSES:
                current_mood = mood
                await message.reply(f"🎭 Mood set to **{mood}**.")
            return

    if not bot_enabled:
        return

    # ---- KEY HANDLER ----
    if any(word in msg.split() for word in KEY_TRIGGERS):
        await message.reply(KEY_RESPONSE)
        return

    # ---- SILENT IGNORE ----
    if message.author.id in ignored_users:
        return

    # ---- PXGHOUL MENTION ----
    if PXGHOUL_ID in [u.id for u in message.mentions]:
        now = time.time()
        last = ping_cooldowns.get(message.author.id, 0)

        if now - last < COOLDOWN_SECONDS:
            ping_counts[message.author.id] = ping_counts.get(message.author.id, 0) + 1
            if ping_counts[message.author.id] >= MAX_PINGS:
                ignored_users.add(message.author.id)
            return

        ping_cooldowns[message.author.id] = now
        ping_counts[message.author.id] = 1

        member = message.guild.get_member(PXGHOUL_ID)
        if not member:
            return

        status = member.status.name.lower()

        # ---- GHOST MODE ----
        if ghost_mode:
            try:
                dm = await member.create_dm()
                await dm.send(
                    f"👻 **Ghost Ping**\n"
                    f"User: {message.author}\n"
                    f"Channel: #{message.channel}\n"
                    f"Message: {message.content}"
                )
            except:
                pass
            return

        # ---- WEBHOOK IMPERSONATION ----
        if (
            status != "dnd"
            and random.random() < WEBHOOK_REPLY_CHANCE
            and message.author.id != last_impersonated_user
        ):
            fake = random.choice(FAKE_REPLIES)
            await send_as_pxghoul(message, fake)
            last_impersonated_user = message.author.id
            return

        # ---- NORMAL BOT RESPONSE ----
        pool = RESPONSES[current_mood].get(status, RESPONSES[current_mood]["online"])
        response = random.choice(pool)

        if status == "offline" and last_online_time:
            delta = datetime.utcnow() - last_online_time
            mins = int(delta.total_seconds() // 60)
            response += f"\n(Last online {mins} minutes ago)"

        await message.reply(response)

client.run(os.environ["DISCORD_TOKEN"])
