import discord
import os
import time
import random
import asyncio
from datetime import datetime

PXGHOUL_ID = 1278727608065986685
COOLDOWN_SECONDS = 60
MAX_PINGS = 3

WEBHOOK_REPLY_CHANCE = 0.40

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

ghost_mode = False
current_mood = "chill"
last_online_time = None
last_impersonated_user = None
fake_me_enabled = False

RESPONSES = {
    "chill": {
        "offline": ["Diego is offline right now."],
        "online": ["He’ll respond when he can."],
        "dnd": ["Diego is busy right now."]
    },
    "busy": {
        "offline": ["Diego is offline."],
        "online": ["Diego is busy."],
        "dnd": ["Do not ping again."]
    },
    "menace": {
        "offline": ["He’s offline. Don’t wait up."],
        "online": ["He saw it."],
        "dnd": ["Stop pinging."]
    }
}

# ---------- NONCHALANT BRAIN ----------

def get_nonchalant_reply(content):
    c = content.lower()

    if any(w in c for w in ["broken", "bug", "error", "issue"]):
        return random.choice([
            "works for me",
            "probably user error",
            "looks fine"
        ])

    if any(w in c for w in ["when", "eta", "soon", "update"]):
        return random.choice([
            "later",
            "eventually",
            "when i get to it"
        ])

    if any(w in c for w in ["help", "how", "fix"]):
        return random.choice([
            "check pins",
            "read above",
            "scroll up"
        ])

    if any(w in c for w in ["you there", "hello", "yo", "ping"]):
        return random.choice([
            "yeah",
            "sup",
            "chill"
        ])

    return random.choice(["ok", "aight", "bet"])

# ---------- WEBHOOK HELPERS ----------

async def get_or_create_webhook(channel):
    webhooks = await channel.webhooks()
    for webhook in webhooks:
        if webhook.name == "pxghoul-ghost":
            return webhook
    return await channel.create_webhook(name="pxghoul-ghost")


async def fake_typing_delay(channel):
    async with channel.typing():
        await asyncio.sleep(random.uniform(2.0, 6.0))


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
    global ghost_mode, current_mood, last_impersonated_user, fake_me_enabled

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

        if msg == "!fakeme on":
            fake_me_enabled = True
            await message.reply("😈 Fake‑you mode **ON**.")
            return

        if msg == "!fakeme off":
            fake_me_enabled = False
            await message.reply("😴 Fake‑you mode **OFF**.")
            return

        if msg == "!fakeme status":
            state = "ON" if fake_me_enabled else "OFF"
            await message.reply(f"🧍‍♂️ Fake‑you mode is **{state}**.")
            return

    # ---- KEY HANDLER ----
    if any(word in msg.split() for word in KEY_TRIGGERS):
        await message.reply(KEY_RESPONSE)
        return

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
        status = member.status.name.lower()

        # ---- GHOST MODE ----
        if ghost_mode:
            await member.send(
                f"👻 Ghost ping from **{message.author}** in #{message.channel}\n"
                f"{message.content}"
            )
            return

        # ---- FAKE‑ME WEBHOOK ----
        if (
            fake_me_enabled
            and status != "dnd"
            and random.random() < WEBHOOK_REPLY_CHANCE
            and message.author.id != last_impersonated_user
        ):
            reply = get_nonchalant_reply(message.content)
            await send_as_pxghoul(message, reply)
            last_impersonated_user = message.author.id
            return

        # ---- NORMAL BOT RESPONSE ----
        pool = RESPONSES[current_mood].get(status, RESPONSES[current_mood]["online"])
        response = random.choice(pool)

        if status == "offline" and last_online_time:
            mins = int((datetime.utcnow() - last_online_time).total_seconds() // 60)
            response += f"\n(Last online {mins}m ago)"

        await message.reply(response)

client.run(os.environ["DISCORD_TOKEN"])
