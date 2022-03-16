from setuptools import setup
from Cython.Build import cythonize

setup(
    name='integral_image',
    ext_modules=cythonize("integral_image.pyx"),
    zip_safe=False,
)