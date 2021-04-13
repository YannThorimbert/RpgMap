import pygame, math
from pygame import surfarray
from pygame.gfxdraw import pixel
import numpy

def _shift_periodic(surface, shiftx):
    w,h = surface.get_size()
    new_surf = pygame.Surface((w,h))
    new_surf.blit(surface, (shiftx,0))
    new_surf.blit(surface, (shiftx-w,0))
    return new_surf

def _smooth(surface):
    w,h = surface.get_size()
    arrayrgb = surfarray.pixels3d(surface)
    sum_array = numpy.zeros(arrayrgb.shape)
    for d in mapgen.MOORE:
        sum_array += numpy.roll(
                        numpy.roll(arrayrgb[:,:], d[0], axis=0),
                            d[1], axis=1 )
    sum_array /= len(mapgen.MOORE)
    s = surfarray.make_surface(sum_array)
    return s

def get_cliff_round(c, s, cliff, r_int, r_ext):
    #version for color background
    w,h = c.get_size()
    surface = s.copy()
    inner = c.get_rect().inflate((-4*r_int, -4*r_int))
    outer = c.get_rect().inflate((-4*r_ext, -4*r_ext))
    arrayrgb = surfarray.pixels3d(surface)
    c_arrayrgb = surfarray.pixels3d(c)
    cliff_arrayrgb = surfarray.pixels3d(cliff)
##    rngs = [(inner.x,inner.y,0,inner.x,0,inner.y),
##            (inner.right,inner.y,inner.right,w,0,inner.y),
##            (inner.x,inner.bottom,inner.x-r_int,inner.x,inner.bottom,h),
##            (inner.right,inner.bottom,inner.right,w-r_int+1,inner.bottom,h)]
    rngs = [(outer.x,outer.y,0,outer.x,0,outer.y),
            (outer.right,outer.y,outer.right,w,0,outer.y),
            (outer.x,outer.bottom,0,outer.x,outer.bottom,h),
            (outer.right,outer.bottom,outer.right,w-r_int+1,outer.bottom,h)]
##    rngs = [(r_ext,r_ext,0,r_ext,0,r_ext),
##            (w-r_ext,r_ext,w-r_ext,w,0,r_ext),
##            (r_ext,h-r_ext,0,r_ext,h-r_ext,h),
##            (w-r_ext,h-r_ext,w-r_ext,w,h-r_ext,h)]
    print(c.get_size(), s.get_size(), cliff.get_size(),rngs)
    for i, ranges in enumerate(rngs):
        x0,y0,xi,xf,yi,yf = ranges
        for x in range(xi,xf):
            for y in range(yi,yf):
                d = math.sqrt((x-x0)**2 + (y-y0)**2)
##                if i < 2:
##                    if d > r_int+1:
##                        continue
                if r_ext >= d >= r_int:
                    arrayrgb[x][y] = cliff_arrayrgb[x][y]
                elif d < r_int:
                    arrayrgb[x][y] = c_arrayrgb[x][y]
    return surface


class TileGen(object):

    def __init__(self, size, color1, color2, seed=None):
        self.size = size
        self.color1 = color1
        self.color2 = color2
        if seed is None:
            seed = mapgen.get_time_seed()
        self.mapgen = mapgen.BinarMapGenerator(self.size, seed)
        self.mapgen.n = 4
        self.mapgen.p = 0.5

    def build_surface(self, array, cellsize):
        """kx: width(in pixels) of ONE cell"""
        w, h = array.shape
        surface = pygame.Surface((w*cellsize, h*cellsize))
        rect = pygame.Rect(0, 0, cellsize, cellsize)
        for x in range(w):
            xpix = x * cellsize
            for y in range(h):
                ypix = y * cellsize
                rect.topleft = (xpix, ypix)
                if array[x][y]:
                    if cellsize == 1:
                        pixel(surface, x, y, self.color1)
                    else:
                        pygame.draw.rect(surface, self.color1, rect)
                else:
                    if cellsize == 1:
                        pixel(surface, x, y, self.color2)
                    else:
                        pygame.draw.rect(surface, self.color2, rect)
        return surface

    def get_surface(self, cellsize, n=None, p=None, smooth=3, coords=(0,0)):
        if n is not None:
            self.mapgen.n = n
        if p is not None:
            self.mapgen.p = p
        self.mapgen.gen_map(coords[0],coords[1])
        surface = self.build_surface(self.mapgen.cells, cellsize)
        for i in range(smooth):
            surface = _smooth(surface)
        return surface

    def get_surfaces_shift(self, n_surfaces, cellsize, n=None, p=None, smooth=3,
                     coords=(0,0), shift=1):
        s0 = self.get_surface(cellsize, n, p, smooth, coords)
        surfaces = [s0]
        for i in range(1,n_surfaces):
            s = _shift_periodic(s0, i*shift)
            surfaces.append(s)
        return surfaces