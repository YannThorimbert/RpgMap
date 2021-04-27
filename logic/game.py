import os, random, pygame, thorpy
from RpgMap.effects import effects
from RpgMap.sprites.load import get_sprite_frames
from RpgMap.mapobjects.objects import MapObject
from RpgMap.logic.constants import SUBMAP_FACTOR
import gui.gui as gui

mo = thorpy.Monitor()

class Game:

    def __init__(self, me):
        self.me = me
        me.game = self
        self.gui = None
        self.t = 0
        self.units = []
        self.need_refresh_ui_box = True
        #Fire
        fire_imgs = get_sprite_frames("sprites/fire_idle.png")
        self.fire = MapObject(self.me, fire_imgs, "fire")
        self.fire.min_relpos=[0,-0.4]
        self.fire_max_relpos=[0,-0.4]
        self.fire.relpos=[0,-0.4]
        #Smoke
        self.smokes_log = {}
        effects.initialize_smokegens()
        #Default structures
        self.bridge_v, self.bridge_h = None, None
        self.bridges = []
        self.cobblestone = None
        self.road = None
        self.bridge_h = None
        self.bridge_v = None
        self.bridge = None
        self.is_main = True


    def add_bridge(self, coord):
##        assert not coord in self.bridges
##        bridge = self.find_right_bridge(coord)
##        bridge = self.bridge_h
        left = self.get_object("river", (coord[0]-1,coord[1]))
        right = self.get_object("river", (coord[0]-1,coord[1]))
        if left and right:
            bridge = self.bridge_v
        else:
            bridge = self.bridge_h
        self.add_object(coord, bridge)
        self.bridges.append(coord)

    def add_smoke(self, type_, coord, delta=None):
        if type_ == "small":
            sg = effects.smokegen_small
        else:
            sg = effects.smokegen_large
        smoke = effects.GameSmoke(self.me.cam, sg, coord, delta)
        self.smokes_log[coord] = smoke

    def remove_smoke(self, coord):
        return self.smokes_log.pop(coord, None)

    def refresh_smokes(self):
        effects.refresh_smokes(self)

    def recompute_smokes_position(self):
        for s in self.smokes_log.values():
            s.refresh_pos()

    def set_fire(self, chunk, coord, before=None):
        cell = self.get_cell_at(chunk, coord)
        if before is None:
            before = ("village","forest")
        self.add_obj_before_other_if_needed(self.fire,1,before,cell)

    def func_reac_time(self):
        mo.append("a")
        self.gui.refresh()
        mo.append("b")
        self.me.func_reac_time()
        mo.append("c")
        self.t += 1
        pygame.display.flip()
        mo.append("d")

##        if self.t%100 == 0:
##            mo.show(rnd=2)
##            print()

##        if self.t%100 == 0:
##            self.check_integrity()

    def update_loading_bar(self, text, progress):
        self.map_initializer.update_loading_bar(text, progress)

    def build_map(self, map_initializer, fast, use_beach_tiler, load_tilers):
        cs = self.me.cell_size
        n_submaps_per_map = 36
        n_time_frames = 16
        n_maps_on_screen = 9
        some_random_factor = 2.
        N = int(n_submaps_per_map*n_time_frames*n_maps_on_screen*some_random_factor)
        print("***INITIAL", N)
        map_initializer.init_loading_bar()
        map_initializer.update_loading_bar("Initializing surfaces",0.)
        for i in range(N):
            nsubmap_x = SUBMAP_FACTOR//cs
            submap_size = (nsubmap_x*cs, )*2
            self.me.surfaces32.append(pygame.Surface(submap_size))
        map_initializer.build_map(self.me, fast, use_beach_tiler, load_tilers, build_gui=self.is_main)
        self.map_initializer = map_initializer
        self.me.build_objects_dict()
        self.collect_path_objects(map_initializer)
        if self.is_main:
            thorpy.add_time_reaction(self.me.e_box, self.func_reac_time)
            ui = gui.Gui(self)


    def collect_path_objects(self, map_initializer):
        self.cobblestone = map_initializer.cobblestone
        self.bridge_h = map_initializer.bridge_h_mapobject
        self.bridge_v = map_initializer.bridge_v_mapobject
        assert self.cobblestone
        assert self.bridge_h
        assert self.bridge_v
        self.bridge = self.bridge_h
        self.road = self.cobblestone

    def add_object(self, coord, obj, quantity=1, rand_relpos=False):
        o = self.me.add_dynamic_object(coord, obj, quantity)
        o.game = self
        if rand_relpos:
            o.randomize_relpos()
        return o

    def get_cell_at(self, chunk, coord):
        neigh = self.me.neigh_maps.get(chunk,None)
        if neigh:
            return self.me.neigh_maps[chunk].lm.get_cell_at(coord[0],coord[1])
        return None

    def add_obj_before_other_if_needed(self, obj, qty, other_names, cell):
        has_other = False
        for o in cell.objects: #ok
            for n in other_names:
                if o.name == n:
                    has_other = True
                    s = self.me.lm.get_current_cell_size()
                    im2, r2 = o.get_current_img_and_rect(s)
                    cell_rect = o.get_current_cell_rect(s)
                    obj.cell = cell
                    obj_rect = obj.get_current_img().get_rect()
                    obj_rect.bottom = r2.bottom + 1
                    obj.cell = None
                    #pos = centercell + relpos*s
                    #<==> relpos = (pos - centercell)/s
                    relpos = (obj_rect.centery - cell_rect.centery) / s
                    obj.min_relpos = [0, relpos]
                    obj.max_relpos = [0, relpos]
                    break
        o = self.add_object(cell.coord, obj, qty, has_other)
        return o


    def get_all_objects_by_str_type(self, str_type):
        d = self.me.objects_dict.get(str_type)
        if d:
            return d.values()
        return []

    def get_map_size(self):
        return self.me.lm.nx, self.me.lm.ny

    def center_cam_on_cell(self, coord):
        """To actually see the result, first draw the map, then display()"""
        self.me.cam.center_on_cell(coord)
        self.recompute_smokes_position()

    def get_object(self, str_type, coord):
        return self.me.get_object(str_type, coord)

##    def check_integrity(self):
##        o1 = self.me.lm.static_objects + self.me.dynamic_objects
##        o2 = []
##        for x in range(self.get_map_size()[0]):
##            for y in range(self.get_map_size()[1]):
##                o2 += self.get_cell_at(x,y).objects
##        for o in o1:
##            o.game = self
##            assert o in o2
##        for o in o2:
##            assert o in o1
##        #o1 contains the same objects as o2
##        od = []
##        for entry in self.me.objects_dict.keys():
##            for o in self.me.objects_dict[entry].values():
##                od.append(o)
####                if not (o in o1):
####                    print(o, o.name, o.str_type, o.cell.coord)
####                    assert o in o1
####        for o in o1:
####            print(o, o.name, o.str_type, o.cell.coord)
####            assert o in od
##        print("The", len(o1), "objects are consistent in memory.")