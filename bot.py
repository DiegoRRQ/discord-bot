import discord
import os

intents = discord.Intents.default()
intents.message_content = True  # needed to read messages

client = discord.Client(intents=intents)

# --- Your trigger words and responses ---
KEY_TRIGGERS = ["key", "keys"]  # case-insensitive check below
KEY_RESPONSE = "All the keys for Diego's scripts can be found in https://discord.com/channels/1458595915463000147/1459979110481793188"

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author == client.user:
        return  # ignore the bot's own messages

    msg = message.content.lower()

    # Check if any trigger word appears in the message
    if any(word in msg.split() for word in KEY_TRIGGERS):
        await message.channel.send(KEY_RESPONSE)

client.run(os.environ["DISCORD_TOKEN"])
```

**`requirements.txt`**
```
discord.py
