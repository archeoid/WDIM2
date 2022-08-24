import math
import qahirah as cairo
from qahirah import CAIRO as CAIRO
import harfbuzz as hb
import colorsys
import numpy as np
import matplotlib.pyplot as plt
import random
import emoji
import io
import ctypes as ct

class Extent:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

lib = ct.CDLL('./lib.so')

lib.get_space.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS'),
    ct.c_int, ct.c_int, ct.c_int, ct.c_int,
    ct.c_void_p, ct.c_void_p
]
lib.get_space.restype = ct.c_int
lib.query_location.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS'),
    ct.c_int, ct.c_int, ct.c_int, ct.c_int, ct.c_int, ct.c_int
]
lib.query_location.restype = ct.c_int
lib.perform_sum.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.uint8, ndim=2, flags='C_CONTIGUOUS'),
    ct.c_int, ct.c_int,
    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS')]
lib.path_text.argtypes = [ct.c_void_p, ct.c_char_p, ct.c_int, ct.c_char_p]
lib.get_text_extent.argtypes = [
    ct.c_void_p, ct.c_char_p, ct.c_int, ct.c_char_p,
    ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p
]
lib.load_font.argtypes = [ct.c_char_p]

class IntegralImage:
    def __init__(self, width, height):
        self.width, self.height = int(width), int(height)
        self.random = random.Random()

        self.image = None
        self.surface_data = None
        self.surface = None
        self.ctx = None
        self.reset()

    def reset(self):
        self.image = np.zeros((self.height, self.width), dtype=np.int32)
        self.surface_data = np.zeros((self.height, self.width), dtype=np.uint8)
        self.surface = cairo.ImageSurface.create_for_data(self.surface_data.ctypes.data, CAIRO.FORMAT_A8, (self.width, self.height), self.width)
        self.ctx = cairo.Context.create(self.surface)

    def get_location(self, width, height, padding) -> (int, int):
        width = int(width+2*padding)
        height = int(height+2*padding)

        if self.height <= height or self.width <= width:
            return None

        x = ct.c_int(0)
        y = ct.c_int(0)

        got = lib.get_space(self.image, self.width, self.height, width, height,
                            ct.byref(x), ct.byref(y))
        if got != 0:
            return None

        return (x.value+padding, y.value+padding)

    def query(self, x, y, w, h):
        area = lib.query_location(self.image, self.width, self.height,
            x, y, w, h)
        
        return area

    def update(self):
        lib.perform_sum(self.surface_data, self.width, self.height, self.image)

    def view(self, w, h, path="mask.png", x_p = -1, y_p = -1):
        data = np.zeros(shape=(self.height, self.width), dtype=np.uint8)
        for x in range(self.width - w):
            for y in range(self.height - h):
                if self.query(x, y, w, h) == 0:
                    data[y, x] = 255
                if x == x_p and y == y_p:
                    data[y, x] = 200
        surface = cairo.ImageSurface.create_for_data(data.ctypes.data, CAIRO.FORMAT_A8, (self.width, self.height), self.width)
        surface.write_to_png(path)

        self.surface.write_to_png("surface.png")

class WordCloud:
    def __init__(self, width, height, font_family, emoji_font):
        self.random = random.Random()
        self.width, self.height = width, height
        self.mask = IntegralImage(self.width, self.height)

        # Constants
        self.max_font_size = int(height/2)
        self.min_font_size = 4
        self.inc_font_size = 2
        self.outline = 0.03
        self.padding = 3
        self.vertical_text = True

        ft = cairo.get_ft_lib()

        self.font_family = font_family.encode('utf-8')

        emoji_face = ft.new_face(emoji_font)
        emoji_face.set_char_size(size=109, resolution=72) #for NotoColorEmoji
        self.emoji_font = cairo.FontFace.create_for_ft_face(emoji_face)
        self.hb_emoji_font = hb.Font.ft_create(emoji_face)
        self.emoji_layered = self.hb_emoji_font.face.ot_color_has_layers
        if self.emoji_layered:
            self.emoji_palette = self.hb_emoji_font.face.ot_colour_palette_get_colours(0)
            def to_rgba(c):
                return (hb.HARFBUZZ.colour_get_red(c)/255,
                hb.HARFBUZZ.colour_get_green(c)/255, 
                hb.HARFBUZZ.colour_get_blue(c)/255, 
                hb.HARFBUZZ.colour_get_alpha(c)/255)
            self.emoji_palette = [to_rgba(c) for c in self.emoji_palette]
        else:
            self.emoji_palette = None

        self.colormap = plt.cm.get_cmap("plasma")
        self.rectangles = False

        self.hue_offset = None
        self.surface = None
        self.ctx = None
        self.data = None
        self.reset()

    def reset(self):
        self.hue_offset = self.random.random()
        self.surface = cairo.ImageSurface.create(CAIRO.FORMAT_ARGB32, (self.width, self.height))
        self.ctx = cairo.Context.create(self.surface)
        self.mask.reset()

        self.ctx.source_colour = (0.2117, 0.22352, 0.247, 1)
        self.ctx.rectangle(cairo.Rect(0, 0, self.width, self.height))
        self.ctx.fill()

        self.data = []

    def add_data(self, data):
        if isinstance(data, list):
            self.data += data
        else:
            self.data += [data]

    def compute(self) -> int:
        size = self.max_font_size
        total = 0
        for d in self.data:
            while size > self.min_font_size:
                if isinstance(d, str):
                    if self.__render_word(d, size):
                        break
                elif isinstance(d, cairo.ImageSurface):
                    if self.__render_surface(d, size):
                        break
                else:
                    raise Exception(f"Unsupported data: {type(d)}")
                size -= self.inc_font_size
            else:
                break
            total += 1
        return total

    def __render_word(self, word, size):
        if emoji.is_emoji(word):
            return self.__render_emoji(word, size)

        ext = self.__get_text_extent(word, size)
        w, h = int(ext.width), int(ext.height)

        pos = self.mask.get_location(w, h, self.padding + (size * self.outline))
        if pos:
            x, y = pos
            self.__internal_render_word(x, y, ext, word, size)
            return True

        if not self.vertical_text:
            return False
        pos = self.mask.get_location(h, w, self.padding + (size * self.outline))
        if pos:
            x, y = pos
            self.__internal_render_word(x, y, ext, word, size, rotate=True)
            return True

        return False

    def __render_emoji(self, emoji, size):
        self.ctx.set_font_size(size)
        self.ctx.set_font_face(self.emoji_font)

        buf = hb.Buffer.create()
        buf.add_str(emoji)
        buf.guess_segment_properties()
        hb.shape(self.hb_emoji_font, buf)
        glyph = buf.get_glyphs()[0][0]

        subglyphs = [cairo.Glyph(glyph.index, (0,0))]
        colors = [None]

        if self.emoji_layered:
            layers = self.hb_emoji_font.face.ot_colour_glyph_get_layers(glyph.index)
            for l in layers:
                subglyphs += [cairo.Glyph(l.glyph, (0, 0))]
                colors += [l.colour_index]
        
        ext = self.ctx.glyph_extents(subglyphs)
        pos = self.mask.get_location(ext.width, ext.height, self.padding)
        if pos:
            x, y = pos
            self.__internal_render_emoji(x, y, ext, subglyphs, colors, size)
            return True

        return False

    def __render_surface(self, surface, size):
        w, h = surface.width, surface.height
        mx = max(w, h)
        sw, sh = mx / size, mx / size
        surface.set_device_scale((sw, sh))
        w, h = int(w / sw), int(h / sh)

        pos = self.mask.get_location(w, h, self.padding)
        if pos:
            x, y = pos

            for target in [self.surface, self.mask.surface]:
                ctx = cairo.Context.create(target.create_for_rectangle(cairo.Rect(x, y, w, h)))
                ctx.set_source_surface(surface, (0,0))
                ctx.paint()

            self.mask.update()

        surface.set_device_scale((1, 1))
        return pos is not None

    def __normalize_color(self, color) -> (float, float, float):
        r, g, b = color
        return r / 255.0, g / 255.0, b / 255.0

    def __get_color(self) -> ((float, float, float), (float, float, float)):
        r, g, b, _ = np.maximum(0, 255 * np.array(self.colormap(self.random.uniform(0, 1))))
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        h = (h + self.hue_offset) % 1.0
        color = self.__normalize_color(colorsys.hsv_to_rgb(h, s, v))
        v -= np.sign(v - 180.0) * 51.0
        outline = self.__normalize_color(colorsys.hsv_to_rgb(h, s, v))

        return color, outline

    def __internal_render_word(self, x, y, ext, word, size, rotate=False):
        w, h = int(ext.width), int(ext.height)
        color, outline = self.__get_color()

        if rotate:
            w, h = h, w

        for ctx in [self.ctx, self.mask.ctx]:
            if rotate:
                ctx.move_to((x, y + h))
                ctx.rotate(1.5 * math.pi)
            else:
                ctx.move_to((x, y))

            self.__text_path(ctx, word, size)

            ctx.source_colour = color
            ctx.fill_preserve()
            ctx.source_colour = outline
            ctx.set_line_width(size * self.outline)
            ctx.stroke()
            if rotate:
                ctx.rotate(0.5 * math.pi)
            if self.rectangles:
                ctx.rectangle(cairo.Rect(x, y, w, h))
                ctx.stroke()

        self.mask.update()

    def __internal_render_emoji(self, x, y, ext, subglyphs, colors, size):
        for ctx in [self.ctx, self.mask.ctx]:
            ctx.set_font_face(self.emoji_font)
            ctx.set_font_size(size)
            ctx.save()
            ctx.translate((-ext.x_bearing+x, -ext.y_bearing+y))
            for i in range(len(subglyphs)):
                if colors[i]:
                    ctx.source_colour = self.emoji_palette[colors[i]]
                else:
                    ctx.source_colour = (1,1,1,1)
                ctx.show_glyphs([subglyphs[i]])
            if self.rectangles:
                ctx.rectangle(cairo.Rect(x, y, ext.width, ext.height))
                ctx.stroke()
            ctx.restore()
        self.mask.update()

    def __get_text_extent(self, word, size):
        x = ct.c_int(0)
        y = ct.c_int(0)
        width = ct.c_int(0)
        height = ct.c_int(0)

        lib.get_text_extent(self.ctx._cairobj, word.encode('utf-8'), size, self.font_family,
            ct.byref(width), ct.byref(height), ct.byref(x), ct.byref(y))

        return Extent(x.value, y.value, width.value, height.value)

    def __text_path(self, ctx, word, size):
        lib.path_text(ctx._cairobj, word.encode('utf-8'), size, self.font_family)


    def write(self) -> io.BytesIO:
        buf = io.BytesIO()
        self.surface.write_to_png_file(buf)
        buf.seek(0)
        return buf

def png_to_surface(data):
    if data:
        return cairo.ImageSurface.create_from_png_bytes(data)
    else:
        surface = cairo.ImageSurface.create(CAIRO.FORMAT_ARGB32, (100, 100))
        ctx = cairo.Context.create(surface)
        ctx.source_colour = (1, 0, 0, 1)
        ctx.set_line_width(10)
        ctx.rectangle(cairo.Rect(0, 0, 100, 100))
        ctx.move_to((0, 0))
        ctx.line_to((100, 100))
        ctx.move_to((0, 100))
        ctx.line_to((100, 0))
        ctx.stroke()
        return surface
        
def load_font(path):
    lib.load_font(path.encode('utf-8'))