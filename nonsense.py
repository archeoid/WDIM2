import markov
import random
import discord
import time
import datetime
import os
import pickledb

RANDOM_MESSAGE_INTERVAL = 50
SLOW_MODE_COOLDOWN = datetime.timedelta(minutes=1)
ERROR_EMOJI = ["🖕", "😴", "🧐", "🤓"]
FEEDBACK_EMOJI = ["🫶", "🤝", "👌", "👍"]
COOLDOWN_EMOJI = ["⌛", "⏳", "🤫", "🤐", "🙊"]
CONFUSED_EMOJI = ["🤯", "👁️", "🫵"]

#dont edit below
nonsense = markov.init(4)
channels = {"learning":[], "fast":[]}
cooldowns = {}
db = pickledb.load('nonsense.db', False)
random_message_counts = {}
bot_mention = ""

async def initialize(client):
    global bot_mention

    if not db.get("learning"):
        db.lcreate("learning")
    if not db.get("fast"):
        db.lcreate("fast")
    if not db.get("snail"):
        db.set("snail", False)
    db.dump()
    
    learning = db.lgetall("learning")
    for ids in learning:
        channels["learning"] += [client.get_guild(ids['guild']).get_channel(ids['channel'])]

    fast = db.lgetall("fast")
    for ids in fast:
        channels["fast"] += [client.get_guild(ids['guild']).get_channel(ids['channel'])]

    bot_mention = f"<@{client.user.id}>"

    await fetch_history(client) 

async def fetch_history(client):
    for channel in channels["learning"]:
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

    if not channel in random_message_counts:
        random_message_counts[channel] = 0
    random_message_counts[channel] += 1    

    if random_message_counts[channel] % RANDOM_MESSAGE_INTERVAL == 0:
        await request.channel.send(content=generate_nonsense())


async def process_message(request):   
    if request.channel in channels["learning"]:
        add_message(request.content)
        await do_random_message(request)

def enforce_cooldown(author, channel, now):
    key = f"{author}{channel}"

    if db.get("snail"):
        key = f"{channel}"
    
    if key in cooldowns:
        delta = now-cooldowns[key]
        if delta < SLOW_MODE_COOLDOWN:
            return False
    cooldowns[key] = now
    return True

async def respond(request, client):
    if request.author == client.user:
        return

    will_respond = False
    if client.user in request.mentions:
        will_respond = True
    if request.reference and request.reference.resolved and request.reference.resolved.author == client.user:
        will_respond = True
    if will_respond and not request.channel in channels["fast"]:
        off_cooldown = enforce_cooldown(request.author.id, request.channel.id, request.created_at)
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
    if request.author == client.user:
        await request.add_reaction(random.choice(CONFUSED_EMOJI))
        return

    command = request.content.removeprefix(".nonsense").strip().lower()
    if command == "tokens" or command == "":
        return f"tokens: {len(nonsense)}"
    
    #authorized commands below this
    if not request.author.guild_permissions.manage_roles:
        await request.add_reaction(random.choice(ERROR_EMOJI))
        return
    
    if command == "fast":
        set_channel(request, "fast", True)
    elif command == "slow":
        set_channel(request, "fast", False)
    elif command == "enable":
        set_channel(request, "learning", True)
    elif command == "disable":
        set_channel(request, "learning", False)
    elif command == "snail":
        db.set("snail", not db.get("snail"))
        db.dump()
        if db.get("snail"):
            await request.add_reaction('🐌')
        else:
            await request.add_reaction('🐇')
    else:
        await request.add_reaction(random.choice(ERROR_EMOJI))
        return
    await request.add_reaction(random.choice(FEEDBACK_EMOJI))

def set_channel(request, name, active):
    global channels
    this = {'guild': request.guild.id, 'channel': request.channel.id}
    values = db.lgetall(name)
    if active and not this in values:
        db.ladd(name, this)
        channels[name] += [request.channel]
    if not active and this in values:
        db.lpop(name, values.index(this))
        channels[name].remove(request.channel)
    db.dump()

if os.path.isfile("forced.txt"):
    text = ""
    with open("forced.txt") as f:
        text = f.read()
    markov.process(nonsense, text.split('\n'))