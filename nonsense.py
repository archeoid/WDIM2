import markov
import random
import discord

nonsense = {}
message_count = 0
random_message_interval = 50

allowed_channels_ids = [] #[{'guild': GUILD_ID_HERE, 'channel': CHANNEL_ID_HERE}]
allowed_channels = []
bot_mention = ""

async def initialize(client):
    global allowed_channels, bot_mention

    for ids in allowed_channels_ids:
        allowed_channels += [client.get_guild(ids['guild']).get_channel(ids['channel'])]
    bot_mention = f"<@{client.user.id}>"

    await fetch_history(client) 

async def fetch_history(client):
    for channel in allowed_channels:
        history = await channel.history(limit=1000).flatten()
        for m in history:
            if m.author == client.user:
                continue
            add_message(m.content)
    print('History added')

def add_message(message):
    #remove mentions of this bot
    message = message.replace(bot_mention, "")

    if not message:
        return

    #ignore mass mentions
    if message.count("<@") > 2:
        return
    
    markov.append(nonsense, message)

    #boost probablity of sending url's
    if 'http' in message:
        for i in range(2):
            markov.append(nonsense, message)

async def process_message(request):
    global message_count
    
    if request.channel in allowed_channels:
        add_message(request.content)

        message_count += 1
        if random_message_interval and message_count % random_message_interval == 0:
            channel = random.choice(allowed_channels)
            await channel.send(content=generate_nonsense())

def should_respond(request, client):
    if client.user in request.mentions:
        return True
    if request.reference and request.reference.resolved and request.reference.resolved.author == client.user:
        return True
    return False

def generate_nonsense():
    out = ""
    while out == "":
        out = markov.generate(nonsense)
 
    return out

async def send_status(request):
    await request.reply(f"tokens: {len(nonsense)}")