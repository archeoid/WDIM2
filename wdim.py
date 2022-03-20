import discord
import wc
import string
import emoji
import re
import datetime
from urllib import request

from tokenization import unigrams_and_bigrams

UNICODE_EMOJI_REGEX = emoji.get_emoji_regexp()
DISCORD_EMOJI_REGEX = re.compile("<:[^:]+:(\d+)>")
DISCORD_REGEX = re.compile("<[^>]+>")
URL_REGEX = re.compile("(http://|https://|www\.)[^\s]+")
SPLIT_REGEX = re.compile('|'.join(map(re.escape, [c for c in string.whitespace])))
PUNC_TRANSLATE = str.maketrans('', '', string.punctuation)
FILTERED_WORDS = ["", "below","id","could","been","out","youll","am","both","cant","wheres","youve","ours","own","not","for","its","me","r","isnt","ill","all","can","www","shouldnt","after","ought","herself","very","and","than","well","our","whats","against","being","whens","under","wouldnt","lets","of","over","to","like","her","yours","in","just","each","the","your","itself","she","couldnt","too","by","this","it","my","com","ever","few","hers","ive","shall","hows","did","there","you","with","so","otherwise","yourself","same","such","yourselves","whom","here","themselves","have","while","whos","during","myself","only","that","whys","is","thats","these","hell","his","cannot","hed","from","further","mustnt","before","wed","he","theyll","do","them","arent","their","we","they","http","hadnt","ourselves","why","would","other","havent","shell","was","didnt","has","theyd","had","more","doesnt","but","also","shes","those","hence","having","youre","as","were","shed","down","heres","again","doing","who","him","its","i","were","hasnt","theyve","through","into","since","where","a","does","if","k","what","else","above","himself","werent","when","any","be","should","theirs","no","hes","then","up","wont","most","theyre","weve","are","off","shant","an","get","until","because","however","which","therefore","or","about","youd","once","nor","some","dont","between","at","theres","im","wasnt","how","on","oh","yeah","stuff","well","still","make","ok","on"]

cooldowns = {}
COOLDOWN = datetime.timedelta(minutes=5)
MAXTIME = datetime.timedelta(days=7)
OVERLOOK = datetime.timedelta(minutes=3)

async def on_wdim(request, client):
    parameters = request.content.removeprefix('.wdim')
    parameters = parameters.removeprefix('.wc').strip()

    now = request.created_at
    author = request.author.id
    channel = request.channel.id

    #parse the time parameters, defaults to MAXTIME if no parameters
    delta, error = parse_time(parameters)
    if error:
        return error

    #enforce a cooldown, specific to each user and channel
    error = enforce_cooldown(author, channel, now)
    if error:
        return error

    tokens = []
    count = 0
    async for m in request.channel.history(limit=None, after=now-delta, oldest_first=False):
        if m.author.id == client.user.id: #ignore our messages
            continue
        if m.content.startswith('.'): #ignore request messages
            continue
        #break on authors messages if in wdim mode (no time parameters)
        #except if it was posted in the last OVERLOOK time
        if not parameters and m.author.id == author:
            if now-m.created_at < OVERLOOK:
                continue
            else:
                #stoping here, update delta for the message
                delta = now-m.created_at
                break
        count += 1
        tokens += tokenize(m.content)

    #turn the tokens into a list of words/emoji ID's, most frequent first
    data = parse_tokens(tokens)
    if len(data) == 0:
        return "You're all caught up!"

    message = f"There were {count} messages in the last {stringify_time(delta)}!"

    async with request.channel.typing():
        await do_wordcloud(request, data, message)
    return None

async def do_wordcloud(request, data, message):
    #resolve the emoji IDs into image surfaces for wc.py
    for i in range(len(data)):
        if type(data[i]) == int:
            data[i] = resolve_discord_emoji(data[i])

    wordcloud = wc.WordCloud(1200, 600, "Whitney", "TwemojiMozilla.ttf")

    wordcloud.add_data(data)

    wordcloud.compute()
    image = wordcloud.write()

    await request.reply(content=message, file=discord.File(image, filename="wordcloud.png"))


def parse_time(time_string):
    #turn time string into a time delta
    if not time_string:
        return MAXTIME, None

    error = "Invalid time duration"
    delta = 0
    try:
        delta = int(time_string[:-1])
    except Exception:
        return None, error
    if delta <= 0:
        return None, error
    unit = time_string[-1].lower()
    if unit == "d":
        delta *= 86400
    elif unit == "h":
        delta *= 3600
    elif unit == "m":
        delta *= 60
    else:
        return None, "Invalid time unit"

    try:
        delta = datetime.timedelta(seconds=delta)
    except Exception:
        return None, error

    if delta > MAXTIME:
        return None, error

    return delta, None

def stringify_time(delta):
    #turn time delta into a time string

    x = int(delta.total_seconds())

    plural = lambda s: "" if s == 1 else "s"

    if x < 60:
        return f"{x} second{plural(x)}"
    x = int(x/60)

    if x < 60:
        return f"{x} minute{plural(x)}"
    x = int(x/60)

    if x < 24:
        return f"{x} hour{plural(x)}"
    x = int(x/24)

    return f"{x} day{plural(x)}"

def resolve_discord_emoji(d):
    file = f"{d}.png"

    url = f"https://cdn.discordapp.com/emojis/{file}"
    try:
        req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = request.urlopen(req).read()

        return wc.png_to_surface(data)
    except Exception:
        return wc.png_to_surface(None)

def tokenize(message):
    message = message.lower()

    #extract emojis from message
    unicode_emojis = [m for m in UNICODE_EMOJI_REGEX.findall(message)]
    discord_emojis = [int(m) for m in DISCORD_EMOJI_REGEX.findall(message)]

    #remove emojis + urls from message
    message = UNICODE_EMOJI_REGEX.sub(' ', message)
    message = DISCORD_REGEX.sub(' ', message)
    message = URL_REGEX.sub(' ', message)

    #remove punctuation from message
    message = message.translate(PUNC_TRANSLATE)

    #split message into words
    words = SPLIT_REGEX.split(message)

    #remove 1 letter words
    words = [w for w in words if len(w) > 1]
    
    #return words and emojis
    return words + unicode_emojis + discord_emojis

def parse_tokens(tokens):
    #filter/process words using gigabrain code (see tokenization.py)
    occurances = unigrams_and_bigrams([t for t in tokens if type(t) == str], FILTERED_WORDS)

    #add emoji's
    for t in [t for t in tokens if type(t) == int]:
        if t in occurances:
            occurances[t] += 1
        else:
            occurances[t] = 1

    #sort and order, most frequent first
    occurances = dict(sorted(occurances.items(), key=lambda item: item[1]))
    occurances = list(occurances.keys())[::-1]

    return occurances

def enforce_cooldown(author, channel, now):
    key = f"{author}{channel}"
    if key in cooldowns:
        delta = now-cooldowns[key]
        if delta < COOLDOWN:
            remaining = COOLDOWN-delta
            return f"Cool it champ! Wait another {stringify_time(remaining)}."
    cooldowns[key] = now
    return None

def initialize():
    wc.load_font("WhitneyMedium.ttf")
    wc.load_font("Impact.ttf")