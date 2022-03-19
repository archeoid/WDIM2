import discord
import wc
import qahirah as cairo
from qahirah import CAIRO as CAIRO
import io
from urllib import request

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

    mcft = cairo.get_ft_lib()
    mcface = mcft.new_face("Impact.ttf")
    mcface.set_char_size(size=10, resolution=10)
    mcfont = cairo.FontFace.create_for_ft_face(mcface)

    mccairo.set_font_face(mcfont)
    mccairo.set_font_size(24)

    mccairo.move_to((216, 196))#(236,217))

    mcname = request.author.name
    if request.author.nick:
        mcname = request.author.nick
    
    mccairo.text_path(mcname)
    mccairo.source_colour = (1.0, 1.0, 1.0)
    mccairo.fill_preserve()
    mccairo.source_colour = (0.0, 0.0, 0.0)
    mccairo.set_line_width(1.2)
    mccairo.stroke()

    mcbuf = io.BytesIO()
    mcrib.write_to_png_file(mcbuf)
    mcbuf.seek(0)

    await request.reply(file=discord.File(mcbuf, filename="mc(you).png"))

    return None