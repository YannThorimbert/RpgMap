import random, os
import pygame
import thorpy
import RpgMap.logic.constants as const



def sgn(x):
    if x < 0:
        return -1
    elif x > 0:
        return 1




class MapObject:
    current_id = 1

    @staticmethod
    def get_saved_attributes():
        return ["name", "quantity", "fns", "factor", "new_type", "relpos", #put new type ?
                "build", "vel", "_refresh_frame_type", "can_interact",
                "is_ground", "always_drawn_last", "str_type"]

    def __init__(self, editor, fns, name="", factor=1., relpos=(0,0), build=True,
                 new_type=True, str_type=None):
        """<factor> : size factor.
        Object that looks the same at each frame"""
        self.editor = editor
        self.lm = editor.lm
        ref_size = editor.zoom_cell_sizes[0]
        self.frame_imgs = []
        self.original_imgs = []
        if isinstance(fns, str):
            fns = [fns]
        self.fns = fns
        thing = None
        for thing in fns:
            if thing:
                if isinstance(thing,str):
                    img = thorpy.load_image(thing, colorkey=(255,255,255))
                else:
                    img = thing
                img = thorpy.get_resized_image(img, (factor*ref_size,)*2)
            else:
                img = None
            self.frame_imgs.append(img)
            self.original_imgs.append(img)
        self.nframes = len(self.original_imgs)
        self.factor = factor
        self.relpos = [0,0]
        self.imgs_z_t = None
        self.cell = None
        self.name = name
        self.str_type = name if str_type is None else str_type
        self.ncopies = 0
        self.min_relpos = [-0.4, -0.4]
        self.max_relpos = [0.4,   0.4]
        self.quantity = 1 #not necessarily 1 for units
        self.build = build
        if build and thing:
            # print("BUILDING", self.name, self.fns)
            self.build_imgs()
        self.new_type = new_type
        if new_type: #then detect type
            already = self.editor.object_types.get(self.str_type)
            if already:
                self.int_type = already
            else:
                self.int_type = MapObject.current_id
                MapObject.current_id += 1
                self.editor.register_object_type(self)
        else: #will probably be set within copy() method
            self.int_type = None
        self.anim_path = None
        self.vel = 0.1
        self.get_current_frame = None
        self._refresh_frame_type = 1
        self.set_frame_refresh_type(self._refresh_frame_type)
        self.is_ground = False #always drawn first
        self.can_interact = False
        self.always_drawn_last = False
        self.is_static = False
        self.hide = False
        self.game = None
        self.blit_on_gm = None
        self.blit_on_gm_border = None

    def get_cell_coord(self):
        return self.cell.coord

    def ypos(self):
        h = self.original_imgs[0].get_size()[1]
        s = self.editor.zoom_cell_sizes[0]
        return self.cell.coord[1]  + 0.5*h/s + self.relpos[1]

    def randomize_relpos(self):
        self.relpos[0] = self.min_relpos[0] +\
                         random.random()*(self.max_relpos[0]-self.min_relpos[0])
        self.relpos[1] = self.min_relpos[1] +\
                         random.random()*(self.max_relpos[1]-self.min_relpos[1])

    def copy(self):
        """The copy references the same images as the original !"""
        self.ncopies += 1
        obj = MapObject(self.editor, [""], self.name, self.factor,
                        list(self.relpos), new_type=False, str_type=self.str_type)
        obj.lm = self.lm
        obj.original_imgs = self.original_imgs
        obj.nframes = self.nframes
        obj.imgs_z_t = self.imgs_z_t
        obj.min_relpos = list(self.min_relpos)
        obj.max_relpos = list(self.max_relpos)
        obj.relpos = list(self.relpos)
        obj.int_type = self.int_type
        obj.quantity = self.quantity
        obj.fns = self.fns
        obj.vel = self.vel
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.is_ground = self.is_ground
        obj.always_drawn_last = self.always_drawn_last
        obj.can_interact = self.can_interact
        return obj

    def deep_copy(self):
        obj = MapObject(self.editor, [""], self.name, self.factor,
                        list(self.relpos), new_type=False, str_type=self.str_type)
        obj.quantity = self.quantity
        obj.fns = self.fns
        obj.original_imgs = [i.copy() for i in self.original_imgs]
        obj.nframes = len(obj.original_imgs)
        obj.imgs_z_t = []
        for frame in range(len(self.imgs_z_t)):
            obj.imgs_z_t.append([])
            for scale in range(len(self.imgs_z_t[frame])):
                obj.imgs_z_t[frame].append(self.imgs_z_t[frame][scale].copy())
##        for imgs in self.imgs_z_t:
##            obj.imgs_z_t = [i.copy() for i in imgs]
        obj.min_relpos = list(self.min_relpos)
        obj.max_relpos = list(self.max_relpos)
        obj.relpos = list(self.relpos)
        obj.int_type = self.int_type
        obj.vel = self.vel
        obj.set_frame_refresh_type(self._refresh_frame_type)
        obj.is_ground = self.is_ground
        obj.always_drawn_last = self.always_drawn_last
        obj.can_interact = self.can_interact
        return obj


    def flip(self, x=True, y=False):
        obj = self.deep_copy()
        obj.original_imgs = [pygame.transform.flip(i, x, y) for i in obj.original_imgs]
        for frame in range(len(obj.imgs_z_t)):
            for scale in range(len(obj.imgs_z_t[frame])):
                obj.imgs_z_t[frame][scale] = pygame.transform.flip(obj.imgs_z_t[frame][scale], x, y)
        return obj

    def add_copy_on_cell(self, cell, first=False):
        copy = self.copy()
        copy.cell = cell
        if first:
            cell.objects.insert(0,copy)
        else:
            cell.objects.append(copy)
        self.editor.register_object_type(self)
        return copy

    def add_unit_on_cell(self, cell):
        assert cell.unit is None
        copy = self.copy()
        copy.cell = cell
        cell.objects.append(copy)
        cell.unit = copy
        return copy

    def add_dynamic_object_on_cell(self, cell):
        copy = self.copy()
        copy.cell = cell
        cell.objects.append(copy)
        self.editor.register_object_type(self)
        return copy

    def remove_from_cell_objects(self):
        self.cell.objects.remove(self)
        if self is self.cell.unit:
            self.cell.unit = None

    def remove_from_map(self):
        me = self.lm.me
        self.remove_from_cell_objects()
        is_bridge = "bridge_" in self.str_type
        if is_bridge and not(self in me.dynamic_objects):
            self.is_static = True
        if self.is_static:# or self.name=="bridge":
            print("Removing static object...")
            if self in me.lm.static_objects:
                me.remove_static_object(self.lm, self)
            me.build_cell_graphics(self.cell)
        elif is_bridge:
            me.dynamic_objects.remove(self)
        else:
            me.remove_dynamic_object(self)

    def move_to_cell(self, dest_cell):
##        assert dest_cell.unit is None
        #remove from old cell
        self.game.me.objects_dict[self.str_type].pop(self.cell.coord)
        self.cell.objects.remove(self)
        self.cell.unit = None
        #go to new cell
        dest_cell.unit = self
        dest_cell.objects.append(self)
        self.cell = dest_cell
        self.game.me.add_to_objects_dict(self)
##        v = self.game.get_object("village", self.cell.coord)
##        if v:
##            s = self.editor.lm.get_current_cell_size()
##            v_bottom_rect = v.get_lowest_rect(s)
##            v_cell_rect = v.get_current_cell_rect(s)
##            self_bottom_rect = self.get_lowest_rect(s)
##            self_bottom_rect.bottom = v_bottom_rect.bottom - 5 #wanted position
##            #pos = centercell + relpos*s
##            #<==> relpos = (pos - centercell)/s
##            relpos = (self_bottom_rect.centery - v_cell_rect.centery) / s
##            self.relpos[1] = relpos

    def move_to_cell_occupied(self, dest_cell): #juste empecher l'arrive sur une cellule occupee
##        assert dest_cell.unit is None
        #remove from old cell
        #1. remove from objects_dict only if departure cell
        od = self.game.me.objects_dict[self.str_type]
        if self.cell.coord in od:
            if od[self.cell.coord] is self:
                self.game.me.objects_dict[self.str_type].pop(self.cell.coord)
        #in any case remove from cell's objects
        self.cell.objects.remove(self)
        if self.cell.unit is self: #only for departure cell
            self.cell.unit = None
        #go to new cell
##        dest_cell.unit = self
        dest_cell.objects.append(self)
        self.cell = dest_cell
##        self.game.me.add_to_objects_dict(self)

    def add_to_final_dest(self, dest_cell):
        print("FINAL DEST")
        dest_cell.unit = self
        self.game.me.add_to_objects_dict(self)

    def move_to_cell_animated(self, path):
        self.anim_path = path

    def refresh_translation_animation(self):
        if self.anim_path:
            x0,y0 = self.cell.coord
            xf,yf = self.anim_path[0]
            dx, dy = xf-x0, yf-y0
            # assert not(dx!=0 and dy!=0)
            if dx != 0:
                sign = sgn(dx)
                self.relpos[0] += self.vel * sign
                if abs(self.relpos[0]) > 1.: #then the object change its cell
                    self.move_to_cell_occupied(self.lm.get_cell_at(x0+sign,y0))
                    if sign > 0:
                        self.relpos[0] = 1. - self.relpos[0]
                    else:
                        self.relpos[0] = 1. + self.relpos[0]
                    self.anim_path.pop(0)
                    if not self.anim_path:
                        self.relpos[0] = 0.
                return sign, 0
            elif dy != 0:
                sign = sgn(dy)
                self.relpos[1] += self.vel * sign
                if abs(self.relpos[1]) > 1.: #then the object change its cell
                    self.move_to_cell_occupied(self.lm.get_cell_at(x0,y0+sign))
                    if sign > 0:
                        self.relpos[1] = 1. - self.relpos[1]
                    else:
                        self.relpos[1] = 1. + self.relpos[1]
                    self.anim_path.pop(0)
                    if not self.anim_path:
                        self.relpos[1] = 0.
                return 0, sign
        if self.anim_path == []:
            self.add_to_final_dest(self.lm.get_cell_at(self.cell.coord[0],self.cell.coord[1]))
            self.anim_path = None
        return 0, 0




##    def build_imgs(self):
##        self.imgs_z_t = [] #list of list of images - idx0:scale, idx1:frame
##        for img in self.original_imgs: #loop over frames
##            W,H = img.get_size()
##            w0 = float(self.editor.zoom_cell_sizes[0])
##            imgs = []
##            for w in self.editor.zoom_cell_sizes: #loop over sizes
##                factor = w/w0
##                zoom_size = (int(factor*W), int(factor*H))
##                img = pygame.transform.scale(img, zoom_size)
##                imgs.append(img)
##            self.imgs_z_t.append(imgs)

    def build_imgs(self):
        self.build = True
        self.imgs_z_t = [] #list of list of images - idx0:scale, idx1:frame
        for w in self.editor.zoom_cell_sizes: #loop over sizes
            imgs = []
            for img in self.original_imgs: #loop over frames
                W,H = img.get_size()
                w0 = float(self.editor.zoom_cell_sizes[0])
                factor = w/w0
                zoom_size = (int(factor*W), int(factor*H))
                img = pygame.transform.scale(img, zoom_size)
                imgs.append(img)
            self.imgs_z_t.append(imgs)

##    def _get_current_frame0(self):
##        return self.cell.lm.t%self.nframes #t is already a modulo ! dont use

    def _get_current_frame1(self): #associated to normal
        return self.cell.lm.t1%self.nframes

    def _get_current_frame2(self): #associated to fast
        return self.cell.lm.t2%self.nframes

    def _get_current_frame3(self): #associated to slow
        return self.cell.lm.t3%self.nframes

    def _get_current_frame4(self): #associated to midslow
        return self.cell.lm.t4%self.nframes

##    def _get_map_time1(self):
##        return self.cell.lm.t

    def _get_map_time1(self):
        return self.cell.lm.t1

    def _get_map_time2(self): #associated to fast
        return self.cell.lm.t2

    def _get_map_time3(self): #associated to slow
        return self.cell.lm.t3

    def _get_map_time4(self): #associated to midslow
        return self.cell.lm.t4

    def get_current_img(self):
        return self.imgs_z_t[self.editor.zoom_level][self.get_current_frame()]

    def get_current_img_and_rect(self, cell_size):
        """Return img and absolute position of rect in the map"""
        img = self.get_current_img()
        r = self.editor.cam.get_rect_at_coord(self.cell.coord)
        ir = img.get_rect()
        ir.center = r.center
        ir.move_ip(self.relpos[0]*cell_size, self.relpos[1]*cell_size)
        return img, ir

    def get_lowest_rect(self, cell_size):
        """Return img and absolute position of rect in the map, for the sprite
        having the lowest y-pos"""
        rects = []
        for img in self.imgs_z_t[self.editor.zoom_level]:
            r = self.editor.cam.get_rect_at_coord(self.cell.coord)
            ir = img.get_rect()
            ir.center = r.center
            ir.move_ip(self.relpos[0]*cell_size, self.relpos[1]*cell_size)
            rects.append(ir)
        rects.sort(key=lambda x:x.bottom)
        return ir

    def get_fakerect_and_img(self, cell_size):
        """We need to hash the rects, but Rect is not hashable, so we return
        a tuple instead."""
        img = self.get_current_img()
        r = self.lm.cam.get_rect_at_coord(self.cell.coord)
        ir = img.get_rect()
        ir.center = r.center
        ir.move_ip(self.relpos[0]*cell_size, self.relpos[1]*cell_size)
        return (ir.x, ir.y, ir.right, ir.bottom), img

    def get_rect_and_img(self, cell_size):
        img = self.get_current_img()
        r = self.lm.cam.get_rect_at_coord(self.cell.coord)
        ir = img.get_rect()
        ir.center = r.center
        ir.move_ip(self.relpos[0]*cell_size, self.relpos[1]*cell_size)
        return ir, img


    def get_current_cell_rect_center(self, cell_size):
        r = self.get_current_cell_rect(cell_size)
        x = self.relpos[0]*cell_size + r.centerx
        y = self.relpos[1]*cell_size + r.centery
        return x,y

    def get_current_cell_rect(self, cell_size):
        return self.editor.cam.get_rect_at_coord(self.cell.coord)

    def get_relative_pos(self, cell_size):
        return self.relpos[0]*cell_size, self.relpos[1]*cell_size

    def set_same_type(self, objs):
        for o in objs:
            o.int_type = self.int_type

    def distance_to(self, another_obj):
        return self.cell.distance_to(another_obj.cell)

    def set_animation_speed(self, type_):
        if type_ == "normal":
            self.set_frame_refresh_type(const.NORMAL)
        elif type_ == "fast":
            self.set_frame_refresh_type(const.FAST)
        elif type_ == "slow":
            self.set_frame_refresh_type(const.SLOW)
        elif type_ == "midslow":
            self.set_frame_refresh_type(const.MIDSLOW)
        else:
            raise Exception("Unknown animation speed :", type_)

    def set_frame_refresh_type(self, type_):
        functions = {const.NORMAL:self._get_current_frame1,
                     const.FAST:self._get_current_frame2,
                     const.MIDSLOW:self._get_current_frame4,
                     const.SLOW:self._get_current_frame3}
        assert type_ in functions
        self._refresh_frame_type = type_
        self.get_current_frame = functions[type_]
        #
        functions = {const.NORMAL:self._get_map_time1,
                     const.FAST:self._get_map_time2,
                     const.MIDSLOW:self._get_map_time4,
                     const.SLOW:self._get_map_time3}
        assert type_ in functions
        self.get_map_time = functions[type_]




