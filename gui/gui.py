import pygame, thorpy, math, random
from pygame.math import Vector2 as V2
import RpgMap.gui.elements as elements
import RpgMap.gui.parameters as guip
import RpgMap.saveload.io as io
from RpgMap.gui import texts
from RpgMap.gui.theme import set_theme
from RpgMap.gui import transitions

ONOMATOPOEIA_DURATION = 1.5
ONOMATOPOEIA_COLOR = (255,)*3
def get_onomatopoeia_frames(text, color):
    els = []
    for font_size in range(22, 15, -1):
        els.append(thorpy.make_text(text, font_size, color))
    return els

def quit_func():
##    io.ask_save(self.game.me)
    thorpy.functions.quit_func()

class Footprint:

    def __init__(self, unit, age, pos):
        self.unit = unit
        dx = self.unit.footprint.get_size()[0]
        self.age = age
        self.pos = (pos[0]-dx,pos[1]-dx)
        self.pos2 = (pos[0]+dx, pos[1]+dx)

    def blit_and_increment(self, surface):
        surface.blit(self.unit.footprint, self.pos)
        surface.blit(self.unit.footprint, self.pos2)
        self.age += 1

class GuiGraphicsEnhancement:

    def __init__(self, gui, zoom, splashes=True, footprints=True):
        self.zoom = zoom
        self.gui = gui
        self.surface = self.gui.surface
        #
        self.splashes = []
        self.splash = None
        self.units_splashes = []
        if splashes:
            self.splashes = [pygame.image.load("sprites/splash.png")]
            self.splashes.append(pygame.transform.flip(self.splashes[0],
                                    True, False))
            self.splash = self.splashes[0]
        #
        self.show_footprints = footprints
        self.footprints = {}
        self.max_footprint_age = 100

    def draw_splashes(self):
        if self.gui.game.me.zoom_level != self.zoom:
            return
        self.splash = self.splashes[self.gui.game.me.lm.t%len(self.splashes)]
        for u in self.units_splashes:
            rect = u.get_current_cell_rect(self.zoom)
            self.surface.blit(self.splash, rect.move(0,-6).bottomleft)

    def draw_footprints(self):
        if self.gui.game.me.zoom_level != self.zoom:
            return
        to_remove = []
        for coord, footprint in self.footprints.items():
            if footprint.age > self.max_footprint_age:
                to_remove.append(coord)
            else:
                footprint.blit_and_increment(self.surface)
        for coord in to_remove:
            self.footprints.pop(coord)


    def refresh(self):
        if self.gui.game.me.zoom_level != self.zoom:
            return
        if self.splash or self.show_footprints:
            self.units_splashes = []
            for u in self.gui.game.units:
                ############################ Splashes ##########################
                if self.splash:
                    if t == "river" or "water" in t:
                        self.units_splashes.append(u)
                ################### Footprints #################################
                if self.show_footprints:
                    if t == "sand" or "snow" in t:
                        if not self.gui.game.get_object("forest", u.cell.coord):
                            rect = u.get_current_cell_rect(self.zoom)
                            footprint = Footprint(u, 0, rect.center)
                            self.footprints[u.cell.coord] = footprint


class Gui:

    def __init__(self, game, time_remaining=-1):
        game.update_loading_bar("Building gui elements", 0.95)
        self.game = game
        game.gui = self
        #
        self.font_colors_mat = {}
        for m in self.game.me.materials:
            n = m.lower()
            if "snow" in n or "sand" in n:
                self.font_colors_mat[m] = (0,)*3
            else:
                self.font_colors_mat[m] = (255,)*3
        #
        self.surface = thorpy.get_screen()
        game.me.cam.ui_manager = self
        self.me = game.me
        self._debug = True
        self.enhancer = GuiGraphicsEnhancement( self, zoom=0, #work only for a given zoom level
                                                splashes=True,
                                                footprints=True)
        #
        self.last_destination_score = {}
        self.destinations_mousemotion = []
        self.destinations_lmb = []
        self.forced_gotocell = False
        self.selected_unit = None
        self.cell_under_cursor = None
        self.blue_highlights = []
        self.red_highlights = []
        #
        self.color_dest_lmb = (255,0,0)
        self.color_dest_mousemotion = (255,255,0)
        self.dest_alpha_amplitude = 20
        self.dest_alpha0 = 100
        self.dest_period = self.me.lm.nframes * 3.
        self.dest_omega = 2. * math.pi / self.dest_period
        #
        self.e_cant_move = guip.get_infoalert_text("Can't go there")
        self.e_cant_move_another = guip.get_infoalert_text("Another unit is already going there")
        self.e_wrong_team = guip.get_infoalert_text("You cannot command another player's units")
        self.e_already_moved = guip.get_infoalert_text("This unit has already moved in this turn")
        #
        self.moving_units = []
        self.add_reactions()
        self.life_font_size = guip.NFS
        self.life_font_color = (255,255,255)
        self.font_life = pygame.font.SysFont(guip.font_gui_life, self.life_font_size)
        self.show_lifes = True
        self.interaction_objs = []
        #
        #here you can add/remove buttons to/from the menu
        e_options = thorpy.make_button("Options", self.show_options)
        e_save = thorpy.make_button("Save", io.ask_save, {"me":self.me})
        e_load = thorpy.make_button("Load", io.ask_load)
        e_quit = thorpy.make_button("Quit game", quit_func)
        self.menu = thorpy.make_ok_box([ get_help_box().launcher,
                                                    e_options,
                                                    e_save,
                                                    e_load,
                                                    e_quit])
        self.menu.center()
        self.set_map_gui()
        e_ap_cancel_move = elements.get_infoalert_text("To cancel last move, press", "<RETURN>")
        self.me.alert_elements.append(e_ap_cancel_move)
        self.me.ap.add_alert_countdown(e_ap_cancel_move, guip.DELAY_HELP * self.me.fps)
        self.has_moved = []
        #
        self.e_add = {key:thorpy.make_button("+") for key in ["left","right","top","down"]}
        self.e_rem = {key:thorpy.make_button("-") for key in ["left","right","top","down"]}
        self.last_move = None


    def set_map_gui(self):
        me = self.me
        ########################################################################
##        self.hline = thorpy.Line(int(0.75*me.e_box.get_fus_rect().width), "h")
##        me.add_gui_element(self.hline, True)
        ########################################################################
        me.menu_button.user_func = self.launch_map_menu


    def show_players_infos(self):
        w = self.game.me.screen.get_width()//2
        objs = ["village", "windmill", "tower"]
        unit_types = set([u.str_type for u in self.game.units])
        boxes = []
        o_e = []
        for pn in [0,1]:
            p = self.game.players[pn]
            title = thorpy.make_text(p.name, 15, p.color_rgb)
            line = thorpy.Line(w, "h")
            p = self.game.players[pn]
            els = []
            for typ in objs:
                for o in self.game.get_objects_of_team(p.team, typ):
##                    img = self.game.me.extract_img(o.cell)
                    if typ == "village":
                        img = self.game.village.imgs_z_t[0][0]
                    elif typ == "windmill":
                        img = self.game.windmill.imgs_z_t[0][0]
                    elif typ == "tower":
                        img = p.race.tower.imgs_z_t[0][0]
                    els.append(thorpy.Image(img))
                    o_e.append((els[-1], o))
            thorpy.grid_store(10, pygame.Rect(0,0,100,100), els)
            g_buildings = thorpy.make_group(els, mode=None)
            #
            els = []
            for typ in unit_types:
                for u in self.game.units:
                    if u.str_type == typ and u.race.team == p.team:
                        img = u.imgs_z_t[0][u.get_current_frame()]
                        els.append(thorpy.Image(img))
                        o_e.append((els[-1], u))
            thorpy.grid_store(10, pygame.Rect(0,0,100,100), els)
            g_units = thorpy.make_group(els, mode=None)
            #
            money_img = thorpy.Image(self.e_gold_img.get_image())
            money_txt = thorpy.make_text(str(p.money))
            income = self.game.compute_player_income(p)
            income_txt = thorpy.make_text("  (income: "+str(income)+")")
            g_money = thorpy.make_group([money_img, money_txt, income_txt])
            g = thorpy.Element(elements=[title,line,g_units,g_buildings,g_money])
            thorpy.store(g)
            g.fit_children()
            boxes.append(g)
        e = thorpy.Box(boxes)
        e.center()
        def refresh():
            for element, obj in o_e:
                img = obj.imgs_z_t[0][obj.get_current_frame()]
##                fire = self.game.get_object("fire", obj.cell.coord)
##                if fire:
##                    img_fire = fire.imgs_z_t[0][fire.get_current_frame()]
##                    r = img_fire.get_rect()
##                    w,h = img.get_size()
##                    r.center = w//2, h//2
##                    r.bottom = h
##                    img.blit(img_fire, r)
                element.set_image(img)
            self.game.me.func_reac_time()
            self.game.t += 1
            e.blit()
            pygame.display.flip()
        thorpy.add_time_reaction(e, refresh)
        def click():
            if not e.get_fus_rect().collidepoint(pygame.mouse.get_pos()):
                thorpy.functions.quit_menu_func()
        thorpy.add_click_reaction(e, click)
        m = thorpy.Menu(e, fps=self.game.me.fps)
        m.play()


    def get_day_text(self):
        if self.game.days_left > 0:
            if self.game.days_left == 1:
                return "Last day !"
            else:
                return str(self.game.days_left) + " days left"

    def check_end_turn(self):
        if self.selected_unit.is_grayed:
            return False
        return True

    def end_turn(self):
        self.selected_unit.make_grayed()

    def extinguish(self):
        if self.game.get_object("fire", self.cell_under_cursor.coord):
            self.game.extinguish(self.cell_under_cursor.coord)

    def check_extinguish(self):
        u = self.selected_unit
        print("CHECK EXT", u.cell.distance_to(self.cell_under_cursor) <= u.help_range[1])
        if u.cell.distance_to(self.cell_under_cursor) <= u.help_range[1]:
            n = u.str_type
            return n == "wizard" or n == "arch_wizard"
        return False

    def launch_map_menu(self):
        thorpy.launch_blocking(self.menu)

    def refresh_graphics_options(self):
        self.font_life = pygame.font.SysFont(guip.font_gui_life, self.life_font_size)
        self.clear()

    def check_interact_burn(self):
        """Return True if there is at least one thing (cell/object) that can
        burn."""
        if self.game.burning.get(self.cell_under_cursor.coord):
            return False
        elif self.unit_under_cursor():
            return False
        elif self.selected_unit.cell.distance_to(self.cell_under_cursor) != 1:
            return False
        else:
            for o in self.cell_under_cursor.objects: #ok
                if o.str_type in self.game.is_burnable:
                    return True
            if self.game.get_object("river", self.cell_under_cursor.coord):
                return False
        if self.selected_unit.str_type == "wizard":
            return self.cell_under_cursor.material.name.lower() in self.game.is_burnable

    def check_interact_gotocell(self):
        c = self.cell_under_cursor
        if self.game.burning.get(c.coord):
            return False
        if c.unit:
            return False
        rect = self.me.cam.get_rect_at_coord(c.coord)
        if rect.center in self.destinations_lmb:
            return True

    def choice_gotocell(self):
        self.forced_gotocell = True

    def clear(self):
        self.selected_unit = None
        self.cell_under_cursor = None
        self.blue_highlights = []
        self.red_highlights = []
        self.interaction_objs = []
        self.can_be_fought = []
        self.can_be_helped = []
        self.current_battle_simulation = None
        self.stars = []

    def cancel(self):
        if self.last_move:
            u, cell = self.last_move
            if u in self.has_moved:
                self.has_moved.remove(u)
                u.move_to_cell(cell)
                self.last_move = None

    def get_destinations(self, cell):
        destinations = []
        self.red_highlights = []
        self.blue_highlights = []
        self.can_be_fought = []
        self.can_be_helped = []
        if cell.unit:
            if cell.unit.is_grayed:
                return []
            if cell.unit.anim_path: #moving unit, let it alone...
                return []
            elif cell.unit in self.has_moved:
                return []
            if not self.selected_unit:
                ref_unit = self.cell_under_cursor.unit
            else:
                ref_unit = self.selected_unit
            score = cell.unit.get_possible_destinations()
            score[cell.coord] = []
            self.last_destination_score = score
            for coord in score:
##                if coord != cell.coord:
                rect = self.me.cam.get_rect_at_coord(coord)
                destinations.append(rect.center)
                if ref_unit:
                    self.update_possible_interactions(ref_unit, coord)
        return destinations

    def update_possible_help_and_fight(self, coord):
        ref_unit = self.selected_unit
        if not ref_unit:
            ref_unit = self.cell_under_cursor.unit
        for other in self.game.units:
            if other is not ref_unit:
                d = other.cell.distance_to_coord(coord)
                if other.team == ref_unit.team:
                    if d <= ref_unit.help_range[1]:
                        if other.quantity < other.base_number:
                            self.can_be_helped.append(other)
                elif d <= ref_unit.attack_range[1]:
                    self.can_be_fought.append(other)

    def update_possible_interactions(self, ref_unit, coord):
        #interactions possible for <ref_unit> when located at hypothetic position <coord>
        for other in self.game.units:
            if other is not ref_unit:
                if other.cell.coord == coord:
                    self.add_unit_highlight(ref_unit, other)
                else:
                    if other.team == ref_unit.team:
                        coords = ref_unit.get_coords_in_help_range()
                    else:
                        coords = ref_unit.get_coords_in_attack_range()
                    for dx,dy in coords:
                        if other.cell.coord == (coord[0]+dx, coord[1]+dy):
                            self.add_unit_highlight(ref_unit, other)
                            break


    def add_unit_highlight(self, ref_unit, unit):
        if unit.team == ref_unit.team:
            self.blue_highlights.append(unit)
        else:
            self.red_highlights.append(unit)

    def add_alert(self, e, coord=None):
        duration = guip.DELAY_HELP * self.me.fps
        self.me.ap.add_alert(e, duration)

    def add_onomatopoeia(self, elements, coord):
        duration = ONOMATOPOEIA_DURATION * self.me.fps
        self.me.ap.add_frames_on_coord(elements, coord, duration)

    def want_to_leave_construction(self, u):
        ok = thorpy.launch_binary_choice("Leave construction ?")
        if ok:
            what, t, unit = self.game.constructions[u.is_building]
            self.game.constructions[u.is_building] = (what, t, None)
            u.is_building = None
            return True

    def go_to_cell(self, u, path):
        if u.is_building:
            if not self.want_to_leave_construction(u):
                return
        self.last_move = u, u.cell
        print("LOGGIG", self.last_move)
        u.move_to_cell_animated(path)
        self.moving_units.append(u)
        self.game.walk_sounds[0].play(-1)


    def small_clear(self):
        self.selected_unit = None
        self.stars = []
        self.current_battle_simulation = None
##        self.blue_highlights = []
##        self.red_highlights = []


    def refresh_moving_units(self):
        to_remove = []
        for u in self.moving_units:
            if not u.anim_path:
                to_remove.append(u)
                #automatic select of unit
                self.selected_unit = u
                self.update_possible_help_and_fight(u.cell.coord)
        for u in to_remove:
            self.moving_units.remove(u)
            self.game.walk_sounds[0].stop()
            self.has_moved.append(u)


    def treat_click_destination(self, cell):
        rect = self.me.cam.get_rect_at_coord(cell.coord)
        print("     clicked:", cell.coord)
        print("     len(dest_lmb):", len(self.destinations_lmb))
        if rect.center in self.destinations_lmb:
            print("     Correct destination")
            cost, path = self.last_destination_score.get(cell.coord, None)
            x,y = path[-1]
            friend = self.game.get_unit_at(x,y)
            print("     friend:",friend)
            #control that the path is not crossing another moving unit's path..
            can_move = True
            for u in self.moving_units:
                if not(u is self.selected_unit):
                    for planned_coord in u.anim_path:
                        if planned_coord in path:
                            can_move = False
                            break
            if can_move:
                if friend: #the user wants to fusion units
##                    #check that same type and sum of quantities does not exceed max_quantity
##                    u1 = self.selected_unit
##                    u2 = friend
##                    MAX_QUANTITY = 20
##                    ok = u2.str_type == u1.str_type and u1.quantity + u2.quantity <= MAX_QUANTITY
                    ok = False
                    if ok:
                        self.go_to_cell(self.selected_unit, path[1:])
                    else:
                        self.add_alert(self.e_cant_move)
                        self.game.deny_sound.play()
                else:
                    self.go_to_cell(self.selected_unit, path[1:])
            else:
                self.add_alert(self.e_cant_move_another)
                self.game.deny_sound.play()
            # self.selected_unit.move_to_cell(cell)
            self.small_clear()


    def burn(self):
        time_left = 2
        if self.game.get_object("windmill", self.cell_under_cursor.coord):
            time_left = 1
        self.game.set_fire(self.cell_under_cursor.coord, time_left)
        self.selected_unit.make_grayed()


    def lmb_unit_already_moved(self, cell):
        if self.selected_unit.is_grayed:
            self.clear()
        else:
            self.update_possible_help_and_fight(self.selected_unit.cell.coord)
            if cell.unit in self.can_be_fought:
                d = cell.distance_to(self.selected_unit.cell)
                if d > 1:
                    self.distant_attack()
                else:
                    self.attack()
                self.clear()
            elif cell.unit in self.can_be_helped:
                self.help()
                self.clear()
            else:
                self.rmb(None)
            self.can_be_fought = []
            self.can_be_helped = []


    def lmb(self, e):
        print("LMB", self.game.t, self.selected_unit)
        self.destinations_mousemotion = []
        pos = e.pos
        cell = self.me.cam.get_cell_at_pix(pos)
        if cell:
            if self.destinations_lmb: #user may be clicking a destination
                interactibles = self.game.get_interactive_objects(cell.coord[0],
                                                                  cell.coord[1])
                if interactibles: #there are objects interactibles at the dest.
                    if cell.unit is None:
                        choices = self.get_interaction_choices(interactibles,
                                                    exceptions=["Burn", "End turn"])
                        if choices:
                            self.user_make_choice(choices)
                        if self.selected_unit:
                            self.treat_click_destination(cell)
                    else: #there is already a unit in the destination
                        choices = self.get_interaction_choices(interactibles,
                                                    exceptions=["Burn", "End turn"])
                        if choices:
                            self.user_make_choice(choices)
                else:
                    self.treat_click_destination(cell)
                self.destinations_lmb = [] #clear destinations
                self.red_highlights = []
                self.blue_highlights = []
                self.can_be_fought = []
                self.can_be_helped = []
                self.small_clear()
            else:#no path (destination) is drawn for lmb
                if self.selected_unit:
                    self.lmb_unit_already_moved(cell)
                    self.small_clear()
                    return
                if cell.unit:
                    if cell.unit.team == self.game.current_player.team:
                        self.selected_unit = cell.unit
                        if not(cell.unit in self.has_moved):
                            print("Update destinations")
                            self.destinations_lmb = self.get_destinations(cell)
                        self.update_possible_help_and_fight(self.selected_unit.cell.coord)
                    else:
                        self.add_alert(self.e_wrong_team)
                        self.game.deny_sound.play()
                else:
                    o = self.game.get_object("village", cell.coord)
                    if o:
                        o2 = self.game.get_object("flag", cell.coord)
                        if o2:
                            if o2.team == self.game.current_player.team:
                                self.production(o)
                                self.small_clear()
                                return
                    self.small_clear()


    def rmb(self, e):
        if self.selected_unit:
            cell = self.cell_under_cursor
            if cell:
                print("Treat interaction RMB")
                if self.selected_unit in self.has_moved:
                    self.update_possible_interactions(self.selected_unit, cell.coord)
                interactibles = self.game.get_interactive_objects(cell.coord[0],
                                                                  cell.coord[1])
                choices = self.get_interaction_choices(interactibles)
                if choices:
                    self.user_make_choice(choices)
                    if self.forced_gotocell:
                        self.forced_gotocell = False
                        self.treat_click_destination(cell)
                else:
                    return
        self.destinations_mousemotion = []
        self.destinations_lmb = []
        self.small_clear()

    def mousemotion(self, e):
        self.destinations_mousemotion = []
        pos = e.pos
        cell = self.me.cam.get_cell_at_pix(pos)
##        cell = self.me.get_cell_at_pix(pos)
        if cell:
            self.cell_under_cursor = cell
            if self.destinations_lmb: #then the user may be tracing the path
                value = self.last_destination_score.get(cell.coord, None)
                if value:
                    self.can_be_fought = []
                    self.can_be_helped = []
                    cost, path = value
                    for coord in path:
                        rect = self.me.cam.get_rect_at_coord(coord)
                        self.destinations_mousemotion.append(rect.center)
                    self.update_possible_help_and_fight(path[-1])
                else: #cannot go there
                    self.try_attack_simulation()
            else:
                if self.selected_unit:
                    self.update_possible_help_and_fight(self.selected_unit.cell.coord)
                    self.try_attack_simulation()
                else:
                    self.destinations_mousemotion = self.get_destinations(cell)
        else:
            self.cell_under_cursor = None

    def continue_build(self):
        if self.selected_unit.is_building:
            if not self.want_to_leave_construction(self.selected_unit):
                return
        coord = self.cell_under_cursor.coord
        self.game.construction_sound.play()
        what, time, unit = self.game.constructions[coord]
        self.game.constructions[coord] = what, time, self.selected_unit
        self.selected_unit.make_grayed()
        self.selected_unit.is_building = coord
        self.small_clear()


    def launch_construction(self, type_):
        self.game.coin_sound.play()
        self.game.add_construction(self.cell_under_cursor.coord, type_,
                                    self.selected_unit)
        self.selected_unit.is_building = self.cell_under_cursor.coord
        self.selected_unit.make_grayed()
        self.game.current_player.money -= int(self.game.construction_price[type_])
        self.e_gold_txt.set_text(str(self.game.current_player.money))
        self.refresh()
        self.small_clear()
        thorpy.functions.quit_menu_func()

    def get_alpha_dest(self):
        t = self.me.lm.tot_time
        return math.sin(t * self.dest_omega) * self.dest_alpha_amplitude + self.dest_alpha0

    def draw_highlight(self, unit, color, s):
        img = unit.get_current_highlight(color)
        rect = img.get_rect()
        rect.center = unit.get_current_cell_rect_center(s)
        self.surface.blit(img, rect.topleft)


    def unit_under_cursor(self):
        if self.cell_under_cursor:
            return self.cell_under_cursor.unit
        else:
            return None

    def draw_before_objects(self, s):
        self.enhancer.draw_footprints()
        self.refresh_moving_units()
        uuc = self.unit_under_cursor()
        if uuc:
            self.draw_highlight(uuc, "yellow", s)
        if self.selected_unit:
            if self.selected_unit is not uuc:
                self.draw_highlight(self.selected_unit, "yellow", s)
        #1. left mouse button
        if self.destinations_lmb:
            surf = pygame.Surface((s,s))
            rect = surf.get_rect()
            surf.set_alpha(self.get_alpha_dest())
            surf.fill(self.color_dest_lmb)
            for pos in self.destinations_lmb:
                rect.center = pos
                self.surface.blit(surf, rect)
        #2. highlights
        for unit in self.red_highlights:
            self.draw_highlight(unit, "red", s)
        for unit in self.blue_highlights:
            self.draw_highlight(unit, "blue", s)

    def draw_destinations(self, s):
        if self.destinations_mousemotion:
            surf = pygame.Surface((s-2,s-2))
            rect = surf.get_rect()
            surf.set_alpha(self.get_alpha_dest())
            surf.fill(self.color_dest_lmb)
            surf.fill(self.color_dest_mousemotion)
            for pos in self.destinations_mousemotion:
                rect.center = pos
                self.surface.blit(surf, rect)
                if self._debug:
                    coord = self.me.cam.get_coord_at_pix(rect.center)
                    #debug : draw distance
##                    if coord in self.last_destination_score:
##                        cost = self.last_destination_score[coord][0]
##                        text = thorpy.make_text(str(cost))
##                        self.surface.blit(text.get_image(), rect)

    def draw_after_objects(self, s):
        self.enhancer.draw_splashes()

    def unit_dies(self, u):
        for l in [self.has_moved, self.can_be_fought, self.can_be_helped]:
            if u in l:
                l.remove(u)


    def refresh(self):
        self.enhancer.refresh()
        if self.game.need_refresh_ui_box:
            thorpy.store(self.me.e_box)
            self.game.need_refresh_ui_box = False

##    def add_flag(self):
##        self.game.add_unit((16,15), self.game.units[0].race["flag"], 1, team=self.game.units[0].team)

    def find_free_unit(self):
        for u in self.game.get_units_of_player(self.game.current_player):
            if not u.is_grayed:
                if not u in self.has_moved:
                    if not u.is_building:
                        self.game.center_cam_on_cell(u.cell.coord)
                        self.blue_highlights.append(u)

    def toggle_show_life(self):
        self.show_lifes = not(self.show_lifes)

    def add_reactions(self):
        reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, self.lmb,{"button":1})
        self.me.e_box.add_reaction(reac_click)
        reac_click = thorpy.Reaction(pygame.MOUSEBUTTONDOWN, self.rmb,{"button":3})
        self.me.e_box.add_reaction(reac_click)
        reac_motion = thorpy.Reaction(pygame.MOUSEMOTION, self.mousemotion)
        self.me.e_box.add_reaction(reac_motion)
##        reac_escape = thorpy.ConstantReaction(pygame.KEYDOWN, self.esc_menu, {"key":pygame.K_ESCAPE})
##        self.me.e_box.add_reaction(reac_escape)
        shortcuts = [(pygame.K_l, self.toggle_show_life),
                     (pygame.K_ESCAPE, self.launch_map_menu),
                     (pygame.K_PERIOD, self.find_free_unit),
                     (pygame.K_BACKSPACE, self.cancel)]
        reacs = []
        for key,func in shortcuts:
            reacs.append(thorpy.ConstantReaction(pygame.KEYDOWN, func,
                         {"key":key}))
        self.me.e_box.add_reactions(reacs)

    def show_options(self):
        e_life_size = thorpy.SliderX(100, (6, 20), "Life font size", type_=int,
                                            initial_value=self.life_font_size)
##        e_life_color = thorpy.ColorSetter(text="Life font color",
##                                            value=self.life_font_color)
        e_title = thorpy.make_text("Units life")
        e_box = thorpy.make_ok_cancel_box([e_title, e_life_size])
        e_box.center()
        result = thorpy.launch_blocking(e_box)
        if result.how_exited == "done":
            self.life_font_size = e_life_size.get_value()
##            self.life_font_color = e_life_color.get_value()
            self.refresh_graphics_options()
        self.me.draw()
        self.menu.blit()
        pygame.display.flip()


    def show_animation_income(self, from_, to, fps=60):
        game = self.game
        COIN_PER_VILLAGE = 1 * 2
        COIN_PER_WINDMILL = 5 * 2
        MOD_SPAWN = 5
        MAX_VEL = 20
        STOP_DIST = 10
        p = game.current_player
        img = self.e_gold_img.get_image()
        sources = {}
        values = {}
        target = self.e_gold_img.get_fus_rect().topleft
        flags = self.game.me.objects_dict.get("flag",{})
        for f in flags.values():
            if f.team == p.team:
                o = self.game.get_object("village", f.cell.coord)
                o2 = self.game.get_object("windmill", f.cell.coord)
                if o:
                    sources[f.cell.coord] = COIN_PER_VILLAGE
                    values[f.cell.coord] = int(INCOME_PER_VILLAGE * p.tax) // COIN_PER_VILLAGE
                elif o2:
                    sources[f.cell.coord] = COIN_PER_WINDMILL
                    values[f.cell.coord] = INCOME_PER_WINDMILL // COIN_PER_WINDMILL
        coins_flying = []
        done = False
        clock = pygame.time.Clock()
        i_anim = 0
        money = from_
        self.e_gold_txt.set_text(str(money))
        while not done:
            if i_anim%MOD_SPAWN == 0:
                for src in sources:
                    if sources[src] > 0:
                        game.coin_sound.play_next_channel()
                        x,y = game.me.cam.get_rect_at_coord(src).topleft
                        value = values[src]
                        coins_flying.append((x,y,value))
                        sources[src] -= 1
            new_coins_flying = []
            ####
            self.refresh()
            self.me.func_reac_time()
            clock.tick(game.me.fps)
            game.t += 1
            ###
            for x,y,value in coins_flying:
                game.me.screen.blit(img, (x,y))
                delta = V2(target) - (x,y)
                L = delta.length()
                if L > MAX_VEL:
                    delta.scale_to_length(MAX_VEL)
                if L > STOP_DIST:
                    x += delta.x
                    y += delta.y
                    new_coins_flying.append((x,y,value))
                else:
                    money += value
                    game.coin_sound.play_next_channel()
                    self.e_gold_txt.set_text(str(money))
            coins_flying = new_coins_flying
            pygame.display.flip()
            i_anim += 1
            if not coins_flying:
                done = True


#1 by 1 version
##    def show_animation_income(self, from_, to, fps=60):
##        game = self.game
##        COIN_PER_VILLAGE = 2
##        COIN_PER_WINDMILL = 10
##        MOD_SPAWN = 15
##        MAX_VEL = 15
##        STOP_DIST = 10
##        p = game.current_player
##        img = self.e_gold_img.get_image()
##        sources = {}
##        target = self.e_gold_img.get_fus_rect().topleft
##        flags = self.game.me.objects_dict.get("flag",{})
##        for f in flags.values():
##            if f.team == p.team:
##                o = self.game.get_object("village", f.cell.coord)
##                o2 = self.game.get_object("windmill", f.cell.coord)
##                if o:
##                    sources[f.cell.coord] = COIN_PER_VILLAGE
##                elif o2:
##                    sources[f.cell.coord] = COIN_PER_WINDMILL
##        coins_flying = []
##        clock = pygame.time.Clock()
##        i_anim = 0
##        money = from_
##        self.e_gold_txt.set_text(str(money))
##        for coord in sources:
##            self.game.center_cam_on_cell(coord)
##            done = False
##            i_anim = 0
##            coins_flying = []
##            n = sources[coord]
##            if n > COIN_PER_VILLAGE:
##                delta_coin = INCOME_PER_WINDMILL
##            else:
##                delta_coin = INCOME_PER_VILLAGE * p.tax
##            ######
##            while not done:
##                if i_anim%MOD_SPAWN == 0:
##                    if n > 0:
##                        cam_coord = game.me.cam.get_rect_at_coord(coord).topleft
##                        coins_flying.append(cam_coord)
##                        n -= 1
##                new_coins_flying = []
##                ####
##                self.refresh()
##                self.me.func_reac_time()
##                clock.tick(game.me.fps)
##                game.t += 1
##                ###
##                for x,y in coins_flying:
##                    game.me.screen.blit(img, (x,y))
##                    delta = V2(target) - (x,y)
##                    L = delta.length()
##                    if L > MAX_VEL:
##                        delta.scale_to_length(MAX_VEL)
##                    if L > STOP_DIST:
##                        x += delta.x
##                        y += delta.y
##                        new_coins_flying.append((x,y))
##                    else:
##                        money += delta_coin
##                        game.coin_sound.play_next_channel()
##                        self.e_gold_txt.set_text(str(money))
##                coins_flying = new_coins_flying
##                pygame.display.flip()
##                i_anim += 1
##                if not coins_flying:
##                    done = True


def get_help_box():
    return elements.HelpBox([
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
            [("Press","<RETURN>","to cancel last move."),
             ("Press","<G>","to toggle grid lines display."),
             ("Press", "<L>", "to toggle the display of units life.")])
        ])
