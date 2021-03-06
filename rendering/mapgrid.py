import math
import pygame
import thorpy
from thorpy.gamestools.basegrid import BaseGrid
from thorpy.gamestools.grid import PygameGrid
from RpgMap.rendering.tilers.tilemanager import get_couple
import RpgMap.logic.constants as const

VON_NEUMAN = [(-1,0), (1,0), (0,-1), (0,1)]
MOORE = [(-1,-1), (1,1), (1,-1), (-1,1)]
WATER = 1
GRASS = 0


class LogicalCell:

    def __init__(self, h, coord, logical_map):
        self.lm = logical_map
        self.couple = get_couple(h, self.lm.material_couples)
        self.h = h
        self.coord = coord
        if h > self.couple.transition:
            self.value = GRASS
            self.material = self.couple.grass
        else:
            self.value = WATER
            self.material = self.couple.water
        self.type = None
        self.name = ""
        self.objects = []
        self.unit = None
##        self.imgs = None

    def get_chunk(self):
        return self.lm.chunk

    def get_game(self):
        return self.lm.me.game

    def set_name(self,name):
        self.name = name
        self.lm.me.modified_cells.append(self.coord)

    def get_neighbors_von_neuman(self):
        for dx,dy in VON_NEUMAN:
            yield self.lm.get_cell_at(self.coord[0]+dx, self.coord[1]+dy)

    def get_neighbors_moore(self):
        for dx,dy in VON_NEUMAN:
            yield self.lm.get_cell_at(self.coord[0]+dx, self.coord[1]+dy)
        for dx,dy in MOORE:
            yield self.lm.get_cell_at(self.coord[0]+dx, self.coord[1]+dy)

    def get_altitude(self):
        return (self.h-0.6)*2e4

    def get_static_img_at_zoom(self, level):
        return self.lm.get_static_img_at_zoom(self.coord, level)

    def has_object_name(self, name):
        for o in self.objects:
            if o.name == name:
                return True
        return False

    def distance_to(self, other):
        return abs(self.coord[0]-other.coord[0]) + abs(self.coord[1]-other.coord[1])

    def distance_to_coord(self, coord):
        return abs(self.coord[0]-coord[0]) + abs(self.coord[1]-coord[1])


class GraphicalCell:

    def __init__(self):
        self.imgs = None



class LogicalMap(BaseGrid):

    def __init__(self, hmap, material_couples, outsides,
                    restrict_size):
        self.material_couples = material_couples
        self.zoom_levels = list(range(len(material_couples[0].tilers)))
        self.current_zoom_level = 0
        if restrict_size is None:
            nx, ny = len(hmap), len(hmap[0])
        else:
            nx, ny = restrict_size
        BaseGrid.__init__(self, int(nx), int(ny))
        self.current_x = 0
        self.current_y = 0
        self.graphical_maps = [] #list of maps, index = zoom level
        self.cell_sizes = []
        for z in self.zoom_levels:
            cell_size = material_couples[0].get_cell_size(z)
            gm = GraphicalMap(nx, ny, cell_size, z, outsides[z])
            gm.lm = self
            self.graphical_maps.append(gm)
            self.cell_sizes.append(cell_size)
        self.current_gm = self.graphical_maps[0]
        #
        self.nframes = len(material_couples[0].get_tilers(0))
        self.t = 0 #in unit of materials frame
        self.t1 = 0 #used for default animated graphics
        self.t2 = 0 #used for fast animated graphics
        self.t3 = 0 #used for slow animated graphics
        self.t4 = 0
        self.tot_time = 0 #in unit of pygame frame
        self.frame_slowness1 = None #associated to t1. Reset in mapbuilding !!!
        self.frame_slowness2 = None #associated to t2
        self.frame_slowness3 = None
        self.frame_slowness4 = None
        #
        self.refresh_cell_heights(hmap)
        self.refresh_cell_types()
        self.colorkey = None #used at build_surface()
        self.static_objects = []
        self.me = None
        self.chunk = None


    def get_slowness(self,number):
        if number == const.NORMAL:
            return self.frame_slowness1
        elif number == const.FAST:
            return self.frame_slowness2
        elif number == const.SLOW:
            return self.frame_slowness3


    def get_current_cell_size(self):
        return self.cell_sizes[self.current_zoom_level]

    def set_zoom(self, level):
        self.current_zoom_level = level
        self.current_gm = self.graphical_maps[level]
        if self.current_x < 0:
            self.current_x = 0
        elif self.current_x > self.nx-2:
            self.current_x = self.nx-2
        if self.current_y < 0:
            self.current_y = 0
        elif self.current_y > self.ny-2:
            self.current_y = self.ny-2

    def next_frame(self):
        self.tot_time += 1
        if self.tot_time % self.frame_slowness2 == 0:
            self.t2 += 1
        if self.tot_time % self.frame_slowness3 == 0:
            self.t3 += 1
        if self.tot_time % self.frame_slowness4 == 0:
            self.t4 += 1
        if self.tot_time % self.frame_slowness1 == 0:
            self.t1 += 1
            self.t = (self.t+1) % self.nframes
            return True

    def refresh_cell_heights(self, hmap):
        for x,y in self:
            self[x,y] = LogicalCell(hmap[x][y], (x,y), self)


    def get_cell_at(self, x, y):
        if self.is_inside((x,y)):
            return self[x,y]
        else:
            return None

    def get_neighbour_value_at(self, x, y, x0, y0):
        neighbour = self.get_cell_at(x,y)
        origin = self[x0,y0]
        if neighbour is None:
            return origin.value #then returns the same as demanding
        else:
            if neighbour.material is origin.material:
                return origin.value
            elif neighbour.material.hmax > origin.material.hmax:
                return GRASS
            else:
                return WATER

    def refresh_cell_types(self):
        for x,y in self:
            cell = self[x,y]
            if cell.value == GRASS:
                t = self.get_neighbour_value_at(x,y-1,x,y)
                b = self.get_neighbour_value_at(x,y+1,x,y)
                l = self.get_neighbour_value_at(x-1,y,x,y)
                r = self.get_neighbour_value_at(x+1,y,x,y)
                n = t*"t" + b*"b" + l*"l" + r*"r"
                if not n:
                    n = "c"
                tl = self.get_neighbour_value_at(x-1,y-1,x,y)
                tr = self.get_neighbour_value_at(x+1,y-1,x,y)
                bl = self.get_neighbour_value_at(x-1,y+1,x,y)
                br = self.get_neighbour_value_at(x+1,y+1,x,y)
                if tl and not(t) and not(l):
                    n += "k"
                if tr and not(t) and not(r):
                    n += "x"
                if bl and not(b) and not(l):
                    n += "y"
                if br and not(b) and not(r):
                    n += "z"
                cell.type = n
            else:
                cell.type = "s"
            for zoom, gm in enumerate(self.graphical_maps):
                if cell.type == "s":
                    type = "c"
                else:
                    type = cell.type
                gm[x,y].imgs = cell.couple.get_all_frames(zoom, type)



    def get_static_img_at_zoom(self, coord, zoom):
        """Returns the image contained on permanent cell of self.
        Use extract_img_at_zoom if you need the cell plus all what has been
        dynamically added (drawn) on self's surface."""
        if self.is_inside(coord):
            img = pygame.Surface((self.cell_sizes[0],)*2)
            self.extract_static_img_at_zoom(coord,zoom,img)
            return img
##            return self.graphical_maps[zoom][coord].imgs[self.t]
        else:
            return self.graphical_maps[zoom].outside_imgs[self.t]

    def extract_static_img_at_zoom(self, coord, zoom, img):
        """Returns the image of the cell of self plus what has been drawn on
        self's surface.
        Use get_static_img_at_zoom if you need the cell only."""
        if self.is_inside(coord):
            self.graphical_maps[zoom].extract_static_img(coord, self.t, img)
        else:
            img.blit(self.graphical_maps[zoom].outside_imgs[self.t],(0,0))



    def get_graphical_cell(self, coord, zoom):
        return self.graphical_maps[zoom][coord]



    def draw(self, screen, dx_pix, dy_pix, topleft, bottomright):
        #dx_pix : number of pixels between the beginning of the cell and
        #   the actual pos.
        x0 = self.current_x
        y0 = self.current_y
        self.current_gm.draw(screen, x0, y0, dx_pix, dy_pix, self.t, topleft, bottomright)
##        self.current_gm.draw_blits(screen, topleft, x0, y0, dx_pix, dy_pix, self.t)

    def build_surfaces(self):
        for gm in self.graphical_maps:
            print("     Logical map building graphical map for size ",
                    gm.cell_size)
            gm.generate_submaps_parameters(factor=const.SUBMAP_FACTOR)
            gm.build_surfaces(self.colorkey)
##            gm.build_surfaces(self.colorkey)

    def blit_material_of_cell(self, cell):
        for gm in self.graphical_maps:
            gm.blit_material_of_cell(cell)


##    def blit_objects(self, objects=None, sort=True): #this is permanent
##        if objects is None:
##            objects = self.static_objects
##        #
##        ground = [o for o in objects if o.is_ground]
##        not_ground = [o for o in objects if not o.is_ground]
##        if sort:
##            not_ground.sort(key=lambda x: x.ypos())
##        for obj in ground:
##            self.blit_object(obj)
##        for obj in not_ground:
##            self.blit_object(obj)

    def blit_objects(self, objects=None, sort=True): #this is permanent
        pass

    def blit_objects_only_on_cells(self, objs, cells):
        """Blit objs only on the specified cells, cropping the rest"""
        for o in objs:
            for c in cells:
                for level, gm in enumerate(self.graphical_maps):
                    gm.blit_object_only_on_cell(o,c)

    def blit_object(self, obj): #this is permanent
        """Permanently blit obj onto self's surfaces."""
        for level, gm in enumerate(self.graphical_maps):
            gm.blit_object_all_frames(obj)



class GraphicalMap(PygameGrid):

    def __init__(self, nx, ny, cell_size, level, outside_imgs):
##        cell_size = material_couples[0].get_cell_size(zoom_level)
        PygameGrid.__init__(self, int(nx), int(ny),
                            cell_size=(cell_size,)*2,
                            topleft=(0,0))
        self.level = level
        self.outside_imgs = outside_imgs
        self.cell_size = cell_size
        for coord in self:
            self[coord] = GraphicalCell()
        self.surfaces = None
        self.nframes = len(self.outside_imgs)
        #
        self.submap_size_pix = None
        self.submap_size_cells = None
        self.n_submaps = None
        self.screen_rect = thorpy.get_screen().get_rect()
        self.colorkey = None
        self.lm = None

    def generate_submaps_parameters(self, factor):
        cells_per_submap_x = factor//self.cell_size
        self.submap_size_pix = (cells_per_submap_x*self.cell_size, )*2
        self.n_submaps = (math.ceil(self.frame.w/self.submap_size_pix[0]),
                          math.ceil(self.frame.h/self.submap_size_pix[1]))
        self.submap_size_cells = (self.submap_size_pix[0]//self.cell_size,
                                    self.submap_size_pix[1]//self.cell_size)


    def build_surfaces(self, colorkey):
        #create table of surfaces
        self.colorkey = colorkey
        self.surfaces = [[[None for frame in range(self.nframes)]
                            for y in range(self.n_submaps[1])]
                              for x in range(self.n_submaps[0])]
##        self.surfaces = [[[self.lm.me.surfaces32.pop() for frame in range(self.nframes)]
##                            for y in range(self.n_submaps[1])]
##                              for x in range(self.n_submaps[0])]


    def build_surface(self, submap_x, submap_y, frame_t):
        """x and y are the submap indices.
        This function build the submaps, not individual cells !"""
        xi = submap_x * self.submap_size_cells[0]
        yi = submap_y * self.submap_size_cells[1]
        xf = min(xi + self.submap_size_cells[0], self.nx)
        yf = min(yi + self.submap_size_cells[1], self.ny)
        glob_posx_pix = xi * self.cell_size
        glob_posy_pix = yi * self.cell_size
        #
        s = self.lm.me.surfaces32.pop()
        self.surfaces[submap_x][submap_y][frame_t] = s
        for x in range(xi,xf):
            xpix = x*self.cell_size
            for y in range(yi,yf):
                ypix = y*self.cell_size
                img = self[(x,y)].imgs[frame_t]
                s.blit(img, (xpix-glob_posx_pix,ypix-glob_posy_pix))
                #
##                cell = self.lm[x,y]
##                ground = [o for o in cell.objects if o.is_ground]
##                not_ground = [o for o in cell.objects if not(o.is_ground)]
##                sort = True
##                if sort:
##                    not_ground.sort(key=lambda x: x.ypos())
##                for o in ground:
##                    self.blit_object_at_frame(o, frame_t)
##                for o in not_ground:
##                    self.blit_object_at_frame(o, frame_t)
        if self.colorkey is not None:
            s.set_colorkey(self.colorkey)
##        self.surfaces[submap_x][submap_y][frame_t] = s


##    def build_surface_objects(self, submap_x, submap_y, frame_t):
##        """x and y are the submap indices.
##        This function build the submaps, not individual cells !"""
##        xi = submap_x * self.submap_size_cells[0]
##        yi = submap_y * self.submap_size_cells[1]
##        xf = min(xi + self.submap_size_cells[0], self.nx)
##        yf = min(yi + self.submap_size_cells[1], self.ny)
##        glob_posx_pix = xi * self.cell_size
##        glob_posy_pix = yi * self.cell_size
##        #
##        s = self.lm.me.surfaces32.pop()
##        for x in range(xi,xf):
##            xpix = x*self.cell_size
##            for y in range(yi,yf):
##                ypix = y*self.cell_size
##                img = self[(x,y)].imgs[frame_t]
##                s.blit(img, (xpix-glob_posx_pix,ypix-glob_posy_pix))
##                #
##                cell = self.lm[x,y]
##                ground = [o for o in cell.objects if o.is_ground and o.is_static]
##                not_ground = [o for o in cell.objects if not(o.is_ground) and o.is_static]
##                sort = True
##                if sort:
##                    not_ground.sort(key=lambda x: x.ypos())
##                for o in ground:
##                    self.blit_object_at_frame(o, frame_t)
##                for o in not_ground:
##                    self.blit_object_at_frame(o, frame_t)
##        if self.colorkey is not None:
##            s.set_colorkey(self.colorkey)
##        self.surfaces[submap_x][submap_y][frame_t] = s

    def blit_material_of_cell(self, cell):
        """Blit the base surface (terrain)"""
        x,y = cell.coord
##        cell_object = self.get_cell_rect_at_coord_in_submap(cell.coord)
##        cell_object.inflate_ip((self.cell_size//3,)*2)
##        cell_here = self.get_cell_rect_at_coord_in_submap((x, y))
##        area_to_be_blitted = cell_here.clip(cell_object)
        surfx = x // self.submap_size_cells[0]
        surfy = y // self.submap_size_cells[1]
        xpix = x*self.cell_size - surfx*self.submap_size_pix[0]
        ypix = y*self.cell_size - surfy*self.submap_size_pix[1]
        for t in range(self.nframes):
            img = self[(x,y)].imgs[t]
            self.surfaces[surfx][surfy][t].blit(img, (xpix,ypix))

    def blit_object_all_frames(self, obj):
        """blit images <obj_img> on self's surface"""
        print("**********boaf***********")
        for t in range(self.nframes):
            self.blit_object_at_frame(obj, t)

    def blit_object_at_frame(self, obj, t):
        """Blit images <obj_img> on self's surface.
        This function is sequentially called on a list of objs that have been
        prealably sorted, and occupying the core region of a submap (i.e. the
        objects of the borders are not expected to be correctly blitted using
        this function."""
        delta = obj.relpos
        reldx, reldy = int(delta[0]*self.cell_size), int(delta[1]*self.cell_size)
        xobj, yobj = obj.cell.coord
        img = obj.imgs_z_t[self.level][t%obj.nframes]
        obj_rect = img.get_rect()
        obj_rect.center = (self.cell_size//2,)*2
        obj_rect.move_ip(reldx, reldy)
        surfx = xobj//self.submap_size_cells[0]
        surfy = yobj//self.submap_size_cells[1]
        xpix = xobj*self.cell_size - surfx*self.submap_size_pix[0] + obj_rect.x #xx simplifiable ?
        ypix = yobj*self.cell_size - surfy*self.submap_size_pix[1] + obj_rect.y
##        for dx in range(-1,2):
##            for dy in range(-1,2):
##                cx,cy = surfx+dx, surfy+dy
##                if 0 <= cx < self.n_submaps[0] and 0 <= cy < self.n_submaps[1]: #xxx else : remonter a map adjacente...
##                    x = xpix - dx*self.submap_size_pix[0]
##                    y = ypix - dy*self.submap_size_pix[1]
##                    img = obj.imgs_z_t[self.level][t%obj.nframes]
##                    s = self.surfaces[cx][cy][t]
##                    if s:
##                        s.blit(img, (x,y))
##                    else:
##                        pass
####                        assert False
####                        self.build_surface(cx,cy,t)
####                        self.surfaces[cx][cy][t].blit(img, (x,y))

        cx, cy = surfx, surfy
        s = self.surfaces[cx][cy][t]
        if s:
            s.blit(img, (xpix,ypix))
            return True
        return False


    def blit_object_at_frame_on_coord(self, obj, t, coord):
        """Blit the part of image of <obj> on cell with coordinate <coord>."""
        delta = obj.relpos
        reldx, reldy = int(delta[0]*self.cell_size), int(delta[1]*self.cell_size)
        xobj, yobj = obj.cell.coord
        img = obj.imgs_z_t[self.level][t%obj.nframes]
        obj_rect = img.get_rect()
        obj_rect.center = (self.cell_size//2,)*2
        obj_rect.move_ip(reldx, reldy)
        obj_surfx = xobj//self.submap_size_cells[0]
        obj_surfy = yobj//self.submap_size_cells[1]
        obj_xpix = xobj*self.cell_size - obj_surfx*self.submap_size_pix[0] + obj_rect.x #xx simplifiable ?
        obj_ypix = yobj*self.cell_size - obj_surfy*self.submap_size_pix[1] + obj_rect.y
        #
        cell_surfx = coord[0]//self.submap_size_cells[0]
        cell_surfy = coord[1]//self.submap_size_cells[1]
        cell_xpix = coord[0]*self.cell_size - cell_surfx*self.submap_size_pix[0]
        cell_ypix = coord[1]*self.cell_size - cell_surfy*self.submap_size_pix[1]
        #
        s = self.surfaces[cell_surfx][cell_surfy][t]
        if s:
            cell_rect = pygame.Rect(cell_xpix,cell_ypix,self.cell_size,self.cell_size) #xxx
##            pygame.draw.rect(s, (0,0,0), cell_rect, 2)
            obj_xpix -= (cell_surfx-obj_surfx)*self.submap_size_pix[0]
            obj_ypix -= (cell_surfy-obj_surfy)*self.submap_size_pix[1]
            topleft = (obj_xpix,obj_ypix)
##            clip = obj_rect.clip(cell_rect)

##            r = img.get_rect()
##            pygame.draw.rect(s, (255,0,0), pygame.Rect(topleft,r.size), 2)
##            pygame.draw.rect(s, (0,0,0), cell_rect, 2)

            s.blit(img, topleft)
            return True
        return False


##    def is_border_and_submap_coord(self, obj):
##        """Return"""
##        delta = obj.relpos
##        reldx, reldy = int(delta[0]*self.cell_size), int(delta[1]*self.cell_size)
##        xobj, yobj = obj.cell.coord
##        frame_t = t%obj.nframes
##        obj_rect = obj.imgs_z_t[self.level][frame_t].get_rect()
##        obj_rect.center = (self.cell_size//2,)*2
##        obj_rect.move_ip(reldx, reldy)
##        surfx = xobj//self.submap_size_cells[0]
##        surfy = yobj//self.submap_size_cells[0]
##        xpix = xobj*self.cell_size - surfx*self.submap_size_pix[0] + obj_rect.x #xx simplifiable ?
##        ypix = yobj*self.cell_size - surfy*self.submap_size_pix[1] + obj_rect.y
##        #check neighboring subsurfaces
##        if surfx > 0: #neighbour left:
##            cx,cy = surfx-1, surfy
##            s = self.surfaces[cx][cy][t]
##            if s:
##                x = xpix + self.cell_size
##                y = ypix
##                img = obj.imgs_z_t[self.level][frame_t]
##                s.blit(img, (x,y))
##                neighs = self.lm[xobj-1,yobj].objects
##        return surfx,surfy


    def blit_object_only_on_cell(self, obj, cell):
        #First we deduce the absolute pos of the obj from its rel pos in the cell
        relpos = obj.relpos
        xobj, yobj = obj.cell.coord
        obj_rect = obj.imgs_z_t[self.level][0].get_rect()
        obj_rect.center = (self.cell_size//2,)*2
        dx, dy = int(relpos[0]*self.cell_size), int(relpos[1]*self.cell_size)
        obj_rect.move_ip(dx,dy)
        #fill table of surfaces
        # ######################################################################
        #xpix_tot [pix] : location of xobj in the global map
        #surfx [sub] : coord of the subsurface containing xobj
        #xpix [pix] : location of xobj in the sub surface (local map)
        xpix_tot = xobj*self.cell_size
        ypix_tot = yobj*self.cell_size
        surfx = xpix_tot//self.submap_size_pix[0]
        surfy = ypix_tot//self.submap_size_pix[1]
        xpix_sub = xpix_tot - surfx*self.submap_size_pix[0] + obj_rect.x
        ypix_sub = ypix_tot - surfy*self.submap_size_pix[1] + obj_rect.y
        # ######################################################################
##        cell_rect = self.get_cell_rect_at_coord_in_submap(cell.coord)
##        print("*** ", cell_rect, obj_rect)
##        if cell_rect.colliderect(obj_rect):
##            print("COLLIDING ! ", cell.coord, obj.cell.coord, obj.name)
##        else:
##            print("     NOT COLLIDING ! ", cell.coord, obj.cell.coord, obj.name)
##        return
        #it is possible that the cell is spread on different subsurfaces !
        #hence we loop :
        for dx in range(-1,2): #not cell ! Just self's subsurfaces
            for dy in range(-1,2): #not cell ! Just self's subsurfaces
                cx, cy = surfx+dx, surfy+dy
                #cx and cy are the subsurface coord of the current subsurface
                #control that the subsurface exists:
                if 0 <= cx < self.n_submaps[0] and 0 <= cy < self.n_submaps[1]:
                    #x [pix]is the location of the obj image in the subsurface of coord cx,cy
                    x = xpix_sub - dx*self.submap_size_pix[0]
                    y = ypix_sub - dy*self.submap_size_pix[1]
                    for t in range(self.nframes):
                        img_obj = obj.imgs_z_t[self.level][t%obj.nframes]
                        #ACCORDING TO ME, WE SHOULD CROP... But it seems to work anyway...
##                        img_rect = img_obj.get_rect()
##                        img_rect.topleft = x,y
##                        cell_rect = self.get_cell_rect_at_coord_in_submap(cell.coord)
##                        print("***", cell_rect, img_rect)
##                        if cell_rect.colliderect(obj_rect):
##                            print("COLLIDING ! ", cell.coord, obj.cell.coord, obj.name)
##                        else:
##                            print("     NOT COLLIDING ! ", cell.coord, obj.cell.coord, obj.name)

##                        return

##                        print("RECTs", img_rect, cell_rect)
##                        area_to_be_blitted = cell_rect.clip(img_rect)
##                        area_to_be_blitted = img_rect.clip(cell_rect)
##                        reste a rebouger en haut a gauche...
##                        area_to_be_blitted.move_ip((-x,-y))
##                        print("ATBB", area_to_be_blitted, img_rect)
##                        self.surfaces[cx][cy][t].blit(img_obj, (x+area_to_be_blitted.x,y+area_to_be_blitted.y), area_to_be_blitted)
                        self.surfaces[cx][cy][t].blit(img_obj, (x,y))

##FINALEMENT :
##    area to be blitted ne concerne que la partie de l'objet qui disparait qui chevauche les autres cellules.
##    Les autres cellules, donc, se redessinnent, mais on ne blitte que ca !


    def draw(self, screen, x0, y0, dxpix, dypix, t, topleft, bottomright):
        """Draw the map, submap by submap."""
        #x0 = current_x from lm
        delta_x = dxpix + x0*self.cell_size
        delta_y = dypix + y0*self.cell_size
        xi, yi = topleft
        xf, yf = bottomright
        for x in range(self.n_submaps[0]):
            x_loc_i = x * self.submap_size_cells[0]
            x_loc_f = x_loc_i + self.submap_size_cells[0]
            if xi <= x_loc_i <= xf or xi <= x_loc_f <= xf:
                posx = round(x*self.submap_size_pix[0] - delta_x)
                for y in range(self.n_submaps[1]):
                    y_loc_i = y * self.submap_size_cells[1]
                    y_loc_f = y_loc_i + self.submap_size_cells[1]
                    if yi <= y_loc_i <= yf or yi <= y_loc_f <= yf:
                        posy = round(y*self.submap_size_pix[1] - delta_y)
                        point = (posx, posy)
                        surf = self.surfaces[x][y][t]
                        if surf:
                            screen.blit(surf, point)
                        else:
##                            print("build surf", x, y, t)
                            self.build_surface(x,y,t)
                            screen.blit(self.surfaces[x][y][t], point)
                        #draw submap border:
##                        pygame.draw.rect(screen, (0,0,255), pygame.Rect(posx,posy,self.submap_size_pix[0],self.submap_size_pix[1]),1)
        #now blit static objects
##        for x in range(self.n_submaps[0]):
##            x_loc_i = x * self.submap_size_cells[0]
##            x_loc_f = x_loc_i + self.submap_size_cells[0]
##            if xi <= x_loc_i <= xf or xi <= x_loc_f <= xf:
##                posx = round(x*self.submap_size_pix[0] - delta_x)
##                for y in range(self.n_submaps[1]):
##                    y_loc_i = y * self.submap_size_cells[1]
##                    y_loc_f = y_loc_i + self.submap_size_cells[1]
##                    if yi <= y_loc_i <= yf or yi <= y_loc_f <= yf:
##                        posy = round(y*self.submap_size_pix[1] - delta_y)
##                        point = (posx, posy)
##                        cell = self.lm[x_loc_i,y_loc_i]
##                        print([o.name for o in cell.objects if o.is_static])
##                        ground = [o for o in cell.objects if o.is_ground and o.is_static]
##                        not_ground = [o for o in cell.objects if not(o.is_ground) and o.is_static]
##                        sort = True
##                        if sort:
##                            not_ground.sort(key=lambda x: x.ypos())
##                        for o in ground:
##                            self.blit_object_at_frame(o, t)
##                        for o in not_ground:
##                            self.blit_object_at_frame(o, t)
##                        screen.blit(self.surfaces[x][y][t], point)


##    def draw_blits(self, screen, topleft, x0, y0, xpix, ypix, t):
##        delta_x = topleft[0] - xpix - x0*self.cell_size
##        delta_y = topleft[1] - ypix - y0*self.cell_size
##        oldposx = delta_x
##        blits = []
##        for x in range(self.n_submaps[0]):
##            posx = round(x*self.submap_size_pix[0] + delta_x)
##            for y in range(self.n_submaps[1]):
##                posy = round(y*self.submap_size_pix[1] + delta_y)
##                blits.append((self.surfaces[x][y][t], (posx,posy)))
##        screen.blits(blits)

    def extract_static_img(self, coord, frame, img):
        """blit on <img> self's graphics present at <coord>"""
        cs = self.cell_size
        nx = int(const.SUBMAP_FACTOR/cs) #why 200 ?
        ny = int(const.SUBMAP_FACTOR/cs)
        size_x = nx*cs
        size_y = ny*cs
        surfx = coord[0]*cs//size_x
        surfy = coord[1]*cs//size_y
        xpix = coord[0]*cs - surfx*size_x
        ypix = coord[1]*cs - surfy*size_y
        s = self.surfaces[surfx][surfy][frame]
        if s:
            img.blit(s, (-xpix, -ypix))

##    def get_cell_rect_at_coord_in_submap(self, cell_coord):
##        xc,yc = cell_coord
##        xpix_tot = xc*self.cell_size
##        ypix_tot = yc*self.cell_size
##        surfx = xpix_tot//self.submap_size_pix[0]
##        surfy = ypix_tot//self.submap_size_pix[1]
##        xpix_sub = xpix_tot - surfx*self.submap_size_pix[0]
##        ypix_sub = ypix_tot - surfy*self.submap_size_pix[1]
##        return pygame.Rect(xpix_sub,ypix_sub,self.cell_size,self.cell_size)


