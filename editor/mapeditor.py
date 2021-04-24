import math, os
import pygame
from pygame.math import Vector2 as V2
import thorpy
import RpgMap.thornoise.purepython.noisegen as ng
import RpgMap.rendering.tilers.tilemanager as tm
from RpgMap.rendering.mapgrid import LogicalMap
import RpgMap.gui.parameters as guip
import RpgMap.gui.elements as gui
from RpgMap.rendering.camera import Camera
import RpgMap.saveload.io as io
from RpgMap.mapobjects.objects import MapObject
from RpgMap.logic.unit import Unit
from RpgMap.logic.constants import MOUSE_NAV_FACTOR
from RpgMap.rendering.neighmap import NeighMap

def sgn(x):
    if x < 0:
        return -1.
    elif x > 0:
        return 1.
    return 0.

mo = thorpy.Monitor()

def reset_mo():
    mo.reset()

class MapEditor:
##    saved_attrs = ["zoom_cell_sizes", "nframes", "fps", "menu_width",
##                            "max_wanted_minimap_size", "chunk_size", "chunk",
##                            "persistance", "n_octaves","show_grid_lines",
##                            "box_hmap_margin"]

    def __init__(self, name="Unnamed map"):
        self.name = name
        self.screen = thorpy.get_screen()
        self.W, self.H = self.screen.get_size() #self.screen size, wont change
        self.screen_rect = self.screen.get_rect()
        self.hmap = None
        #values below are default values; they can change and
        # self.refresh_derived_parameters() must be called
        self.fps = 80
        self.menu_width = 200
        self.zoom_cell_sizes = None
        self.chunk_size = None
        self.chunk = None
        self.nframes = 16 #number of different tiles for one material (used for moving water)
        self.max_wanted_minimap_size = 128 #in pixels.
        self.show_grid_lines = False
        #
        self.lm = None
        self.cam = None #camera, to be built later
##        self.viewport_rect = None
        self.zoom_level = 0
        self.materials = {}
        self.material_couples = None
        self.dynamic_objects = []
        self.modified_cells = []
        self.object_types = {}
##        self.last_cell_clicked = None
        #
        self.cursor_color = 0 #0 = normal, 1 = select
        self.cursors = None
        self.idx_cursor = 0
        self.img_cursor = None
        self.cursor_slowness = None
        #gui
        self.original_img_hmap = None
        self.e_box = None
        self.cell_info = None
        self.unit_info = None
##        self.misc_info = None
        #
        self.ap = gui.AlertPool()
        self.alert_elements = []
##        self.e_ap_move = gui.get_infoalert_text("To move the map, drag it with", "<LMB>",
##                                        "or hold", "<left shift>", "while moving mouse")
##        self.ap.add_alert_countdown(self.e_ap_move, guip.DELAY_HELP * self.fps)
##        self.alert_elements.append(self.e_ap_move)
        #
        self.map_initializer = None
        self.game = None
        self.objects_dict = {}
        #
        self.neigh_maps = {}
        #
        self.surfaces32 = []
        self.delta_cam = V2()


    def refresh_neigh_maps(self):
        r = self.screen_rect
        xc, yc = self.cam.get_coord_at_pix(r.center)
        delta_c = xc//self.cam.nx, yc//self.cam.ny
        #
        to_remove = []
        #Remove furthest maps
        for dx,dy in self.neigh_maps.keys():
            if abs(dx-delta_c[0]) + abs(dy-delta_c[1]) > 2:
                to_remove.append((dx,dy))
        for delta in to_remove:
            print("*** remove neigh")
            nm = self.neigh_maps.pop(delta)
            surfaces = nm.lm.current_gm.surfaces
            nx = len(surfaces)
            ny = len(surfaces[0])
            nt = len(surfaces[0][0])
            for x in range(nx):
                for y in range(ny):
                    for t in range(nt):
                        s = surfaces[x][y][t]
                        if s:
                            self.surfaces32.append(s)
        #Add nearest maps
        corners = []
        for x in [r.x, r.w]:
            for y in [r.y, r.h]:
                corners.append((x,y))
        for corner in corners:
            xc,yc = self.cam.get_coord_at_pix(corner)
            delta = xc//self.cam.nx, yc//self.cam.ny
            if not (delta in self.neigh_maps):
                self.neigh_maps[delta] = NeighMap(self, delta)
##        print(len(self.neigh_maps))


    def add_to_objects_dict(self, o):
        if o.str_type in self.objects_dict:
            self.objects_dict[o.str_type][o.cell.coord] = o
        else:
            self.objects_dict[o.str_type] = {o.cell.coord:o}

    def add_static_object(self, o):
        self.lm.static_objects.append(o)
        self.add_to_objects_dict(o)

    def remove_static_object(self, o):
        self.lm.static_objects.remove(o)
        self.objects_dict[o.str_type].pop(o.cell.coord)

    def remove_dynamic_object(self, o):
        self.dynamic_objects.remove(o)
        self.objects_dict[o.str_type].pop(o.cell.coord)

    def build_objects_dict(self):
        self.add_lm_to_object_dict(self.lm)
        for o in self.dynamic_objects:
            self.add_to_objects_dict(o)

    def add_lm_to_object_dict(self, lm):
        for o in lm.static_objects:
            self.add_to_objects_dict(o)

    def get_object(self, str_type, coord):
        by_str_type = self.objects_dict.get(str_type)
        if by_str_type:
            return by_str_type.get(coord)

    ############################################################################

    def initialize_rivers(self):
        lm = self.lm
        img_fullsize = self.get_material_image("Shallow water")
        imgs = {}
        for dx in [-1,0,1]:
            for dy in[-1,0,1]:
                imgs = tm.build_tiles(img_fullsize, lm.cell_sizes,
                                                lm.nframes,
                                                dx*lm.nframes, dy*lm.nframes, #dx, dy
                                                sin=False)
                river_obj = MapObject(self, imgs[0], "river", 1.)
                river_obj.is_ground = True
                self.register_object_type(river_obj)

    def register_object_type(self, obj): #map obj.str_type to obj.int_type
        registered = self.object_types.get(obj.str_type)
        if registered is None: #first time we see this object name
            self.object_types[obj.str_type] = obj.int_type
        else:
            if registered != obj.int_type: #conflict
                print("Object types:", self.object_types)
                raise Exception("Object type already exists:", obj.int_type)

    def get_fn(self):
        return self.name.replace(" ","_")+".map"

    def add_gui_element(self, e, insert=False):
        self.e_box.add_element(e, insert)
        thorpy.store(self.e_box)

    def build_gui_elements(self): #worst function ever
        ########################################################################
        if len(self.zoom_cell_sizes) > 1:
            self.e_zoom = thorpy.SliderX.make(self.menu_width//4, (0, 100),
                                                "Zoom (%)", int, initial_value=100)
            def func_reac_zoom(e):
                levels = len(self.zoom_cell_sizes) - 1
                level = int(levels*self.e_zoom.get_value()/self.e_zoom.limvals[1])
                self.set_zoom(levels-level,False)
        ########################################################################
        self.menu_button = thorpy.make_menu_button(force_convert_alpha=True)
        self.cell_info = gui.CellInfo(self, self.menu_rect.inflate((-10,0)).size,
                         self.cell_rect.size, self.draw_no_update, self.menu_button)
        self.unit_info = gui.UnitInfo(self,self.menu_rect.inflate((-10,0)).size,
                         self.cell_rect.size, self.draw_no_update, self.menu_button)
##        self.misc_info = gui.MiscInfo(self.menu_rect.inflate((-10,0)).size)
        ########################################################################
        elements =[ self.cell_info.e,
                    self.unit_info.e,
                    self.menu_button]
        if len(self.zoom_cell_sizes) > 1:
            elements.insert(0, self.e_zoom)
        self.e_box = thorpy.Element.make(elements=elements,
                                        size=self.menu_rect.size)
        self.e_box.set_main_color((200,200,200,160))
        thorpy.store(self.e_box)
        self.e_box.stick_to("screen","right","right")
        ########################################################################
        if len(self.zoom_cell_sizes) > 1:
            reac_zoom = thorpy.Reaction(reacts_to=thorpy.constants.THORPY_EVENT,
                                        reac_func=func_reac_zoom,
                                        event_args={"id":thorpy.constants.EVENT_SLIDE,
                                                    "el":self.e_zoom},
                                        reac_name="zoom slide")
            self.e_box.add_reaction(reac_zoom)
        ########################################################################
        thorpy.add_keydown_reaction(self.e_box, pygame.K_m, reset_mo)
        thorpy.add_keydown_reaction(self.e_box, pygame.K_KP_PLUS,
                                    self.increment_zoom, params={"value":-1},
                                    reac_name="k plus")
        thorpy.add_keydown_reaction(self.e_box, pygame.K_KP_MINUS,
                                    self.increment_zoom, params={"value":1},
                                    reac_name="k minus")
        wheel_reac1 = thorpy.ConstantReaction(pygame.MOUSEBUTTONDOWN,
                                            self.increment_zoom,
                                            {"button":4},
                                            {"value":1})
        wheel_reac2 = thorpy.ConstantReaction(pygame.MOUSEBUTTONDOWN,
                                            self.increment_zoom,
                                            {"button":5},
                                            {"value":-1})
        self.e_box.add_reactions([wheel_reac1, wheel_reac2])
        ########################################################################
        velocity = 0.2
        thorpy.add_keydown_reaction(self.e_box, pygame.K_LEFT,
                                    self.move_cam_and_refresh,
                                    params={"delta":(-velocity,0)},
                                    reac_name="k left")
        thorpy.add_keydown_reaction(self.e_box, pygame.K_RIGHT,
                                    self.move_cam_and_refresh,
                                    params={"delta":(velocity,0)},
                                    reac_name="k right")
        thorpy.add_keydown_reaction(self.e_box, pygame.K_UP,
                                    self.move_cam_and_refresh,
                                    params={"delta":(0,-velocity)},
                                    reac_name="k up")
        thorpy.add_keydown_reaction(self.e_box, pygame.K_DOWN,
                                    self.move_cam_and_refresh,
                                    params={"delta":(0,velocity)},
                                    reac_name="k down")
        ########################################################################
        self.help_box = gui.HelpBox([
        ("Move camera",
            [("To move the map, drag it with", "<LMB>",
                "or hold", "<LEFT SHIFT>", "while moving mouse."),
             ("The minimap on the upper right can be clicked or hold with",
                "<LMB>", "in order to move the camera."),
             ("The","<KEYBOARD ARROWS>",
              "can also be used to scroll the map view.")]),

        ("Zoom",
            [("Use the","zoom slider","or","<NUMPAD +/- >",
              "to change zoom level."),
             ("You can also alternate zoom levels by pressing","<RMB>",".")]),

        ("Miscellaneous",
            [("Press","<g>","to toggle grid lines display.")])
        ])
        thorpy.add_keydown_reaction(self.e_box, pygame.K_g,
                                    self.toggle_show_grid_lines,
                                    reac_name="toggle grid")
        thorpy.add_mousemotion_reaction(self.e_box, self.func_reac_mousemotion,
                                        constant=False)
        thorpy.add_click_reaction(self.e_box, self.func_reac_click,
                                    constant=False)
        thorpy.add_unclick_reaction(self.e_box, self.func_reac_unclick,
                                    constant=False)


##
##
##    e_hmap.add_reaction(thorpy.Reaction(pygame.MOUSEMOTION,
##                                            self.func_reac_mousemotion))
##        e_hmap.add_reaction(thorpy.Reaction(pygame.MOUSEBUTTONDOWN,
##                                            self.func_reac_click))
##        e_hmap.add_reaction(thorpy.Reaction(pygame.MOUSEBUTTONUP,
##                                            self.func_reac_unclick))


    def toggle_show_grid_lines(self):
            self.show_grid_lines = not(self.show_grid_lines)


    def build_map(self):
        outsides = self.materials["outside"].imgs
        self.lm = LogicalMap(self.hmap, self.material_couples,
                             outsides, self.chunk_size)
        self.lm.me = self
        return self.lm

    def build_neigh(self, hmap):
        outsides = self.materials["outside"].imgs
        lm = LogicalMap(hmap, self.material_couples, outsides, self.chunk_size)
        lm.me = self
        return lm

    def set_map(self, logical_map):
        self.cam.set_map_data(logical_map)


    def build_camera(self, img_hmap):
        self.original_img_hmap = img_hmap
        cam = Camera()
        self.ap.cam = cam
        cam.me = self
        for level in range(len(self.zoom_cell_sizes)):
            self.zoom_level = level
            self.refresh_derived_parameters()
            cam.set_parameters(self.chunk_size, self.cell_size)
        self.zoom_level = 0
        self.refresh_derived_parameters()
        cam.set_parameters(self.chunk_size, self.cell_size)
        self.cam = cam

    def set_key_scroll_velocity(self, velnorm):
        for name in ["left", "right", "up", "down"]:
            name = "k "+name
            value = self.e_box.get_reaction(name).params["delta"]
            value = sgn(value) * velnorm
            self.e_box.get_reaction(name).params["delta"] = value


    def build_surfaces(self, sort_objects=True):
        print("***************************")
        self.lm.build_surfaces() #build surfaces attribute of graphical maps
##        self.lm.build_surfaces_fast()
        self.lm.blit_objects(sort=sort_objects) #blit objs on graphical maps
        ########################################################################
        cursors_n = gui.get_cursors(self.cell_rect.inflate((2,2)),
                                        guip.CURSOR_COLOR_NORMAL)
        cursors_s = gui.get_cursors(self.cell_rect.inflate((2,2)),
                                        guip.CURSOR_COLOR_SELECT)
        self.cursors = [cursors_n, cursors_s]
        self.idx_cursor = 0
        self.img_cursor = self.cursors[self.cursor_color][self.idx_cursor]
        self.cursor_slowness = int(0.3*self.fps)

    def build_cell_graphics(self, cellbase): #blit_objects doit blitter que sur la cellule qui a change !!!!
        xc,yc = cellbase.coord
        static_objects_ground = {}
        static_objects_not_ground = {}
        cells_to_refresh = []
        for x in range(xc-2,xc+3):
            for y in range(yc-2,yc+3):
                static_objects_ground[(x,y)] = []
                static_objects_not_ground[(x,y)] = []
                cell = self.lm.get_cell_at(x,y)
                if cell:
                    dx, dy = abs(xc-x), abs(yc-y)
                    if dx < 2 and dy < 2:
                        cells_to_refresh.append(cell)
                        self.lm.blit_material_of_cell(cell)
                    for o in self.lm.static_objects:
                        if o.cell is cell:
                            if o.is_ground:
                                static_objects_ground[(x,y)].append(o)
                            else:
                                static_objects_not_ground[(x,y)].append(o)
        #blit ground
        for x in range(xc-2,xc+3):
            for y in range(yc-2,yc+3):
                coord = (x,y)
                if coord in static_objects_ground:
                    objs = static_objects_ground[(x,y)]
                    if objs:
                        self.lm.blit_objects_only_on_cells(objs, cells_to_refresh)
        #blit not ground
        for x in range(xc-2,xc+3):
            for y in range(yc-2,yc+3):
                coord = (x,y)
                if coord in static_objects_not_ground:
                    objs = static_objects_not_ground[(x,y)]
                    if objs:
                        self.lm.blit_objects_only_on_cells(objs, cells_to_refresh)


    def set_zoom(self, level, refresh_slider=True):
        center_before = self.cam.nx//2, self.cam.ny//2
        self.zoom_level = level
        self.refresh_derived_parameters()
        self.cam.set_parameters(self.chunk_size,
                            self.cell_size)
        self.lm.set_zoom(level)
        self.cam.reinit_pos()
        self.move_cam_and_refresh((center_before[0]-self.cam.nx//2,
                                    center_before[1]-self.cam.ny//2))
        if refresh_slider:
            n = len(self.zoom_cell_sizes) - 1
            if n > 0:
                newval = self.e_zoom.limvals[1]*(1 - float(level)/n)
                self.e_zoom.set_value(int(newval))
        #cursor
        cursors_n = gui.get_cursors(self.cell_rect.inflate((2,2)),
                                        guip.CURSOR_COLOR_NORMAL)
        cursors_s = gui.get_cursors(self.cell_rect.inflate((2,2)),
                                        guip.CURSOR_COLOR_SELECT)
        self.cursors = [cursors_n, cursors_s]
        self.idx_cursor = 0
        self.img_cursor = self.cursors[self.cursor_color][self.idx_cursor]
        #
        self.game.recompute_smokes_position()
        self.unblit_map()
        self.draw_no_update()
        #
        for nm in self.neigh_maps.values():
            nm.cam.set_parameters(self.chunk_size, self.cell_size)
            nm.lm.set_zoom(level)


    def increment_zoom(self, value):
        self.zoom_level += value
        self.zoom_level %= len(self.zoom_cell_sizes)
        self.set_zoom(self.zoom_level)

    def update_cell_info(self):
        mousepos = pygame.mouse.get_pos()
        cell = self.cam.get_cell_at_pix(mousepos)
        if cell:
            rcursor = self.img_cursor.get_rect()
            rcursor.center = self.cam.get_rect_at_pix(mousepos).center
            self.screen.blit(self.img_cursor, rcursor)
            if self.cell_info.cell is not cell:
                self.cell_info.update_e(cell)
            self.unit_info.update_e(cell.unit)
            if cell.unit:
                self.cursor_color = 1
            else:
                if self.get_object("village", cell.coord):
                    self.cursor_color = 1
                else:
                    self.cursor_color = 0
            self.img_cursor = self.cursors[self.cursor_color][self.idx_cursor]
    ##        if cell.objects:
    ##            print(cell.objects)

    def unblit_map(self):
        rect = self.cam.get_visible_map_rect()
        pygame.draw.rect(self.screen, (0,0,0), rect)


    def draw_as_neigh(self, neigh_map):
        #blit terrain + static objects
        neigh_map.cam.draw_map(self.screen, self.show_grid_lines)
        #blit cursor
##        self.cam.draw_rmouse(self.screen, self.box_hmap.get_rect())
        #blit dynamic objects
        neigh_map.cam.draw_objects(self.screen, self.dynamic_objects, draw_ui=False)
        #blit smoke effects
##        self.game.refresh_smokes()
        #update right pane
##        self.update_cell_info()#xxxx
        #blit right pane and draw rect on minimap
##        self.e_box.blit()
        #blit cursor
##        self.cam.draw_rmouse(self.screen, self.box_hmap.get_rect())
##        pygame.draw.rect(self.screen, (255,255,255), self.cam.rmouse, 1)
        #draw border
##        rect = self.cam.get_visible_map_rect()
##        pygame.draw.rect(self.screen, (255,255,0), rect, 3)


    def draw(self):
        #blit map frame
        mo.append("a")
        self.screen.fill((0,0,0))
        mo.append("b")
        #blit map
##        self.cam.draw_map(self.screen, self.show_grid_lines)
        #
        for delta, nm in self.neigh_maps.items():
            dx,dy = delta
            nm.lm.current_x = self.lm.current_x - dx*self.lm.nx
            nm.lm.current_y = self.lm.current_y - dy*self.lm.ny
            nm.cam.pos_cells.x = self.cam.pos_cells.x
            nm.cam.pos_cells.y = self.cam.pos_cells.y
            self.draw_as_neigh(nm)
        mo.append("c")
        #draw border
        rect = self.cam.get_visible_map_rect()
        pygame.draw.rect(self.screen, (255,0,0), rect, 3)
        mo.append("d")
        #
        #blit cursor
##        self.cam.draw_rmouse(self.screen, self.box_hmap.get_rect())
        #blit objects
        self.cam.draw_objects(self.screen, self.dynamic_objects, True)
        mo.append("e")
        #blit smoke effects
        self.game.refresh_smokes()
        #update right pane
        self.update_cell_info()
        #blit right pane and draw rect on minimap
        self.e_box.blit()
        self.delta_cam = V2()
        #blit cursor
##        self.cam.draw_rmouse(self.screen, self.box_hmap.get_rect())
##        pygame.draw.rect(self.screen, (255,255,255), self.cam.rmouse, 1)
        mo.append("f")
##        if self.game.t%100 == 0:
##            mo.show(rnd=2)
##            print()



    def draw_no_update(self):
        #blit map frame
        self.screen.fill((0,0,0))
        #blit map
        self.cam.draw_map(self.screen, self.show_grid_lines)
        #blit objects
        self.cam.draw_objects(self.screen, self.dynamic_objects, True)
        #blit smoke effects
        self.game.refresh_smokes()
        #blit right pane and draw rect on minimap
        self.e_box.blit()
##        pygame.draw.rect(self.screen, (255,255,255), self.cam.rmouse, 1)
##        self.cam.draw_rmouse(self.screen, self.box_hmap.get_rect())

    def func_reac_time(self):
        for o in self.dynamic_objects:
            o.refresh_translation_animation()
        self.process_mouse_navigation()
        self.draw() #most of the time is spent here
        self.ap.refresh()
        self.ap.draw(self.screen, 20,20)
        #
        self.lm.next_frame()
        if self.lm.tot_time%self.cursor_slowness == 0:
            self.idx_cursor = (self.idx_cursor+1)%len(self.cursors[0])
            self.img_cursor = self.cursors[self.cursor_color][self.idx_cursor]
        #
        for nm in self.neigh_maps.values():
            nm.lm.next_frame()



    def func_reac_click(self, e):
        pass
##        if e.button == 1: #left click
##            if self.box_hmap.get_rect().collidepoint(e.pos):
##                self.cam.center_on(e.pos)
####            elif pygame.key.get_mods() & pygame.KMOD_LCTRL:
####                self.increment_zoom(1)
##        elif e.button == 3: #right click
##            pass


    def func_reac_unclick(self, e):
        cell = self.cam.get_cell_at_pix(e.pos)
        # if e.button == 1: #left click
        #     pass
        if e.button == 3: #right click
            #1. undraw destinations if necessary
            mm = bool(self.cam.ui_manager.destinations_mousemotion)
            lmb = bool(self.cam.ui_manager.destinations_lmb)
            su = self.cam.ui_manager.selected_unit
            if mm or lmb or su:
                self.cam.ui_manager.destinations_mousemotion = []
                self.cam.ui_manager.destinations_lmb = []
                self.cam.ui_manager.selected_unit = None
                self.draw_no_update()
                pygame.display.flip()
            if not lmb: #2. display infos
                can_unit = self.unit_info.can_be_launched(cell, self)
                can_cell = self.cell_info.can_be_launched(cell, self)
                map_rect = self.cam.get_visible_map_rect()
                if can_unit:
                    self.unit_info.last_cell_clicked = cell
                    self.unit_info.launch_em(cell, e.pos, map_rect)
                elif can_cell:
                    self.cell_info.last_cell_clicked = cell
                    self.cell_info.launch_em(cell, e.pos, map_rect)
                self.cell_info.last_cell_clicked = None
                self.cell_info.launched = False
##                self.unit_info.launched = False
            self.unit_info.last_cell_clicked = None

    def func_reac_mousemotion(self, e):
    ##    if pygame.key.get_mods() & pygame.KMOD_CTRL:
        if pygame.mouse.get_pressed()[0]:
            delta = -V2(e.rel)#/self.cam.cell_rect.w #assuming square cells
            self.move_cam_and_refresh(delta)
            self.cell_info.last_cell_clicked = self.cam.get_cell_at_pix(e.pos)
            for e in self.alert_elements:
                self.ap.add_alert_countdown(e, guip.DELAY_HELP * self.fps)

##    xx plutot a faire au func time ??? TOUT ca, grace a delta_cam = V2(x,y)
    def move_cam_and_refresh(self, delta):
        self.cam.move(delta)
        self.delta_cam += delta
        self.cam.refresh_gm_pos()
        self.refresh_neigh_maps()

    def add_unit(self, coord, obj, quantity=None):
        cell = self.lm.get_cell_at(coord[0],coord[1])
        assert cell
        obj_added = obj.add_unit_on_cell(cell)
        if quantity is not None:
            obj_added.quantity = quantity
        self.dynamic_objects.append(obj_added)
        self.add_to_objects_dict(obj_added)
        return obj_added

    def add_dynamic_object(self, coord, obj, quantity=None): #le nom est mal copie qqpart !!!!
        cell = self.lm.get_cell_at(coord[0], coord[1])
        assert cell
        obj_added = obj.add_dynamic_object_on_cell(cell)
        if quantity is not None:
            obj_added.quantity = quantity
        self.dynamic_objects.append(obj_added)
        self.add_to_objects_dict(obj_added)
        return obj_added

    def process_mouse_navigation(self): #cam can move even with no mousemotion!
        if pygame.key.get_mods() & pygame.KMOD_LSHIFT:
            pos = pygame.mouse.get_pos()
            center_of_map_layout = self.W//2, self.H//2
            d = V2(pos) - center_of_map_layout
            if d != (0,0):
                intensity = 1e-6*d.length_squared()**1.5
                if intensity > 1.:
                    intensity = 1.
                d.scale_to_length(intensity)
                #comment out if map is limited in space:
##                marginy = -2
##                marginx = -5
##                nx_displayable = self.W // self.cell_size
##                ny_displayable = self.H // self.cell_size
##                if self.cam.pos_cells.x + nx_displayable + marginx > self.cam.nx and d.x > 0:
##                    d.x = 0
##                if self.cam.pos_cells.x - marginy < 0 and d.x < 0:
##                    d.x = 0
##                if self.cam.pos_cells.y + ny_displayable + marginx > self.cam.ny and d.y > 0:
##                    d.y = 0
##                elif self.cam.pos_cells.y - marginy < 0 and d.y < 0:
##                    d.y = 0
                delta = d*MOUSE_NAV_FACTOR
                self.cam.move(delta)
                self.delta_cam += delta
                self.cam.refresh_gm_pos()
                for e in self.alert_elements:
                    self.ap.add_alert_countdown(e, guip.DELAY_HELP * self.fps)
                self.refresh_neigh_maps()

    def load_image(self, fn):
        img = thorpy.load_image(fn)
        return pygame.transform.smoothscale(img, (self.zoom_cell_sizes[0],)*2)

    def get_material_image(self, material, scale=0, frame=0):
        return self.materials[material].imgs[scale][frame]

    def get_color_image(self, color):
        surface = pygame.Surface((self.zoom_cell_sizes[0],)*2)
        surface.fill(color)
        return surface

    def refresh_derived_parameters(self):
        self.cell_size = self.zoom_cell_sizes[self.zoom_level]
        self.cell_rect = pygame.Rect(0,0,self.cell_size,self.cell_size)
        self.menu_size = (self.menu_width, self.H)
        self.menu_rect = pygame.Rect((0,0),self.menu_size)
        self.menu_rect.right = self.W
##        self.viewport_rect = pygame.Rect((0,0),(self.menu_rect.left,
##                                                self.menu_rect.bottom))

    def build_tiles(self, img_full_size, dx_divider=0, dy_divider=0):
        return tm.build_tiles(img_full_size, self.zoom_cell_sizes, self.nframes,
                                dx_divider, dy_divider)

    def add_material(self, name, hmax, img_fullsize, dx_divider=0, dy_divider=0,
                     id_=None):
        static = dx_divider == 0 and dy_divider == 0 or self.nframes == 1
        imgs = self.build_tiles(img_fullsize, dx_divider, dy_divider)
        if id_ is None:
            id_ = name
        self.materials[id_] = tm.Material(name, hmax, imgs, static)

    def build_materials(self, cell_radius_divider, fast=False,
                        use_beach_tiler=True, load_tilers=True):
        try:
            from pygame import surfarray
            use_beach_tiler = use_beach_tiler
        except:
            use_beach_tiler = False
        if not use_beach_tiler or load_tilers:
            fast = True
        materials = list(self.materials.values())
        self.material_couples = tm.get_material_couples(materials,
                                                        cell_radius_divider,
                                                        fast,
                                                        use_beach_tiler,
                                                        load_tilers)

    def build_hmap(self):
        if self.n_octaves == "auto" or self.n_octaves == "max":
            self.n_octaves = None
        M = max(self.chunk_size)
        power = int(math.log2(M))
        if 2**power < M:
            power += 1
        S = int(2**power)
        hmap = ng.generate_terrain(S, self.n_octaves, self.chunk, self.persistance)
        hmax = 3.5
        hmin = 0.5
        for x in range(self.chunk_size[0]):
            for y in range(self.chunk_size[1]):
                h = hmap[x][y] - hmin
                h /= (hmax-hmin)
                hmap[x][y] = h
                if hmap[x][y] < 0: hmap[x][y] = 0
                elif hmap[x][y] > 1: hmap[x][y] = 1
##        ng.normalize(hmap)
        if self.reverse_hmap:
            ng.apply(hmap, lambda x:1.-x)
        self.hmap = hmap
        return hmap


    def build_hmap_neigh(self, chunk):
        if self.n_octaves == "auto" or self.n_octaves == "max":
            self.n_octaves = None
        M = max(self.chunk_size)
        power = int(math.log2(M))
        if 2**power < M:
            power += 1
        S = int(2**power)
        hmap = ng.generate_terrain(S, self.n_octaves, chunk, self.persistance)
        hmax = 3.5
        hmin = 0.5
        for x in range(self.chunk_size[0]):
            for y in range(self.chunk_size[1]):
                h = hmap[x][y] - hmin
                h /= (hmax-hmin)
                hmap[x][y] = h
                if hmap[x][y] < 0: hmap[x][y] = 0
                elif hmap[x][y] > 1: hmap[x][y] = 1
##        ng.normalize(hmap)
        if self.reverse_hmap:
            ng.apply(hmap, lambda x:1.-x)
        return hmap

##    def to_file(self, fn):
##        print("Saving map to",fn)
##        f = open(fn, "wb")
##        io.to_file(self, f)
##        for obj in self.dynamic_objects:
##            io.to_file(obj, f)
##        f.close()
##
##    def from_file(self, fn):
##        print("Loading map from",fn)
##        loaded = io.from_file(self, fn)
##        self.refresh_derived_parameters()
##        return loaded


    def save_tilers(self, base_fn):
        """Save builded tilers as png"""
        for i,couple in enumerate(self.material_couples):
            print("Writing to disk couple", i)
            if couple.static:
                frames = [0]
            else:
                frames = range(self.nframes)
            for n in frames:
                for type_ in couple.tilers[0][0].imgs:
                    name = "_".join([str(i),str(n),str(type_)])+".png"
                    pygame.image.save(couple.tilers[0][n].imgs[type_],
                                        os.path.join(base_fn,name))

    def get_hmap_img(self, size):
##        if not self.hmap:
        hmap = self.build_hmap()
        img_hmap = ng.build_surface(self.hmap, self.colorscale_hmap)
        new_img_hmap = pygame.Surface(self.chunk_size)
        new_img_hmap.blit(img_hmap, (0,0))
##        w = int(0.2*self.chunk_size[0]*self.cell_size)
##        h = int(0.2*self.chunk_size[1]*self.cell_size)
        w,h = size
        img = pygame.transform.scale(new_img_hmap, (w,h))
        return img

    def extract_img(self, cell):
        img = pygame.Surface((self.cell_size,)*2)
        img.blit(self.screen, (0,0), self.cam.get_rect_at_coord(cell.coord))
        return img
##        new_img = cell.get_static_img_at_zoom(0)
##        cell_size = self.cell_size
##        for o in cell.objects:
##            if not o.is_static:
##                if not isinstance(o, Unit):
##                    new_img.blit(o.imgs_z_t[0][0], o.get_relative_pos(cell_size))
##        return new_img


    def get_local_coord(self, xy):
        dchunk = (xy[0]//self.lm.nx, xy[1]//self.lm.ny)
        x = xy[0] - dchunk[0]*self.lm.nx
        y = xy[1] - dchunk[1]*self.lm.ny
        return (x,y), dchunk

    def get_cell_at_coord(self, xy):
        dchunk = (xy[0]//self.lm.nx, xy[1]//self.lm.ny)
        nm = self.neigh_maps.get(dchunk, None)
        if nm:
            x = xy[0] - dchunk[0]*self.lm.nx
            y = xy[1] - dchunk[1]*self.lm.ny
            return nm.lm[x,y]
