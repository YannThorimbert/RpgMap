import math
import pygame
from thorpy._utils.images import load_image
from pygame import surfarray

rounding = ["tblr","tbl","lrb","bl","tbr","tb","br","b","lrt","tl","lr","l",
            "tr","t","r","c"]

def _get_corners(surface, size):
    tl = pygame.Surface((size, size)).convert()
    tr = pygame.Surface((size, size)).convert()
    bl = pygame.Surface((size, size)).convert()
    br = pygame.Surface((size, size)).convert()
    w,h = surface.get_size()
    tl.blit(surface, (0,0))
    tr.blit(surface, (-w+size,0))
    bl.blit(surface, (0,-h+size))
    br.blit(surface, (-w+size,-h+size))
    return tl, tr, bl, br


class BaseTiler(object):

    def __init__(self, c, colorkey=None):
        if isinstance(c, str):
            self.original_img = load_image(c, colorkey)
        else:
            self.original_img = c
        self.c = self.original_img.copy() #current center
        self.imgs = {}

    def get_img(self, value):
        return self.imgs[rounding[value]]

    def get_name(self, value):
        return rounding[value]

    def get_void_surf(self):
        return pygame.Surface(self.c.get_size())

    def cut_side(self, side, radius, background):
        #version for color background
        surf =  self.get_void_surf()
        surf.fill(background)
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
        rngs = [(inner.x,inner.y,0,inner.x,0,inner.y),
                (inner.right,inner.y,inner.right,w,0,inner.y),
                (inner.x,inner.bottom,0,inner.x,inner.bottom,h),
                (inner.right,inner.bottom,inner.right,w,inner.bottom,h)]
        for x0,y0,xi,xf,yi,yf in rngs:
            for x in range(xi,xf):
                for y in range(yi,yf):
                    if math.sqrt((x-x0)**2 + (y-y0)**2) > radius:
                        b_c_rgb[x][y] = background
        return surface

    def get_antiround(self, radius, background):
        #version for color background
        w,h = self.c.get_size()
        surface = self.c.copy()
        b_c_rgb = surfarray.pixels3d(surface)
        rngs = [(0,0,0,radius,0,radius),
                (w,0,w-radius,w,0,radius),
                (0,h,0,radius,h-radius,h),
                (w,h,w-radius,w,h-radius,h)]
        for x0,y0,xi,xf,yi,yf in rngs:
            for x in range(xi,xf):
                for y in range(yi,yf):
                    if math.sqrt((x-x0)**2 + (y-y0)**2) < radius:
                        b_c_rgb[x][y] = background
        return surface

    def get_corners(self, radius, background):
        tl, tr, bl, br = _get_corners(self.get_round(radius, background), 2*radius)
        return tr, tl, br, bl

    def get_anticorners(self, radius, background):
        tl, tr, bl, br = _get_corners(self.get_antiround(radius, background), 2*radius)
        return tr, tl, br, bl

    def make_round(self, surf, name, radius, corners):
        w,h = self.c.get_size()
        tr, tl, br, bl = corners
        if "top" in name and "left" in name:
            surf.blit(tl,(0,0))
        if "top" in name and "right" in name:
            surf.blit(tr,(w-2*radius,0))
        if "bottom" in name and "left" in name:
            surf.blit(bl,(0,h-2*radius))
        if "bottom" in name and "right" in name:
            surf.blit(br,(w-2*radius,h-2*radius))

    def build_tile(self, name, radius, background, corners, rounded=True):
        surf = self.cut_side(name, radius, background)
        if rounded:
            self.make_round(surf, name, radius, corners)
        return surf

    def build_internal_help(self, names, radius, background, anticorners):
        knames, xnames, ynames, znames = names
        x,k,z,y = anticorners
        w,h = self.c.get_size()
        wr,hr = k.get_size()
        for name in knames:
            if name in self.imgs:
                img = self.imgs[name].copy()
                img.blit(k,(0,0))
                self.imgs[name+"k"] = img
        for name in xnames:
            if name in self.imgs:
                img = self.imgs[name].copy()
                img.blit(x,(w-wr,0))
                self.imgs[name+"x"] = img
        for name in ynames:
            if name in self.imgs:
                img = self.imgs[name].copy()
                img.blit(y,(0,h-hr))
                self.imgs[name+"y"] = img
        for name in znames:
            if name in self.imgs:
                img = self.imgs[name].copy()
                img.blit(z,(w-wr,h-hr))
                self.imgs[name+"z"] = img

    def build_internals(self, radius, background, anticorners):
        knames = ["br","b","r","c"]
        xnames = ["bl","b","l","c"]
        ynames = ["tr","t","r","c"]
        znames = ["tl","l","t","c"]
        self.build_internal_help([knames,xnames,ynames,znames], radius,
                                 background, anticorners)
        knames = []
        xnames = ["bk","ck"]
        ynames = ["rk","ck","cx"]
        znames = ["lx","ty","ck","cx","cy"]
        self.build_internal_help([knames,xnames,ynames,znames], radius,
                                 background, anticorners)
        knames = []
        xnames = []
        ynames = ["ckx"]
        znames = ["ckx","cky","cxy"]
        self.build_internal_help([knames,xnames,ynames,znames], radius,
                                 background, anticorners)
        knames = []
        xnames = []
        ynames = []
        znames = ["ckxy"]
        self.build_internal_help([knames,xnames,ynames,znames], radius,
                                 background, anticorners)



    def build_tiles(self, radius, background):
        corners = self.get_corners(radius, background)
        anticorners = self.get_anticorners(radius, background)
        self.imgs["c"] = self.c
##        self.imgs["s"] = self.c.copy()
        # 0th order (no corners)
        self.imgs["t"] = self.cut_side("top", radius, background)
        self.imgs["b"] = self.cut_side("bottom", radius, background)
        self.imgs["l"] = self.cut_side("left", radius, background)
        self.imgs["r"] = self.cut_side("right", radius, background)
        #corner (preprocess)
        self.imgs["tl"] = self.build_tile("topleft",radius,background,corners)
        self.imgs["tr"] = self.build_tile("topright",radius,background,corners)
        self.imgs["bl"] = self.build_tile("bottomleft",radius,background,corners)
        self.imgs["br"] = self.build_tile("bottomright",radius,background,corners)
        # 2nd order (bicorners
        self.imgs["tb"] = self.cut_side("topbottom", radius, background)
        self.imgs["lr"] = self.cut_side("leftright", radius, background)
        #3rd order (tricorners)
        self.imgs["tbl"] = self.build_tile("topbottomleft", radius, background, corners)
        self.imgs["tbr"] = self.build_tile("topbottomright", radius, background, corners)
        self.imgs["tlr"] = self.build_tile("leftrighttop", radius, background, corners)
        self.imgs["blr"] = self.build_tile("leftrightbottom", radius, background, corners)
        #4th order (quadricorners)
        self.imgs["tblr"] = self.build_tile("topbottomleftright", radius, background, corners)
        self.build_internals(radius, background, anticorners)

    def make(self, size, radius, background=(255,255,255), scale_first=True):
        if scale_first:
            self.scale_base(size)
        self.build_tiles(radius, background)
        if not scale_first:
            self.scale_base(size)
            self.scale_all_to_c()

    def scale_base(self, size):
        if size != self.original_img.get_size():
            self.c = pygame.transform.scale(self.original_img, size)

    def scale_all_to_c(self):
        size = self.c.get_size()
        for key in self.imgs:
            self.imgs[key] = pygame.transform.scale(self.imgs[key],size)