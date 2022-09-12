import markov
import random
import discord
import time
import datetime
import os

RANDOM_MESSAGE_INTERVAL = 50
LEARNING_CHANNELS = [] #[{'guild': GUILD_ID_HERE, 'channel': CHANNEL_ID_HERE}]
FAST_MODE_CHANNELS = []
SNAIL_MODE = False
SLOW_MODE_COOLDOWN = datetime.timedelta(minutes=1)

ERROR_EMOJI = ["🖕", "😴", "🧐", "🤓"]
FEEDBACK_EMOJI = ["🫶", "🤝", "👌", "👍"]
COOLDOWN_EMOJI = ["⌛", "⏳", "🤫", "🤐", "🙊"]
CONFUSED_EMOJI = ["🤯", "👁️", "🫵"]

#dont edit below
nonsense = markov.init(4)
message_counts = {}
learning_channels = []
bot_mention = ""
slow_mode_cooldowns = {}

async def initialize(client):
    global learning_channels, bot_mention

    for ids in LEARNING_CHANNELS:
        learning_channels += [client.get_guild(ids['guild']).get_channel(ids['channel'])]
    bot_mention = f"<@{client.user.id}>"

    await fetch_history(client) 

async def fetch_history(client):
    for channel in learning_channels:
        history = await channel.history(limit=1000).flatten()
        for m in history:
            if m.author != client.user:
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

    #ignore huge messages
    if len(message) > 400:
        return
    
    markov.append(nonsense, message)

async def do_random_message(request):
    if not RANDOM_MESSAGE_INTERVAL:
        return

    channel = request.channel.id

    if not channel in message_counts:
        message_counts[channel] = 0
    message_counts[channel] += 1    

    if message_counts[channel] % RANDOM_MESSAGE_INTERVAL == 0:
        await request.channel.send(content=generate_nonsense())


async def process_message(request):   
    if request.channel in learning_channels:
        add_message(request.content)
        await do_random_message(request)
        

def enforce_cooldown(author, channel, now):
    key = f"{author}{channel}"

    if SNAIL_MODE:
        key = f"{channel}"
    
    if key in slow_mode_cooldowns:
        delta = now-slow_mode_cooldowns[key]
        if delta < SLOW_MODE_COOLDOWN:
            return False
    slow_mode_cooldowns[key] = now
    return True

async def respond(request, client):
    if request.author == client.user:
        return

    will_respond = False
    if client.user in request.mentions:
        will_respond = True
    if request.reference and request.reference.resolved and request.reference.resolved.author == client.user:
        will_respond = True
    channel = request.channel.id
    if will_respond and not channel in FAST_MODE_CHANNELS:
        off_cooldown = enforce_cooldown(request.author.id, channel, request.created_at)
        if not off_cooldown:
            await request.add_reaction(random.choice(COOLDOWN_EMOJI))
        will_respond = off_cooldown

    if will_respond:
        await request.reply(generate_nonsense())

def generate_nonsense():
    out = ""
    while out == "" or markov.analysis(nonsense, out) < 0.5:
        out = markov.generate(nonsense, 2)

    return out

async def on_nonsense(request, client):
    global FAST_MODE_CHANNELS, SNAIL_MODE, ANALYSIS_MODE
    channel = request.channel.id

    command = request.content.removeprefix(".nonsense").strip().lower()
    if command == "tokens" or command == "":
        return f"tokens: {len(nonsense)}"
    elif command == "analysis":
        if not request.reference:
            await request.add_reaction(random.choice(ERROR_EMOJI))
            return

        reference = request.reference.resolved
        if not reference or type(reference) != discord.Message:
            await request.add_reaction(random.choice(ERROR_EMOJI))
            return
        
        score = markov.analysis(nonsense, reference.content)*100
        await request.reply(f"{score:.2f}%")
        return
    
    if request.author == client.user:
        await request.add_reaction(random.choice(CONFUSED_EMOJI))
        return

    if not request.author.guild_permissions.manage_roles:
        await request.add_reaction(random.choice(ERROR_EMOJI))
        return

    if command == "fast":
        SNAIL_MODE = False
        if not channel in FAST_MODE_CHANNELS:
            FAST_MODE_CHANNELS += [channel]
        await request.add_reaction(random.choice(FEEDBACK_EMOJI))
    elif command == "slow":
        SNAIL_MODE = False
        if channel in FAST_MODE_CHANNELS:
            FAST_MODE_CHANNELS = [c for c in FAST_MODE_CHANNELS if c != channel]
        await request.add_reaction(random.choice(FEEDBACK_EMOJI))
    elif command == "snail":
        SNAIL_MODE = True
        await request.add_reaction(random.choice(FEEDBACK_EMOJI))
    elif command.startswith("purge"):
        token = command.removeprefix("purge").strip()
        markov.delete(nonsense, token)
        await request.add_reaction(random.choice(FEEDBACK_EMOJI))

if os.path.isfile("forced.txt"):
    text = ""
    with open("forced.txt") as f:
        text = f.read()
    markov.process(nonsense, text.split('\n'))