import ctypes as ct
import numpy as np
import qahirah as cairo
from qahirah import CAIRO as CAIRO

lib = ct.CDLL('./lib.so')
lib.get_location.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS'),
    ct.c_int,ct.c_int,ct.c_int,ct.c_int,
    ct.c_void_p, ct.c_void_p]
lib.get_location.restype = ct.c_int
lib.peform_sum.argtypes = [
    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS'),
    ct.c_int, ct.c_int,
    np.ctypeslib.ndpointer(dtype=np.int32, ndim=2, flags='C_CONTIGUOUS')]
lib.path_text.argtypes = [ct.c_void_p, ct.c_char_p, ct.c_int]
lib.get_text_extent.argtypes = [
    ct.c_void_p, ct.c_char_p, ct.c_int,
    ct.c_void_p, ct.c_void_p, ct.c_void_p, ct.c_void_p
]
lib.load_font.argtypes = [ct.c_char_p]

height = 120
width = 700

surface = cairo.ImageSurface.create(CAIRO.FORMAT_ARGB32, (width, height))
ctx = cairo.Context.create(surface)

ctx.move_to((10,10))
ctx.save()
lib.path_text(ctx._cairobj, "Test".encode('utf-8'), 72)
ctx.source_colour = (1.0, 0.8, 0.0)
ctx.fill_preserve()
ctx.source_colour = (0.8, 0.6, 0.0)
ctx.set_line_width(2)
ctx.stroke()

x = ct.c_int(0)
y = ct.c_int(0)
width = ct.c_int(0)
height = ct.c_int(0)

lib.get_text_extent(ctx._cairobj, "Test".encode('utf-8'), 150,
    ct.byref(width), ct.byref(height), ct.byref(x), ct.byref(y))
print(x,y,width,height)



surface.write_to_png("out.png")