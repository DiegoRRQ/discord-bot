import discord
import os

PXGHOUL_ID = 1278727608065986685

KEY_TRIGGERS = ["key", "keys"]
KEY_RESPONSE = (
    "All the keys for Diego's scripts can be found in "
    "https://discord.com/channels/1458595915463000147/1459979110481793188"
)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.presences = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content.lower()

    # -------- KEY / KEYS HANDLER --------
    if any(word in msg.split() for word in KEY_TRIGGERS):
        await message.reply(KEY_RESPONSE)
        await message.add_reaction("🔑")  # change emoji if you want
        return

    # -------- PXGHOUL MENTION HANDLER --------
    if PXGHOUL_ID in [user.id for user in message.mentions]:
        guild = message.guild
        if not guild:
            return

        member = guild.get_member(PXGHOUL_ID)
        if not member:
            return

        status = member.status

        if status == discord.Status.offline:
            response = "Diego is currently offline, please be patient!"
        elif status == discord.Status.dnd:
            response = (
                "Diego is currently busy, please be patient and do not @ him again."
            )
        elif status in (discord.Status.online, discord.Status.idle):
            response = "Diego will respond as soon as he can, please be patient."
        else:
            response = "Diego will respond as soon as he can, please be patient."

        await message.reply(response)

client.run(os.environ["DISCORD_TOKEN"])
