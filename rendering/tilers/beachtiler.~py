from thorpy._utils.interpolation import get_y
from pygame import surfarray
import math, pygame
from PyWorld2D.rendering.tilers.roundtiler import RoundTiler


class BeachTiler(RoundTiler):


    def get_round(self, radius, background):
        w,h = self.c.get_size()
        surface = self.s.copy().convert_alpha()
        newsurf = pygame.Surface((w,h), pygame.SRCALPHA,
                                  depth=self.c.get_bitsize()).convert_alpha()
        newsurf.fill((0,0,0,0))
        inner = self.c.get_rect().inflate((-4*radius, -4*radius))
        n_a = surfarray.pixels_alpha(newsurf)
        n_rgb = surfarray.pixels3d(newsurf)
        b_b_c_rgb = surfarray.pixels3d(self.c)
        rngs = [(inner.x,inner.y,0,inner.x,0,inner.y),
                (inner.right,inner.y,inner.right,w,0,inner.y),
                (inner.x,inner.bottom,0,inner.x,inner.bottom,h),
                (inner.right,inner.bottom,inner.right,w,inner.bottom,h)]
        for i, ranges in enumerate(rngs):
            x0,y0,xi,xf,yi,yf = ranges
            for x in range(xi,xf):
                for y in range(yi,yf):
                    d = math.hypot(x-x0, y-y0)
                    n_a[x][y] = 255 - get_y(d,0,2*radius)
                    n_rgb[x][y] = b_b_c_rgb[x][y]
        del n_a
        del n_rgb
        surface.unlock()
        newsurf.unlock()
        surface.blit(newsurf,(0,0))
        return surface

    def get_antiround(self, radius, background):
        w,h = self.c.get_size()
        surface = self.s.copy().convert_alpha()
        newsurf = pygame.Surface((w,h), pygame.SRCALPHA,
                                  depth=self.c.get_bitsize()).convert_alpha()
        newsurf.fill((0,0,0,0))
        outer = self.c.get_rect().inflate((-2*radius, -2*radius))
        n_a = surfarray.pixels_alpha(newsurf)
        n_rgb = surfarray.pixels3d(newsurf)
        b_b_c_rgb = surfarray.pixels3d(self.c)
        rngs = [(0,0,0,2*radius,0,2*radius),
                (w,0,w-2*radius,w,0,2*radius),
                (0,h,0,2*radius,h-2*radius,h),
                (w,h,w-2*radius,w,h-2*radius,h)]
        for i, ranges in enumerate(rngs):
            x0,y0,xi,xf,yi,yf = ranges
            for x in range(xi,xf):
                for y in range(yi,yf):
                    d = math.hypot(x-x0, y-y0)
                    n_a[x][y] = get_y(d,0,2*radius)
                    n_rgb[x][y] = b_b_c_rgb[x][y] #grass
        del n_a
        del n_rgb
        surface.unlock()
        newsurf.unlock()
        surface.blit(newsurf,(0,0))
        return surface

    def cut_side(self, side, radius, background):
        w,h = self.c.get_size()
        b_c_surf = self.c.copy().convert_alpha() #beach
        newsurf = pygame.Surface((w,h), pygame.SRCALPHA,
                                  depth=self.c.get_bitsize()).convert_alpha()
        newsurf.fill((0,0,0,0))
        n_a = surfarray.pixels_alpha(newsurf)
        n_rgb = surfarray.pixels3d(newsurf)
        s_rgb = surfarray.pixels3d(self.s)
        b_c_rgb = surfarray.pixels3d(b_c_surf)
        if "top" in side:
            for x in range(w):
                for y in range(0,2*radius):
                    n_a[x][y] = 255 - get_y(y, 0, 2*radius)
                    n_rgb[x][y] = s_rgb[x][y]
        if "bottom" in side:
            for x in range(w):
                for y in range(h-2*radius,h):
                    n_a[x][y] = get_y(y, h-2*radius, h)
                    n_rgb[x][y] = s_rgb[x][y]
        if "left" in side:
            for y in range(h):
                for x in range(0,2*radius):
                    n_a[x][y] = 255 - get_y(x, 0, 2*radius)
                    n_rgb[x][y] = s_rgb[x][y]
        if "right" in side:
            for y in range(h):
                for x in range(w-2*radius,w):
                    n_a[x][y] =  get_y(x, w-2*radius, w)
                    n_rgb[x][y] = s_rgb[x][y]
        del n_a
        del n_rgb
        del b_c_rgb
        b_c_surf.unlock()
        newsurf.unlock()
        b_c_surf.blit(newsurf, (0,0))
        return b_c_surf

    def _debug(self):
        for img in self.imgs.values():
            pygame.draw.rect(img, (0,0,0), img.get_rect(), 1)
