import array
import numpy as np
cimport cython

# adapted from https://github.com/amueller/word_cloud/blob/master/wordcloud/query_integral_image.pyx

def get_space(int[:,:] data, int w, int h, random):
    cdef int x = data.shape[0]-1
    cdef int y = data.shape[1]-1
    cdef int area, i, j
    cdef int hits = 0

    # first just guess randomly (more efficient early on)
    for d in range(1000):
        i = random.randint(0, x - w)
        j = random.randint(0, y - h)
        area = data[i, j] + data[i + w, j + h]
        area -= data[i + w, j] + data[i, j + h]
        if area == 0:
            return i, j

    # resort to exhaustive search
    for i in xrange(x - w):
        for j in xrange(y - h):
            area = data[i, j] + data[i + w, j + h]
            area -= data[i + w, j] + data[i, j + h]
            if area == 0:
                hits += 1
    if not hits:
        # no room left
        return None
    # pick a location at random
    cdef int goal = random.randint(0, hits)
    hits = 0
    for i in xrange(x - w):
        for j in xrange(y - h):
            area = data[i, j] + data[i + w, j + h]
            area -= data[i + w, j] + data[i, j + h]
            if not area:
                hits += 1
                if hits == goal:
                    return i, j

def query_location(int[:,:] data, int i, int j, int w, int h):
    cdef area = data[i, j] + data[i + w, j + h]
    area -= data[i + w, j] + data[i, j + h]
    return area == 0