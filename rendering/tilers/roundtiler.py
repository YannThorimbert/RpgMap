from thorpy._utils.images import load_image
from pygame import surfarray
import math, pygame
from RpgMap.rendering.tilers.basetiler import BaseTiler

class RoundTiler(BaseTiler):

    def __init__(self, c, s, c_colorkey=None, s_colorkey=None):
        BaseTiler.__init__(self, c, c_colorkey)
        if isinstance(s, str):
            self.original_s = load_image(s, s_colorkey)
        else:
            self.original_s = s
        self.s = self.original_s.copy() #current center
        if self.s.get_size() != self.c.get_size():
            self.s = pygame.transform.scale(self.s, self.c.get_size())

    def scale_base(self, size):
        if size != self.original_img.get_size():
            self.c = pygame.transform.scale(self.original_img, size)
            self.s = pygame.transform.scale(self.original_s, size)

    def build_tiles(self, radius, background):
        self.imgs["s"] = self.s
        BaseTiler.build_tiles(self, radius, background)

    def make(self, size, radius, scale_first=True):
        if scale_first:
            self.scale_base(size)
        self.build_tiles(radius, background=None)
        if not scale_first:
            self.scale_base(size)
            self.scale_all_to_c()

    def cut_side(self, side, radius, background):
        #version for color background
        surf =  self.s.copy()
        w,h = self.c.get_size()
        rect = surf.get_rect()
        if "top" in side:
            rect = pygame.Rect(0, radius, w, h-radius)
        if "bottom" in side:
            rect = rect.clip(pygame.Rect(0, 0, w, h-radius))
        if "left" in side:
            rect = rect.clip(pygame.Rect(radius, 0, w-radius, h))
        if "right" in side:
            rect = rect.clip(pygame.Rect(0, 0, w-radius, h))
        surf.blit(self.c, rect.topleft, rect)
        return surf

    def get_round(self, radius, background):
        #version for color background
        w,h = self.c.get_size()
        surface = self.c.copy()
        inner = self.c.get_rect().inflate((-4*radius, -4*radius))
        b_c_rgb = surfarray.pixels3d(surface)
        s_rgb = surfarray.pixels3d(self.s)
        rngs = [(inner.x,inner.y,0,inner.x,0,inner.y),
                (inner.right,inner.y,inner.right,w,0,inner.y),
                (inner.x,inner.bottom,0,inner.x,inner.bottom,h),
                (inner.right,inner.bottom,inner.right,w,inner.bottom,h)]
        radiusSqr = radius**2
        for x0,y0,xi,xf,yi,yf in rngs:
            for x in range(xi,xf):
                dxSqr = (x-x0)**2
                if dxSqr < radiusSqr:
                    for y in range(yi,yf):
                        if dxSqr + (y-y0)**2 < radiusSqr:
                            b_c_rgb[x][y] = s_rgb[x][y]
        return surface

    def get_antiround(self, radius, background):
        w,h = self.c.get_size()
        surface = self.c.copy()
        b_c_rgb = surfarray.pixels3d(surface)
        s_rgb = surfarray.pixels3d(self.s)
        rngs = [(0,0,0,radius,0,radius),
                (w,0,w-radius,w,0,radius),
                (0,h,0,radius,h-radius,h),
                (w,h,w-radius,w,h-radius,h)]
        radiusSqr = radius**2
        for x0,y0,xi,xf,yi,yf in rngs:
            for x in range(xi,xf):
                dxSqr = (x-x0)**2
                if dxSqr < radiusSqr:
                    for y in range(yi,yf):
                        if dxSqr + (y-y0)**2 < radiusSqr:
                            b_c_rgb[x][y] = s_rgb[x][y]
        return surface


##def get_round(radius, side, front):
##    if not delta:
##        return front
##    w,h = front.get_size()
##    background = pygame.Surface((w,h))
##    surface = front.copy().convert_alpha()
##    newsurf = pygame.Surface((w,h), pygame.SRCALPHA,
##                              depth=background.get_bitsize()).convert_alpha()
##    newsurf.fill((0,0,0,0))
##    inner = background.get_rect().inflate((-2*radius, -2*radius))
##    n_a = surfarray.pixels_alpha(newsurf)
##    n_rgb = surfarray.pixels3d(newsurf)
##    b_b_c_rgb = surfarray.pixels3d(background)
##    #Define ranges.
##    topleft = (inner.left,inner.top,     0,inner.left,   0,inner.top)
##    topright = (inner.right,inner.top,    inner.right,h,  0,inner.top)
##    bottomleft = (inner.left,inner.bottom,  0,inner.left,   inner.bottom,h)
##    bottomright = (inner.right-1,inner.bottom-1, inner.right,h,  inner.bottom,h)
##    ranges = []
##    dx,dy = delta
####    if "t" in sides and "l" in sides:
##    if dx>0 and dy>0:
##        ranges.append(topleft)
##    elif dx<0 and dy<0:
##        ranges.append(bottomleft)
##    elif dx<0 and dy>0:
##        ranges.append(topright)
##    elif dx>0 and dy<0:
##        ranges.append(bottomright)
##    r2 = radius**2
##    for centerx,centery,xi,xf,yi,yf in ranges:
##        for x in range(xi,xf):
##            rx2 = (x-centerx)**2
##            for y in range(yi,yf):
##                if rx2 + (y-centery)**2 > r2:
##                    n_a[x][y] = 255  #alpha background = 255
##                    n_rgb[x][y] = b_b_c_rgb[x][y]
##    del n_a
##    del n_rgb
##    surface.unlock()
##    newsurf.unlock()
##    surface.blit(newsurf,(0,0))
##    surface = surface.convert()
##    surface.set_colorkey((0,0,0))
##    return surface


def get_round_river(radius_divider, corner, front):
    if corner is None:
        return front
    w,h = front.get_size()
    background = pygame.Surface((w,h))
    surface = front.copy().convert_alpha()
    newsurf = pygame.Surface((w,h), pygame.SRCALPHA,
                              depth=background.get_bitsize()).convert_alpha()
    newsurf.fill((0,0,0,0))
    radius = w//radius_divider
    inner = background.get_rect().inflate((-2*radius, -2*radius))
    n_a = surfarray.pixels_alpha(newsurf)
    n_rgb = surfarray.pixels3d(newsurf)
    b_b_c_rgb = surfarray.pixels3d(background)
    #Define ranges.
    topleft = (inner.left,inner.top,     0,inner.left,   0,inner.top)
    topright = (inner.right,inner.top,    inner.right,h,  0,inner.top)
    bottomleft = (inner.left,inner.bottom,  0,inner.left,   inner.bottom,h)
    bottomright = (inner.right-1,inner.bottom-1, inner.right,h,  inner.bottom,h)
    ranges = {"topleft":topleft, "topright":topright, "bottomleft":bottomleft,
                "bottomright":bottomright}
    r2 = radius**2
    centerx,centery,xi,xf,yi,yf = ranges[corner]
    for x in range(xi,xf):
        rx2 = (x-centerx)**2
        for y in range(yi,yf):
            if rx2 + (y-centery)**2 > r2:
                n_a[x][y] = 255  #alpha background = 255
                n_rgb[x][y] = b_b_c_rgb[x][y]
##            else:
##                n_rgb[x][y] = (b_b_c_rgb[x][y]+n_rgb[x][y])//2
    del n_a
    del n_rgb
    surface.unlock()
    newsurf.unlock()
    surface.blit(newsurf,(0,0))
    surface = surface.convert()
    surface.set_colorkey((0,0,0))
    return surface
