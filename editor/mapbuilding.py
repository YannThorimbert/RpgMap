import random, pygame, thorpy, os
import RpgMap.thornoise.purepython.noisegen as ng
##import RpgMap.thornoise.numpygen.noisegen as ng
import RpgMap.rendering.tilers.tilemanager as tm
from RpgMap.rendering.tilers.roundtiler import get_round_river
from RpgMap.mapobjects.objects import MapObject
import RpgMap.mapobjects.objects as objs
import RpgMap.mapobjects.distributors as distrib
from RpgMap.editor.mapeditor import MapEditor
from RpgMap.ia.path import BranchAndBoundForMap
from RpgMap.logic import custom
from RpgMap.logic.constants import *
from RpgMap.editor.pathbuilding import add_river_greedy, get_path_orientation


terrain_small = {  "hdeepwater": 0.3, #deep water only below 0.3
                    "hwater": 0.4, #normal water between 0.3 and 0.4
                    "hshore": 0.5, #shore water between 0.4 and 0.5
                    "hsand": 0.6, #and so on...
                    "hgrass": 0.7,
                    "hrock": 0.8,
                    "hthinsnow": 0.9}

terrain_medium = {  "hdeepwater": 0.3,
                    "hwater": 0.4,
                    "hshore": 0.55,
                    "hsand": 0.6,
                    "hgrass": 0.7,
                    "hrock": 0.8,
                    "hthinsnow": 0.9}

terrain_normal = {  "hdeepwater": 0.4, #deep water only below 0.4
                    "hwater": 0.55, #normal water between 0.4 and 0.55
                    "hshore": 0.6, #shore water between 0.55 and 0.6
                    "hsand": 0.62, #and so on...
                    "hgrass": 0.8,
                    "hrock": 0.83,
                    "hthinsnow": 0.9}

terrain_plains = {  "hdeepwater": 0.2, #deep water only below 0.2
                    "hwater": 0.3, #normal water between 0.2 and 0.35
                    "hshore": 0.4, #shore water between 0.3 and 0.4
                    "hsand": 0.48, #and so on...
                    "hgrass": 0.68,
                    "hrock": 0.78,
                    "hthinsnow": 0.9}

terrain_flat = {    "hdeepwater": 0.2, #deep water only below 0.4
                    "hwater": 0.35, #normal water between 0.4 and 0.55
                    "hshore": 0.4, #shore water between 0.55 and 0.6
                    "hsand": 0.42, #and so on...
                    "hgrass": 1.,
                    "hrock": 1.999,
                    "hthinsnow": 1.9999}

VON_NEUMAN = [(-1,0), (1,0), (0,-1), (0,1)]



class MapInitializer:

    def __init__(self, name):
        self.loading_bar = None
        self.name = name #name of the map
        ############ terrain generation:
        self.chunk_size = (128,128) #in number of cells. Put a power of 2 for tilable maps
        self.seed = (1310,14) #Kind of seed. Neighboring chunk give tilable maps.
        self.persistance = 2. #parameter of the random terrain generation.
        self.n_octaves = "max" #parameter of the random terrain generation.
        self.reverse_hmap = False #set to True to reverse height map
        self.colorscale_hmap = None #colorscale to use for the minimap
        ############ graphical options:
        self.zoom_cell_sizes = [32, 16, 8] #size of one cell for the different zoom levels.
        self.nframes = 16 #number of frames per world cycle (impacts memory requirement!)
        self.fps = None #frame per second
        self.menu_width = 200 #width of the right menu in pixels
        ############ material options:
        #cell_radius = cell_size//radius_divider
        # change how "round" look cell transitions
        self.cell_radius_divider = 8
        #path or color of the image of the different materials
        self.water = FN_TERRAIN + "water1.png"
        self.sand = FN_TERRAIN + "sand1.jpg"
        self.grass = FN_TERRAIN + "grass.png"
        self.grass2 = FN_TERRAIN + "grass8.png"
        self.rock = FN_TERRAIN + "rock2.png"
        self.black = (0,0,0)
        self.white = (255,255,255)
        #mixed images - we superimpose different image to make a new one
        #the value indicated correspond
        self.deepwater= 127 #mix water with black : 127 is the alpha of black
        self.mediumwater= 50 #mix water with black : 50 is the alpha of black
        self.shore = 127 #mix sand with water : 127 is the alpha of water
        self.thinsnow = 200 #mix rock with white : 200 is the alpha of white
        #water movement is obtained by using shifts.
        #x-shift is dx_divider and y-shift is dy_divider. Unit is pixel.
        self.dx_divider = 10
        self.dy_divider = 8
        #here we specify at which altitude is each biome
        self.hdeepwater = 0.4 #deep water only below 0.4
        self.hwater = 0.55 #normal water between 0.4 and 0.55
        self.hshore = 0.6 #shore water between 0.55 and 0.6
        self.hsand = 0.62 #and so on...
        self.hgrass = 0.8
        self.hrock = 0.83
        self.hthinsnow = 0.9
        self.hsnow = float("inf")
        #precomputed tiles are used only if load_tilers=True is passed to build_materials()
        self.precomputed_tiles = FN_TERRAIN + "precomputed/"
        #NB : if you want to add your own materials, then you must write your
        #   own version of build_materials function below, and modify the above
        #   parameters accordingly in order to include the additional material
        #   or remove the ones you don't want.
        ############ static objects options:
##        self.static_objects_n_octaves = 4
        self.static_objects_n_octaves = 4
        self.static_objects_persistance = 1.7
        # self.cobble_fn = FN_STRUCTURES + "cobblestone2.png"
        self.cobble_fn = FN_TERRAIN + "dirt1.jpg"
        self.cobble_fn_size = 1.
        self.bridge_h = FN_STRUCTURES + "bridge_h.png"
        self.bridge_h_size = 1.
        self.bridge_v = FN_STRUCTURES + "bridge_v.png"
        self.bridge_v_size = 1.
        #if you want to add objects by yourself, look at add_static_objects(self)
        self.min_road_length = 10
        self.max_road_length = 40
        self.max_number_of_roads = 5
        self.min_river_length = 10
        self.max_number_of_rivers = 5
        self.rounded_river = True
        ############ End of user-defined parameters
        self.user_objects = []
        self._objects = {}
        self.heights = []
        self.seed_static_objects = self.seed
        self.rivers = None
        self.cobble_fnstone = None
        self.bridge_h_mapobject= None
        self.bridge_v_mapobject = None

    def set_terrain_type(self, terrain_type, colorscale):
        for key in terrain_type:
            setattr(self, key, terrain_type[key])
        self.colorscale_hmap = colorscale

    def get_saved_attributes(self):
        attrs = [a for a in self.__dict__.keys() if not a.startswith("_")]
        attrs.sort()
        return attrs

    def get_image(self, me, name):
        value = getattr(self, name)
        if isinstance(value, str):
            return me.load_image(value)
        elif isinstance(value, tuple):
            return me.get_color_image(value)


    def configure_map_editor(self, fps):
        """Set the properties of the map editor"""
        self.fps = fps
        me = MapEditor(self.name)
        me.map_initializer = self
        me.zoom_cell_sizes = self.zoom_cell_sizes
        me.nframes = self.nframes
        me.fps = self.fps
        me.menu_width = self.menu_width
        me.chunk_size = self.chunk_size
        me.seed = self.seed
        me.persistance = self.persistance
        me.n_octaves = self.n_octaves
        me.reverse_hmap = self.reverse_hmap
        me.colorscale_hmap = self.colorscale_hmap
        me.refresh_derived_parameters()
        return me


    def build_materials(self, me, fast, use_beach_tiler, load_tilers):
        """
        <fast> : quality a bit lower if true, loading time a bit faster.
        <use_beach_tiler>: quality much better if true, loading buch slower.
        Requires Numpy !
        <load_tilers> : use precomputed textures from disk. Very slow but needed if
        you don't have Numpy but still want beach_tiler.
        """
        #might be chosen by user:
        #cell_radius = cell_size//radius_divider
        # change how "round" look cell transitions
        cell_radius_divider = 8
        #we load simple images - they can be of any size, they will be resized
        water_img = self.get_image(me, "water")
        sand_img = self.get_image(me, "sand")
        grass_img = self.get_image(me, "grass")
        grass_img2 = self.get_image(me, "grass2")
        rock_img = self.get_image(me, "rock")
        black_img = self.get_image(me, "black")
        white_img = self.get_image(me, "white")
        #mixed images - we superimpose different image to make a new one
        deepwater_img = tm.get_mixed_tiles(water_img, black_img, self.deepwater)
        mediumwater_img = tm.get_mixed_tiles(water_img, black_img, self.mediumwater)
        shore_img = tm.get_mixed_tiles(sand_img, water_img, self.shore) # alpha of water is 127
        thinsnow_img = tm.get_mixed_tiles(rock_img, white_img, self.thinsnow)
        ##river_img = tm.get_mixed_tiles(rock_img, water_img, 200)
        river_img = shore_img
        #water movement is obtained by using a delta-x (dx_divider) and delta-y shifts,
        # here dx_divider = 10 and dy_divider = 8
        #hmax=0.1 means one will find deepwater only below height = 0.1
        ##deepwater = me.add_material("Very deep water", 0.1, deepwater_img, self.dx_divider, self.dy_divider)
        me.add_material("Deep water", self.hdeepwater, mediumwater_img, self.dx_divider, self.dy_divider)
        me.add_material("Water", self.hwater, water_img, self.dx_divider, self.dy_divider)
        me.add_material("Shallow water", self.hshore, shore_img, self.dx_divider, self.dy_divider)
        me.add_material("Sand", self.hsand, sand_img)
        me.add_material("Grass", self.hgrass, grass_img)
        ##me.add_material("Grass", 0.8, grass_img2, id_="Grass2")
        me.add_material("Rock", self.hrock, rock_img)
        me.add_material("Thin snow", self.hthinsnow, thinsnow_img)
        me.add_material("Snow", self.hsnow, white_img)
        #Outside material is mandatory. The only thing you can change is black_img
        outside = me.add_material("outside", -1, black_img)
        #this is the heavier computing part, especially if the maximum zoom is large:
        print("Building material couples")
        if load_tilers:
            load_tilers = self.precomputed_tiles
        me.build_materials(cell_radius_divider, fast=fast,
                            use_beach_tiler=use_beach_tiler,
                            load_tilers=load_tilers)
    ##                        load_tilers=FN_TERRAIN + "precomputed/")
        ##me.save_tilers(FN_TERRAIN + "precomputed/")
        ##import sys;app.quit();pygame.quit();sys.exit();exit()

    def add_object(self, obj_name, x, y, flip=False):
        self.user_objects.append((obj_name, (x,y), flip))


    def add_static_objects(self, me, seed_static):
        #1) We use another hmap to decide where we want trees (or any other object)
        S = len(me.hmap)
        m = ng.generate_terrain(S, n_octaves=self.static_objects_n_octaves,
                                persistance=self.static_objects_persistance,
                                chunk=seed_static)
        ng.normalize(m)
        self.smap = m

        #me.lm is a superimposed map on which we decide to blit some static objects:
        #3) We build the objects that we want.
        # its up to you to decide what should be the size of the object (3rd arg)
        for d in custom.distributions:
            d.build_objects(me)

        #
        cobble = MapObject(me,self.cobble_fn,"cobblestone",self.cobble_fn_size)
        cobble.is_ground = True
        self.cobblestone = cobble
        bridge_h = MapObject(me,self.bridge_h,"bridge",self.bridge_h_size,
                                str_type="bridge_h")
        bridge_h.is_ground = True
        bridge_h.max_relpos = [0., 0.]
        bridge_h.min_relpos = [0., 0.]
        bridge_v = MapObject(me,self.bridge_v,"bridge",self.bridge_v_size,
                                str_type="bridge_v")
        bridge_v.is_ground = True
        bridge_v.max_relpos = [0., 0.]
        bridge_v.min_relpos = [0., 0.]
        self.bridge_h_mapobject = bridge_h
        self.bridge_v_mapobject = bridge_v
        self._objects = {"cobble":cobble, "bridge_h":bridge_h, "bridge_v":bridge_v, "road":cobble}
        for d in custom.distributions:
            for o in d.objects:
                self._objects[o.name] = o

        #4) add the objects via distributors, to add them randomly in a nice way
        for d in custom.distributions:
            distributor = d.get_distributor(me, me.lm, self.smap)
            distributor.distribute_objects(me.lm, exclusive=d.exclusive)

        self.cobbles = [cobble, cobble.flip(True,False),
                    cobble.flip(False,True), cobble.flip(True,True)]
        ############################################################################
        #Here we show how to use the path finder for a given unit of the game
        #Actually, we use it here in order to build cobblestone roads on the map
        me.initialize_rivers()
        costs_materials_road = {name:1. for name in me.materials}
        costs_materials_road["Snow"] = 10. #unit is 10 times slower in snow
        costs_materials_road["Thin snow"] = 2. #twice slower on thin snow...
        costs_materials_road["Sand"] = 2.
##        for name in me.materials:
##            if "water" in name.lower():
##                costs_materials_road[name] = 10
        river_type = me.object_types["river"]
        bush_int_type = self._objects["bush"].int_type
        village_int_type = self._objects["village"].int_type

        costs_objects_road = {  bush_int_type: 2.,
                                cobble.int_type: 0.9,
                                river_type:2.} #unit is 2 times slower in rivers
        #Materials allowed (here we allow water because we add bridges)
        possible_materials_road=list(me.materials)
        for name in me.materials:
            if "water" in name.lower():
                possible_materials_road.remove(name)
        possible_objects_road=[cobble.int_type, bush_int_type,
                                village_int_type, river_type]
        ########################################################################
        #now we build a path for rivers, just like we did with roads.
        costs_materials_river = {name:1. for name in me.materials}
        #Materials allowed (here we allow water because we add bridges)
        possible_materials_river=list(me.materials)
        possible_objects_river=[]
        random.seed(self.seed_static_objects)
        n_roads = 0
        n_rivers = 0
        lm = me.lm
        self.imgs_river = self.build_imgs_river(me)
        material_dict = get_materials_dict(lm)
        self.update_loading_bar("Finding paths for rivers and roads...",0.6)
        for i in range(self.max_number_of_rivers):
            add_river_greedy(me, me.lm,
                            material_dict,
                            self.imgs_river,
                            self.rounded_river,
                            min_length=self.min_river_length)
##        while n_roads < self.max_number_of_roads or n_rivers < self.max_number_of_rivers:
##            if n_rivers < self.max_number_of_rivers:
##                n_rivers += 1
##                self.rivers = add_river_greedy(me, me.lm, material_dict, imgs_river,
##                                    costs_materials_river,
##                                    costs_objects_road,
##                                    possible_materials_river,
##                                    possible_objects_river,
##                                    min_length=self.min_river_length,
##                                    max_length=self.max_river_length)
##            if n_roads < self.max_number_of_roads:
##                n_roads += 1
##                add_random_road(me.lm, me.lm, self.cobbles,
##                                    (bridge_h,bridge_v),
##                                    costs_materials_road,
##                                    costs_objects_road,
##                                    possible_materials_road,
##                                    possible_objects_road,
##                                    min_length=self.min_road_length,
##                                    max_length=self.max_road_length)


    def add_static_objects_neigh(self, me, lm, seed_static):
        #1) We use another hmap to decide where we want trees (or any other object)
        me = lm.me
        S = len(me.hmap)
        m = ng.generate_terrain(S, n_octaves=self.static_objects_n_octaves,
                                persistance=self.static_objects_persistance,
                                chunk=seed_static)
        ng.normalize(m)
        self.smap = m
        #4) add the objects via distributors, to add them randomly in a nice way
        for d in custom.distributions:
            distributor = d.get_distributor(me, lm, self.smap)
            distributor.distribute_objects(lm, exclusive=d.exclusive)

        ############################################################################
        #Here we show how to use the path finder for a given unit of the game
        #Actually, we use it here in order to build cobblestone roads on the map
        costs_materials_road = {name:1. for name in me.materials}
        costs_materials_road["Snow"] = 10. #unit is 10 times slower in snow
        costs_materials_road["Thin snow"] = 2. #twice slower on thin snow...
        costs_materials_road["Sand"] = 2.
        river_type = me.object_types["river"]
        bush_int_type = self._objects["bush"].int_type
        village_int_type = self._objects["village"].int_type

        costs_objects_road = {  bush_int_type: 2.,
                                self.cobblestone.int_type: 0.9,
                                river_type:2.} #unit is 2 times slower in rivers
        #Materials allowed (here we allow water because we add bridges)
        possible_materials_road=list(me.materials)
        for name in me.materials:
            if "water" in name.lower():
                possible_materials_road.remove(name)
        possible_objects_road=[self.cobblestone.int_type, bush_int_type,
                                village_int_type, river_type]
        ########################################################################
        #now we build a path for rivers, just like we did with roads.
        costs_materials_river = {name:1. for name in me.materials}
        #Materials allowed (here we allow water because we add bridges)
        possible_materials_river=list(me.materials)
        possible_objects_river=[]
        random.seed(self.seed_static_objects)
        material_dict = get_materials_dict(lm)
        for i in range(self.max_number_of_rivers):
            add_river_greedy(me, lm,
                            material_dict,
                            self.imgs_river,
                            self.rounded_river,
                            min_length=self.min_river_length)
##                add_random_road(me.lm, me.lm, cobbles,
##                                    (bridge_h,bridge_v),
##                                    costs_materials_road,
##                                    costs_objects_road,
##                                    possible_materials_road,
##                                    possible_objects_road,
##                                    min_length=self.min_road_length,
##                                    max_length=self.max_road_length)

    def add_user_objects(self, me):
        for name,coord,flip in self.user_objects:
            obj = self._objects[name]
            cell = me.lm.get_cell_at(coord[0],coord[1])
            if flip:
                obj = obj.flip()
            obj = obj.add_copy_on_cell(cell, first=True)
            obj.is_static=True
            obj.randomize_relpos()
            #insert at the beginning because it is the last object
            #think e.g. of a wooden bridge over a river. What the unit sees is
            #the wooden bridge
##            me.lm.static_objects.insert(0,obj)
            me.add_static_object(obj)

    def build_neigh(self, me, chunk):
        import time
        a = time.time()
        hmap = me.build_hmap_neigh(chunk) #up to 16%
        b = time.time()
        lm = build_lm_neigh(me, hmap) #takes 20-60% of the time
        c = time.time()
        self.add_static_objects_neigh(me, lm, (chunk[0]+1,chunk[1]+1)) #20%-60%
        d = time.time()
##        self.add_user_objects(me) #pas encore fait
        lm.build_surfaces() #
        e = time.time()
##        sort_objects = True
##        lm.blit_objects(sort=sort_objects) #
##        lm.blit_objects_smart()
        #monitoring
        tot_time = e-a
        steps = [b-a,c-b,d-c,e-d]
        print("Neigh built: ",end="")
        for s in steps:
            print(round(100.*s/tot_time),"% ", end="")
        print()
        return lm

    def init_loading_bar(self):
        screen = thorpy.get_screen()
        screen.fill((255,255,255))
        loading_bar = thorpy.LifeBar.make(" ",
            size=(thorpy.get_screen().get_width()//2,30))
        loading_bar.center(element="screen")
        self.loading_bar = loading_bar


    def build_map(self, me, fast=False, use_beach_tiler=True, load_tilers=False,
                    graphical_load=True, build_gui=True):
        """
        <fast> : quality a bit lower if true, loading time a bit faster.
        <use_beach_tiler>: quality much better if true, loading buch slower.
        Requires Numpy !
        <load_tilers> : use precomputed textures from disk. Very slow but needed if
        you don't have Numpy but still want beach_tiler.
        """
        if graphical_load: #just ignore this - nothing to do with map configuration
            self.update_loading_bar("Building height map...", 0.1)
        build_hmap(me)
        for x,y,h in self.heights:
            me.hmap[x][y] = h
        if graphical_load:
            img = thorpy.get_resized_image(me.original_img_hmap,
                                        thorpy.get_screen().get_size(), max)
            thorpy.get_screen().blit(img, (0,0))
            self.update_loading_bar("Building tilers...",0.2)
        self.build_materials(me, fast, use_beach_tiler, load_tilers)
        self.update_loading_bar("Building map surfaces...",0.3)
        build_lm(me)
        self.update_loading_bar("Adding static objects...",0.4)
        self.add_static_objects(me, (me.seed[0]+1,me.seed[1]+1))
        self.add_user_objects(me)
        #Now that we finished to add objects, we generate the pygame surface
        self.update_loading_bar("Building surfaces", 0.8)
        me.build_surfaces()
        if build_gui:
            me.build_gui_elements()


    def h(self, x,y,h):
        if isinstance(h,str):
            h = getattr(self, "h"+h) - 0.001
        self.heights.append((x,y,h))

    def update_loading_bar(self, text, progress):
        self.loading_bar.set_text(text)
        self.loading_bar.set_life(progress)
        self.loading_bar.blit()
        pygame.display.flip()


    def build_imgs_river(self, me):
        lm = me.lm
        river_img = me.get_material_image("Shallow water")
        imgs_river = {}
        for dx in [-1,0,1]:
            for dy in[-1,0,1]:
                imgs = tm.build_tiles(river_img, lm.cell_sizes,
                                            lm.nframes,
                                            dx*lm.nframes, dy*lm.nframes, #dx, dy
                                            sin=False)
                if self.rounded_river:
                    rd = self.cell_radius_divider
                    if dx>0 and dy>0:
                        corners = ["bottomleft", "topright"]
                    elif dx>0 and dy<0:
                        corners = ["bottomright", "topleft"]
                    elif dx<0 and dy>0:
                        corners = ["bottomright", "topleft"]
                    elif dx<0 and dy<0:
                        corners = ["bottomleft", "topright"]
                    for corner in corners:
                        delta = (dx,dy,corner)
                        imgs_river[delta] = [[] for z in range(len(imgs))]
                        for z in range(len(imgs)):
                            rounded_imgs = []
                            for img in imgs[z]:
                                rounded_imgs.append(get_round_river(rd//2, corner, img))
                            imgs_river[delta][z] = rounded_imgs
                    else:
                        delta = (dx,dy,None)
                        imgs_river[delta] = imgs
                else:
                    delta = (dx,dy,None)
                    imgs_river[delta] = imgs
        return imgs_river


def build_lm(me):
    """Build the logical map corresponding to me's properties"""
    lm = me.build_map() #build a logical map with me's properties
    lm.chunk = (0,0)
    lm.cam = me.cam
    lm.frame_slowness1 = max(1,me.fps//7) #frame will change every k*FPS [s]
    lm.frame_slowness2 = max(1,lm.frame_slowness1 // 2)
    lm.frame_slowness3 = 2 * lm.frame_slowness1
    lm.frame_slowness4 = int(1.1 * lm.frame_slowness1)
    me.set_map(lm) #we attach the map to the editor

def build_lm_neigh(me, hmap):
    """Build the logical map corresponding to me's properties"""
    lm = me.build_neigh(hmap) #build a logical map with me's properties
    lm.frame_slowness1 = max(1,me.fps//7) #frame will change every k*FPS [s]
    lm.frame_slowness2 = max(1,lm.frame_slowness1 // 2)
    lm.frame_slowness3 = 2 * lm.frame_slowness1
    lm.frame_slowness4 = int(1.1 * lm.frame_slowness1)
    return lm

def build_hmap(me):
    """Build a pure height map"""
    hmap = me.build_hmap()
    ##hmap[2][1] = 0.7 #this is how you manually change the height of a given cell
    #Here we build the miniature map image

    img_hmap = ng.build_surface(hmap, me.colorscale_hmap)
    new_img_hmap = pygame.Surface(me.chunk_size)
    new_img_hmap.blit(img_hmap, (0,0))
    img_hmap = new_img_hmap
    me.build_camera(img_hmap)
    return hmap


def add_random_road(lm, layer,
                    cobbles, bridges,
                    costs_materials, costs_objects,
                    possible_materials, possible_objects,
                    min_length,
                    max_length):
    """Computes and draw a random road between two random villages."""
    print("     Building random road...")
    villages = [o for o in layer.static_objects if "village" in o.str_type]
    if not villages:
        return
    v1 = random.choice(villages)
    c1 = find_free_next_to(lm, v1.cell.coord)
    # c1 = v1.cell
    if c1:
        villages_at_right_distance = []
        for v2 in villages:
            if v2 is not v1:
                if min_length <= c1.distance_to(v2.cell) <= max_length:
                    villages_at_right_distance.append(v2)
        if villages_at_right_distance:
            v2 = random.choice(villages_at_right_distance)
            c2 = find_free_next_to(lm, v2.cell.coord)
            # c2 = v2.cell
        else:
            return
        if c2:
            sp = BranchAndBoundForMap(lm, c1, c2,
                                    costs_materials, costs_objects,
                                    possible_materials, possible_objects)
            path = sp.solve()
            draw_road(path, cobbles, bridges, lm)

def get_materials_dict(lm):
    """Build the list of coordinates corresponding to each material"""
    d = {}
    for x in range(lm.nx):
        for y in range(lm.ny):
            mat = lm.cells[x][y].material.name.lower()
            if mat in d:
                d[mat].append((x,y))
            else:
                d[mat] = [(x,y)]
    return d

##def pick_one_cell(md, coord1, materials):
##    for mat in materials:
##        if mat in md:
##            return random.choice(md[mat])



def find_free_next_to(lm, coord):
    ok = []
    for x,y in VON_NEUMAN:
        cell = lm.get_cell_at(coord[0]+x,coord[1]+y)
        if cell:
            if not cell.objects:
                if not cell.unit:
                    ok.append(cell)
    if ok:
        return random.choice(ok)



def draw_path(path, objects, layer):
    """<path> is a list of cells"""
    for cell in path:
        c = random.choice(objects)
        c = c.add_copy_on_cell(cell)
        layer.static_objects.append(c)

def draw_road(path, cobbles, bridges, layer):
    """<path> is a list of cells"""
    for i,cell in enumerate(path):
        already_there = [c.str_type for c in cell.objects]
        is_bridge =  "river" in already_there
        if is_bridge:
            dx,dy = get_path_orientation(i,cell,path)
            if dx != 0:
                c = bridges[0]
            elif dy != 0:
                c = bridges[1]
            else:
                c = random.choice(bridges)
                # raise Exception("Path orientation not expected:",dx,dy)
        else:
            c = random.choice(cobbles)
        if not(c.str_type in already_there):
            c = c.add_copy_on_cell(cell)
            layer.static_objects.append(c)
