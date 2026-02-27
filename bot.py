import discord
import os
import time
import random
import asyncio
from datetime import datetime

PXGHOUL_ID = 1278727608065986685

COOLDOWN_SECONDS = 60
MAX_PINGS = 3
WEBHOOK_REPLY_CHANCE = 0.45

ANNOY_DECAY_SECONDS = 180  # annoyance decays every 3 minutes

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

# annoyance tracking
annoyance = {}          # user_id -> score
last_annoy_time = {}    # user_id -> timestamp

RESPONSES = {
    "chill": {
        "offline": ["Diego is offline right now."],
        "online": ["He’ll respond when he can."],
        "dnd": ["Diego is busy right now."]
    }
}

# ---------- FAKE‑ME BRAINS ----------

NONCHALANT = [
    "ok",
    "aight",
    "bet",
    "works for me",
    "looks fine",
    "later"
]

SASSY = [
    "scroll up",
    "check pins",
    "already answered",
    "same as before",
    "nothing changed"
]

MAD = [
    "stop spamming",
    "asked already",
    "not broken",
    "read",
    "no"
]

KEYWORDS = [
    "broken", "bug", "error", "issue",
    "when", "eta", "update",
    "fix", "help", "how", "why", "script"
]

def should_fakeme_reply(message):
    c = message.content.lower()

    if "?" in c:
        return True

    if any(w in c for w in KEYWORDS):
        return True

    if PXGHOUL_ID in [u.id for u in message.mentions]:
        return True

    return False


def get_annoyance_level(user_id):
    now = time.time()
    last = last_annoy_time.get(user_id, now)

    # decay annoyance over time
    decay = int((now - last) // ANNOY_DECAY_SECONDS)
    if decay > 0:
        annoyance[user_id] = max(0, annoyance.get(user_id, 0) - decay)
        last_annoy_time[user_id] = now

    score = annoyance.get(user_id, 0)

    if score >= 6:
        return "mad"
    elif score >= 3:
        return "sass"
    return "chill"


def get_fake_reply(user_id):
    level = get_annoyance_level(user_id)

    if level == "mad":
        return random.choice(MAD)
    if level == "sass":
        return random.choice(SASSY)
    return random.choice(NONCHALANT)

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
    global ghost_mode, fake_me_enabled, last_impersonated_user

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

    member = message.guild.get_member(PXGHOUL_ID)
    if not member:
        return

    status = member.status.name.lower()

    # ---- GHOST MODE ----
    if ghost_mode and PXGHOUL_ID in [u.id for u in message.mentions]:
        await member.send(
            f"👻 Ghost ping from **{message.author}** in #{message.channel}\n"
            f"{message.content}"
        )
        return

# ---- FAKE‑ME GLOBAL ----
if fake_me_enabled and status != "dnd" and should_fakeme_reply(message):
    uid = message.author.id

    # calculate dynamic chance (more annoying = more replies)
    chance = min(0.15 + (annoyance.get(uid, 0) * 0.10), 0.85)

    if random.random() < chance:
        annoyance[uid] = annoyance.get(uid, 0) + 1
        last_annoy_time[uid] = time.time()

        reply = get_fake_reply(uid)
        await send_as_pxghoul(message, reply)
        return

    # ---- NORMAL BOT RESPONSE (only when pinged) ----
    if PXGHOUL_ID in [u.id for u in message.mentions]:
        pool = RESPONSES["chill"].get(status, ["He’ll respond when he can."])
        response = random.choice(pool)

        if status == "offline" and last_online_time:
            mins = int((datetime.utcnow() - last_online_time).total_seconds() // 60)
            response += f"\n(Last online {mins}m ago)"

        await message.reply(response)

client.run(os.environ["DISCORD_TOKEN"])

