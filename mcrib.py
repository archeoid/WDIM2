import discord
import wc
import qahirah as cairo
from qahirah import CAIRO as CAIRO
import io
from urllib import request
import markov

mctext = ""
with open("mcrib.txt") as f:
    mctext = f.read()

transcript = markov.process(mctext.split('\n'))

def fetch_mcrib_image():
    url = "https://cdn.discordapp.com/attachments/869468815283605524/954586510848561273/unknown.png"
    try:
        req = request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        data = request.urlopen(req).read()

        return wc.png_to_surface(data)
    except Exception:
        return wc.png_to_surface(None)

async def on_mcrib(request):
    mcrib = fetch_mcrib_image()

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

def generate_mcrib_sentance():
    out = ""
    while not "rib" in out.lower():
        out = markov.generate(transcript)
 
    return out