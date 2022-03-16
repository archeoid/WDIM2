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
MAX_DELTA = 7*24*60*60
FILTERED_WORDS = ["","below","i'd","could","been","out","you'll","am","both","can't","where's","you've","ours","own","not","for","its","me","r","isn't","i'll","all","can","www","shouldn't","after","ought","herself","very","and","than","we'll","our","what's","against","being","when's","under","wouldn't","let's","of","over","to","like","her","yours","in","just","each","the","your","itself","she","couldn't","too","by","this","it","my","com","ever","few","hers","i've","shall","how's","did","there","you","with","so","otherwise","yourself","same","such","yourselves","whom","here","themselves","have","while","who's","during","myself","only","that","why's","is","that's","these","he'll","his","cannot","he'd","from","further","mustn't","before","we'd","he","they'll","do","them","aren't","their","we","they","http","hadn't","ourselves","why","would","other","haven't","she'll","was","didn't","has","they'd","had","more","doesn't","but","also","she's","those","hence","having","you're","as","were","she'd","down","here's","again","doing","who","him","it's","i","we're","hasn't","they've","through","into","since","where","a","does","if","k","what","else","above","himself","weren't","when","any","be","should","theirs","no","he's","then","up","won't","most","they're","we've","are","off","shan't","an","get","until","because","however","which","therefore","or","about","you'd","once","nor","some","don't","between","at","there's","i'm","wasn't","how","on","oh","yeah","stuff","well","still","make","ok","on"]

def resolve_discord_emoji(d):
    file = f"{d}.png"

    url = f"https://cdn.discordapp.com/emojis/{file}"
    try:
        req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = request.urlopen(req).read()
        #hash = hashlib.md5(data).hexdigest()

        return wc.png_to_surface(data)
    except Exception:
        return wc.png_to_surface(None)

def tokenize(message):
    message = message.lower()

    unicode_emojis = [m for m in UNICODE_EMOJI_REGEX.findall(message)]
    discord_emojis = [int(m) for m in DISCORD_EMOJI_REGEX.findall(message)]

    message = UNICODE_EMOJI_REGEX.sub(' ', message)
    message = DISCORD_REGEX.sub(' ', message)
    message = URL_REGEX.sub(' ', message)

    message = message.translate(PUNC_TRANSLATE)

    words = SPLIT_REGEX.split(message)

    return words + unicode_emojis + discord_emojis

def get_frequencies(tokens):
    #filter words
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

async def on_wdim(request, client):
    parameters = request.content.removeprefix('.wdim')

    #whether to get only get messages up to the last message by author
    stop_on_author = parameters == ""

    timedelta, error = parse_time(parameters)
    if error:
        return error

    timestamp = request.created_at-timedelta

    tokens = []
    async for m in request.channel.history(limit=None, after=timestamp):
        if m.author.id == client.user.id: #ignore our messages
            continue
        if m.content.startswith('.wdim'): #ignore request messages
            continue
        if stop_on_author and m.author.id == request.author.id:
            break
        tokens += tokenize(m.content)

    error = await do_wordcloud(request, tokens)
    return error

def parse_time(time_string):
    if not time_string:
        return datetime.timedelta(days=7), None

    delta = 0
    try:
        delta = int(time_string[:-1])
    except ValueError:
        return None, "Invalid time duration"
    unit = time_string[-1].lower()
    if unit == "d":
        delta *= 86400
    elif unit == "h":
        delta *= 3600
    elif unit == "m":
        delta *= 60
    else:
        return None, "Invalid time unit"

    if delta > MAX_DELTA:
        return None, "Invalid time duration"

    return datetime.timedelta(seconds=delta), None

async def do_wordcloud(request, tokens):
    tokens = get_frequencies(tokens)

    if len(tokens) == 0:
        return "You're all caught up!"

    for i in range(len(tokens)):
        if type(tokens[i]) == int:
            tokens[i] = resolve_discord_emoji(tokens[i])

    wordcloud = wc.WordCloud(1200, 600, "WhitneyMedium.ttf", "TwemojiMozilla.ttf")
    wordcloud.add_data(tokens)
    wordcloud.compute()
    image = wordcloud.write()

    await request.channel.send(file=discord.File(image, filename="wordcloud.png"))
    return None