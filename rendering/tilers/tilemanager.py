import math, os
import pygame

has_surfarray = False
try:
    from RpgMap.rendering.tilers.beachtiler import BeachTiler
    from RpgMap.rendering.tilers.basetiler import BaseTiler
    from RpgMap.rendering.tilers.roundtiler import RoundTiler
    has_surfarray = True
except:
    pass

from RpgMap.rendering.tilers.loadtiler import LoadTiler

def get_mixed_tiles(img1, img2, alpha_img_2):
    i1 = img1.copy()
    i2 = img2.copy()
    i2.set_alpha(alpha_img_2)
    i1.blit(i2,(0,0))
    return i1

##def get_shifted_tiles(img, nframes, dx=0, dy=0, reverse=False, sin=True):
##    w, h = img.get_size()
##    s = pygame.Surface((2*w,2*h))
##    s.blit(img, (0,0))
##    s.blit(img, (w,0))
##    s.blit(img, (0,h))
##    s.blit(img, (w,h))
##    #now we just have to take slices
##    images = []
##    for i in range(nframes):
##        if sin:
##            delta_x = dx*math.sin(2.*math.pi*i/float(nframes))
##            delta_y = dy*math.sin(2.*math.pi*i/float(nframes))
##        else:
##            delta_x = i*dx
##            delta_y = i*dy
##        result = pygame.Surface((w,h))
##        result.blit(s,(delta_x-w//2,delta_y-h//2))
##        images.append(result)
##    if reverse:
##        images += images[::-1][1:-1]
##    return images

def get_shifted_tiles(img, nframes, dx=0, dy=0, reverse=False, sin=True):
    r = img.get_rect()
    w,h = r.size
    images = []
    for i in range(nframes):
        if sin:
            delta_x = dx*math.sin(2.*math.pi*i/float(nframes))
            delta_y = dy*math.sin(2.*math.pi*i/float(nframes))
        else:
            delta_x = i*dx
            delta_y = i*dy
##        print(delta_x,w)
##        assert abs(delta_x) <= w
##        assert abs(delta_y) <= h
        result = pygame.Surface(r.size)
        xsgn, ysgn = 1, 1
        if delta_x>0:
            xsgn = -1
        if delta_y>0:
            ysgn = -1
        result.blit(img,r.move(delta_x,delta_y))
        result.blit(img,r.move(delta_x,delta_y+ysgn*h))
        result.blit(img,r.move(delta_x+xsgn*w,delta_y))
        result.blit(img,r.move(delta_x+xsgn*w,delta_y+ysgn*h))
        images.append(result)
    if reverse:
        images += images[::-1][1:-1]
    return images

def build_tiles(img_fullsize, sizes, nframes, dx_divider=0, dy_divider=0,
                reverse=False, sin=True, colorkey=None):
    """Returns a list of list of images on the form : imgs[size][frame]"""
    imgs = []
    for size in sizes:
        #smoothscale is important here, otherwise FAST should be always True
        img = pygame.transform.smoothscale(img_fullsize, (size,)*2)
        dx = 0
        if dx_divider:
            dx = int(size/dx_divider)
        dy = 0
        if dy_divider:
            dy = int(size/dy_divider)
        imgs.append(get_shifted_tiles(img, nframes, dx, dy, reverse, sin))
    if colorkey:
        for tiles in imgs:
            for img in tiles:
                img.set_colorkey(colorkey)
    return imgs

def build_color_tiles(color, sizes, nframes, reverse=False, sin=True):
    imgs = []
    for size in sizes:
        img = pygame.Surface((size,)*2)
        img.fill(color)
        imgs.append(get_shifted_tiles(img, nframes, 0, 0, reverse, sin))
    return imgs

def get_radiuses(nframes, initial_value, increment, reverse=False, sin=True):
    values = []
    if sin:
        current = initial_value
    else:
        current = 0
    for i in range(nframes):
        if sin:
            delta = increment*math.sin(2.*math.pi*i/float(nframes))
        else:
            delta = increment
        current += delta
        values.append(int(current))
    if reverse:
        values = values[::-1][1:-1]
    return values


def build_tilers(grasses, waters, radius_divider, use_beach_tiler):
    nzoom = len(grasses)
    assert nzoom == len(waters) #same number of zoom levels
    nframes = len(grasses[0])
    for z in range(nzoom):
        assert nframes == len(waters[z]) #same number of frames
    tilers = [[None for n in range(nframes)] for z in range(nzoom)]
    for z in range(nzoom):
        cell_size = grasses[z][0].get_width()
        radius = cell_size//radius_divider
        for n in range(nframes):
            if use_beach_tiler:
                tiler = BeachTiler(grasses[z][n], waters[z][n])
                tiler.make(size=(cell_size,)*2, radius=radius)
            else:
                tiler = BaseTiler(grasses[z][n])
                tiler.make(size=(cell_size,)*2, radius=0)
            tilers[z][n] = tiler
    return tilers

def build_static_tilers(grasses, waters, radius_divider, use_beach_tiler):
    nzoom = len(grasses)
    assert nzoom == len(waters) #same number of zoom levels
    nframes = len(grasses[0])
    for z in range(nzoom):
        assert nframes == len(waters[z]) #same number of frames
    tilers = [[None for n in range(nframes)] for z in range(nzoom)]
    for z in range(nzoom):
        cell_size = grasses[z][0].get_width()
        radius = cell_size//radius_divider
        if use_beach_tiler:
            tiler = BeachTiler(grasses[z][0], waters[z][0])
            tiler.make(size=(cell_size,)*2, radius=radius)
        else:
            tiler = BaseTiler(grasses[z][0])
            tiler.make(size=(cell_size,)*2, radius=0)
        for n in range(nframes):
            tilers[z][n] = tiler
    return tilers

def build_tilers_fast(grasses, waters, radius_divider, use_beach_tiler):
    nzoom = len(grasses)
    assert nzoom == len(waters) #same number of zoom levels
    nframes = len(grasses[0])
    for z in range(nzoom):
        assert nframes == len(waters[z]) #same number of frames
    tilers = [[None for n in range(nframes)] for z in range(nzoom)]
    cell_size = grasses[0][0].get_width()
    radius = cell_size//radius_divider
    for n in range(nframes):
        if use_beach_tiler:
            tiler = BeachTiler(grasses[0][n], waters[0][n])
            tiler.make(size=(cell_size,)*2, radius=radius)
        else:
            tiler = BaseTiler(grasses[0][n])
            tiler.make(size=(cell_size,)*2, radius=0)
        tilers[0][n] = tiler
    if nzoom > 1:
        for z in range(1,nzoom):
            for n in range(nframes):
                if use_beach_tiler:
                    tiler = BeachTiler(grasses[z][n], waters[z][n])
                else:
                    tiler = BaseTiler(grasses[z][n])
                size = grasses[z][n].get_size()
                ref = tilers[0][n]
                for key in ref.imgs:
                    tiler.imgs[key] = pygame.transform.scale(ref.imgs[key], size)
                tilers[z][n] = tiler
    return tilers

def load_tilers_dynamic(i, grasses, waters, folder): #pour static, nframes=1
    nzoom = len(grasses)
    assert nzoom == len(waters) #same number of zoom levels
    nframes = len(grasses[0])
    for z in range(nzoom):
        assert nframes == len(waters[z]) #same number of frames
    tilers = [[None for n in range(nframes)] for z in range(nzoom)]
    for z in range(nzoom): #PEUT ETRE LARGEMENT OPTIMIZE VU QUE ON POURRAIT LOADER UNE SEULE FOIS CHAQUE IMAGE, A LA PLACE DE z FOIS
        cell_size = grasses[z][0].get_width()
        for n in range(nframes):
            basename = os.path.join(folder,str(i)+"_"+str(n)+"_")
            tilers[z][n] = LoadTiler(basename, (cell_size,)*2)
    return tilers

def load_tilers_static(i, grasses, waters, folder): #pour static, nframes=1
    nzoom = len(grasses)
    assert nzoom == len(waters) #same number of zoom levels
    nframes = len(grasses[0])
    for z in range(nzoom):
        assert nframes == len(waters[z]) #same number of frames
    tilers = [[None for n in range(nframes)] for z in range(nzoom)]
    for z in range(nzoom): #PEUT ETRE LARGEMENT OPTIMIZE VU QUE ON POURRAIT LOADER UNE SEULE FOIS CHAQUE IMAGE, A LA PLACE DE z FOIS
        cell_size = grasses[z][0].get_width()
        basename = os.path.join(folder,str(i)+"_"+str(0)+"_")
        tiler = LoadTiler(basename, (cell_size,)*2)
        for n in range(nframes):
            tilers[z][n] = tiler
    return tilers


def get_material_couples(materials, radius_divider, fast, use_beach_tiler,
                            load_tilers):
    materials.sort(key=lambda x:x.hmax)
    couples = []
    imgs_zoom0_mat0 = materials[0].imgs[0]
    nframes = len(imgs_zoom0_mat0)
    max_cell_size = imgs_zoom0_mat0[0].get_width()
    for i in range(len(materials)-1):
        print("     Building tilers for couple", i)
        assert nframes == len(materials[i+1].imgs[0])
        couple = MaterialCouple(i, materials[i], materials[i+1], radius_divider,
                                max_cell_size, fast, use_beach_tiler, load_tilers)
        couples.append(couple)
    return couples


def get_couple(h, couples):
    if h < 0.:
        return couples[0]
    else:
        for couple in couples:
            if couple.grass.hmax >= h:
                return couple
    return couples[-1]

class Material:

    def __init__(self, name, hmax, imgs, static):
        self.name = name
        self.hmax = hmax
        self.imgs = imgs
        self.static = static

class MaterialCouple:

    def __init__(self, i, material1, material2, radius_divider, max_cell_size,
                 fast, use_beach_tiler, load_tilers):
        if not has_surfarray and not load_tilers:
            raise Exception("Numpy was not found, and tilers are not loaded")
        assert material1.hmax != material2.hmax
        if material1.hmax > material2.hmax:
            self.grass, self.water = material1, material2
        else:
            self.grass, self.water = material2, material1
        #
        if load_tilers:
            if material1.static and material2.static:
                self.static = True
                self.tilers = load_tilers_static(i, self.grass.imgs, self.water.imgs, load_tilers)
            else:
                self.static = False
                self.tilers = load_tilers_dynamic(i, self.grass.imgs, self.water.imgs, load_tilers)
        else:
            build_tilers_static = build_static_tilers
            if fast:
                build_tilers_dynamic = build_tilers_fast
            else:
                build_tilers_dynamic = build_tilers
            if material1.static and material2.static:
                self.static = True
                self.tilers = build_tilers_static(self.grass.imgs, self.water.imgs,
                                                    radius_divider, use_beach_tiler)
            else:
                self.static = False
                self.tilers = build_tilers_dynamic(self.grass.imgs, self.water.imgs,
                                                    radius_divider, use_beach_tiler)
        self.transition = self.water.hmax
        self.max_cell_size = max_cell_size

    def get_tilers(self, zoom):
        return self.tilers[zoom]

    def get_cell_size(self, zoom):
        return self.tilers[zoom][0].imgs["c"].get_width()

    def get_all_frames(self, zoom, type_):
        return [self.tilers[zoom][t].imgs[type_] for t in range(len(self.tilers[zoom]))]

