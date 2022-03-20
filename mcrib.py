import discord
import wc
import qahirah as cairo
from qahirah import CAIRO as CAIRO
import io
from urllib import request
import random

def resolve_mcrib():
    url = "https://cdn.discordapp.com/attachments/869468815283605524/954586510848561273/unknown.png"
    try:
        req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = request.urlopen(req).read()

        return wc.png_to_surface(data)
    except Exception:
        return wc.png_to_surface(None)

async def on_mcrib(request):
    mcrib = resolve_mcrib()

    mccairo = cairo.Context.create(mcrib)

    mccairo.move_to((216, 178))#(236,217))

    mcname = request.author.name
    if request.author.nick:
        mcname = request.author.nick

    wc.lib.path_text(mccairo._cairobj, mcname.encode('utf-8'), 24, "Impact".encode('utf-8'))
    
    mccairo.source_colour = (1.0, 1.0, 1.0)
    mccairo.fill_preserve()
    mccairo.source_colour = (0.0, 0.0, 0.0)
    mccairo.set_line_width(1.2)
    mccairo.stroke()

    mcbuf = io.BytesIO()
    mcrib.write_to_png_file(mcbuf)
    mcbuf.seek(0)

    await request.reply(content=generate_mcrib_sentance(), file=discord.File(mcbuf, filename="mc(you).png"))

    return None

def markov_process(path):
    p = {}

    body = ""
    with open(path) as f:
        body = f.read()

    lines = body.split('\n')

    for l in lines:
        if not "^" in p:
            p["^"] = []
        words = l.split()

        if len(words) == 0:
            continue

        p["^"].append(words[0])

        for i in range(1, len(words)):
            last = words[i-1]
            key = last.lower()
            this = words[i]

            if not key in p:
                p[key] = []
            
            p[key].append(this.strip())

        last = words[-1].lower()
        if not last in p:
            p[last] = []
        
        p[last].append("$")
    return p

def valid_mcrib_sentance(sentance):
    if "rib" in sentance.lower():
        return True

def generate_mcrib_sentance():
    p = transcript

    out = ""

    while not valid_mcrib_sentance(out):
        current = "^"
        out = ""
        while True:
            if not current.lower() in p:
                break
            current = random.choice(p[current.lower()])

            if current == "$":
                break

            if current in "!,?.":
                out = out[:-1]

            out += current + " "
            
    return out

transcript = markov_process("mcrib.txt")