import array
import numpy as np
cimport cython

# adapted from https://github.com/amueller/word_cloud/blob/master/wordcloud/query_integral_image.pyx

def get_space(int[:,:] data, int w, int h, random):
    cdef int x = data.shape[1]-1
    cdef int y = data.shape[0]-1
    cdef int area, i, j
    cdef int hits = 0

    # first just guess randomly (more efficient early on)
    for d in range(1000):
        i = random.randint(0, y - h)
        j = random.randint(0, x - w)
        area = data[i, j] + data[i + h, j + w]
        area -= data[i + h, j] + data[i, j + w]
        if area == 0:
            return i, j

    # resort to exhaustive search
    for i in xrange(y - h):
        for j in xrange(x - w):
            area = data[i, j] + data[i + h, j + w]
            area -= data[i + h, j] + data[i, j + w]
            if area == 0:
                return i,j

def query_location(int[:,:] data, int i, int j, int w, int h):
    cdef area = data[i, j] + data[i + h, j + w]
    area -= data[i + h, j] + data[i, j + w]
    return area == 0