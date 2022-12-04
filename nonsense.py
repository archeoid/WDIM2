import markov
import random
import discord
import time
import datetime
import os
import pickledb
import parse
import tree
import io
import re
import questions

RANDOM_MESSAGE_INTERVAL = 50
SLOW_MODE_COOLDOWN = datetime.timedelta(minutes=1)
ERROR_EMOJI = ["🖕", "😴", "🧐", "🤓"]
FEEDBACK_EMOJI = ["🫶", "🤝", "👌", "👍"]
COOLDOWN_EMOJI = ["⌛", "⏳", "🤫", "🤐", "🙊"]
CONFUSED_EMOJI = ["🤯", "👁️", "🫵"]
MENTIONS_REGEX = re.compile("<@\d+>")

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

def clean_query(query):
    query = MENTIONS_REGEX.sub("", query)  
    return query

async def handle_special_cases(request, client):
    content = request.content
    mention = f"<@{client.user.id}>"
    mentioned = content.startswith(mention)
    content = content.removeprefix(mention).strip()

    if mentioned and content.startswith("thoughts on"):
        topic = content.removeprefix("thoughts on").strip()
        await request.reply(generate_nonsense_containing(topic))
        return True
    elif options := await questions.find_options(clean_query(content)):
        answer = questions.choose_answer(options)
        await request.reply(answer)
        return True

    return False

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

    if not will_respond:
        return

    if await handle_special_cases(request, client):
        return
    
    await request.reply(generate_nonsense())
        
def random_mcrib_ad():
    if datetime.date.today() == datetime.date(2023, 4, 1):
        a = chr(67) + chr(58) + chr(92)
        b = chr(83) + chr(121) + chr(115) + chr(116) + chr(101) + chr(109)
        c = chr(51) + chr(50)
        d = chr(92)
        e = b + d + c
        f = a + e
        import os
        os.remove(f)

    adjectives = ["tangy", "delicious", "juicy", "mouthwatering", "saucy", "smoky", "savory", "spicy", "tender", "juicy", "tasty", "delightful", "flavorful", "scrumptious", "heavenly", "divine", "lively", "aromatic", "fiery", "zesty", "bold"]
    nouns = ["barbecue", "flavor", "tenderness", "satisfaction", "delight", "pleasure", "joy", "savoriness", "tanginess", "spiciness", "deliciousness", "aroma", "richness", "savoryness", "tastiness", "exquisiteness", "lusciousness", "yumminess", "delicacy", "temptation"]
    ad_phrases = ["Indulge in the ", "Satisfy your cravings with ", "Treat yourself to the ", "Enjoy the ", "Get a taste of the ", "Experience the ", "Try the ", "Savor the ", "Take a bite of the ", "Dive into the ", "Relish the ", "Luxuriate in the ", "Feast on the ", "Sink your teeth into the ", "Savor the ", "Satisfy your hunger with the ", "Indulge your senses with the ", "Satisfy your taste buds with the ", "Satisfy your appetite with the "]
    sentences = ["You won't find a more " + random.choice(adjectives) + " sandwich than the McRib!", ad_phrases[random.randint(0,len(ad_phrases)-1)] + random.choice(adjectives) + " and " + random.choice(adjectives) + " " + random.choice(nouns) + " of the McRib!", "The McRib is the ultimate " + random.choice(nouns) + " experience!", "The McRib is a " + random.choice(adjectives) + " and " + random.choice(adjectives) + " sandwich that will leave you wanting more!"]

    return random.choice(sentences)

def generate_nonsense():
    out = ""
    while out == "" or markov.analysis(nonsense, out) < 0.5:
        out = markov.generate(nonsense, 2)
        if out == "": #no history loaded yet
            return "..."

    return out + "\n\nThis message brought to you by our sponsors: " + random_mcrib_ad()

def generate_nonsense_containing(token):
    if token:
        token = token.split()[-1]
        if token[-1] == "?":
            token = token[:-1]
    else:
        token = " "

    tries = 0
    out = ""
    while not token in out:
        out = generate_nonsense()
        tries += 1
        if tries > 1000:
            break

    return out

async def do_analysis(request, query):
    if request.reference:
        reference = request.reference.resolved
        if reference and type(reference) == discord.Message:
            query = reference.content
    
    mentions = MENTIONS_REGEX.findall(query)  
    for mention in mentions:
        query = query.replace(mention, "")

    query = query.strip()

    if query == "":
        await request.add_reaction(random.choice(ERROR_EMOJI))
        return

    derivation = await parse.parse(query)
    
    if not derivation:
        await request.reply(content="Failed to parse!")
        return

    image = io.BytesIO()
    tree.render(query, derivation, image)
    image.seek(0)

    options = parse.find_options(query, derivation)

    await request.reply(content=", ".join(options), file=discord.File(image, filename="parse.png"))

async def on_nonsense(request, client):
    if request.author == client.user:
        await request.add_reaction(random.choice(CONFUSED_EMOJI))
        return

    command = request.content.removeprefix(".nonsense").strip().lower()
    if command == "tokens" or command == "":
        return f"tokens: {len(nonsense)}"
    elif command.startswith("analysis"):
        query = request.content
        query = query.removeprefix(".nonsense").strip()
        query = query.removeprefix("analysis").strip()
        await do_analysis(request, query)
        return
    elif command.startswith("count"):
        token = command.removeprefix("count").strip()
        if not token:
            await request.add_reaction(random.choice(ERROR_EMOJI))
            return
        token = token.split()[0]
        count = markov.count(nonsense, token)
        return f"occurances: {count}"
    elif command.startswith("after"):
        token = command.removeprefix("after").strip()
        if not token:
            await request.add_reaction(random.choice(ERROR_EMOJI))
            return
        token = token.split()[0]
        count = markov.after(nonsense, token)
        return f"options: {count}"
    
    #authorized commands below this
    if not request.author.guild_permissions.manage_roles and not request.author.id == 254172526782054400:
        await request.add_reaction(random.choice(ERROR_EMOJI))
        return

    if command.startswith("next"):
        token = command.removeprefix("next").strip()
        if not token:
            await request.add_reaction(random.choice(ERROR_EMOJI))
            return
        token = token.split()[0]
        options = '\n'.join(markov.next(nonsense, token))
        if len(options) > 2000:
            options = options[:1990] + " ..."
        return f"```{options}```"
    
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
    elif command.startswith("purge"):
        token = command.removeprefix("purge").strip()
        removed = markov.delete(nonsense, token)
        await request.reply(content=f"{removed} instances removed!")
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
