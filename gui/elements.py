import pygame, thorpy
import RpgMap.gui.parameters as guip


def get_help_text(*texts):
##    if start == "normal":
##        state = 0
##    else:
##        state = 1
    state = 0
    get_text = {0:guip.get_info_text, 1:guip.get_highlight_text}
    els = []
    for text in texts:
        els.append(get_text[state](text))
        state = 1 if state==0 else 0
    return thorpy.make_group(els)

def get_infoalert_text(*texts):
    h = get_help_text(*texts)
    e = thorpy.Element("",[h])
##    e.set_font_size(HFS)
##    e.set_font_color(HFC)
    thorpy.store(e)
    e.set_main_color((200,200,200,100))
    e.fit_children()
    return e

def get_help_text_normal(*texts,start="normal"):
    if start == "normal":
        state = 0
    else:
        state = 1
    get_text = {0:guip.get_text, 1:guip.get_highlight_text}
    els = []
    for text in texts:
        els.append(get_text[state](text))
        state = 1 if state==0 else 0
    return thorpy.make_group(els)


def get_cursors(rect, color):
    assert color != (255,255,255) #used for transparency
    thick = int(rect.w/5)
    if thick != 0:
        if thick%2 != 0: thick -= 1
    thick2 = int(rect.w/3)
    if thick2 != 0:
        if thick2%2 != 0: thick2 -= 1
    cursors = [get_cursor(rect, color, 0, thick2)]
    for thick in range(1,thick):
        cursors.append(get_cursor(rect, color, thick, thick2))
    if len(cursors) > 1:
        cursors.pop(0)
    cursors += cursors[::-1][1:-1]
    return cursors[::-1]

def get_cursor(rect, color, thick, thick2):
    surface = pygame.Surface(rect.size)
    surface = pygame.Surface(rect.size)
    surface.fill(color)
    rbulk = rect.inflate((-2*thick,-2*thick))
    rbulk.topleft = (thick,thick)
    pygame.draw.rect(surface, (255,255,255), rbulk)
    rh = pygame.Rect(0,thick2,rect.w,rect.h-2*thick2)
    pygame.draw.rect(surface, (255,255,255), rh)
    rw = pygame.Rect(thick2,0,rect.w-2*thick2,rect.w)
    pygame.draw.rect(surface, (255,255,255), rw)
    surface.set_colorkey((255,255,255))
    return surface

##def launch():

class MiscInfo:
    def __init__(self, size):
        self.e_title = guip.get_title("Map infos")
        self.e = thorpy.Box.make([self.e_title])
        self.e.set_size((size[0],None))

class CellInfo:
    def __init__(self, me, size, cell_size, redraw, external_e):
        self.me = me
        self.wline = int(0.75*size[0])
        self.e_coordalt = thorpy.make_text("(?,?)", font_size=10, font_color=(200,200,200))
        self.e_mat_img = thorpy.Image.make(pygame.Surface(cell_size))
        self.e_mat_name = guip.get_text("")
        self.e_obj_name = guip.get_text("")
        self.e_mat_obj = thorpy.make_group([self.e_mat_name,  self.e_obj_name], "v")
##        self.e_mat = thorpy.make_group([self.e_mat_img, self.e_mat_obj])
        self.e_mat = thorpy.Box(elements=[self.e_mat_img, self.e_mat_obj])
##        self.e_mat.fit_children(axis=(False, True))
        self.elements = [self.e_mat, self.e_coordalt]
        self.e = thorpy.Box.make(self.elements)
        self.e.set_main_color((20,20,20))
        self.e.set_size((size[0],int(0.8*self.e.get_fus_size()[1])), margins=(2,2))
        for e in self.e.get_elements():
            e.recenter()
        self.cell = None
        #emap : to be displayed when a cell is clicked
        self.em_title = guip.get_title("Cell informations")
        self.em_coord = guip.get_text("")
        self.em_altitude = guip.get_text("")
        self.em_name = guip.get_small_text("")
        self.em_rename = guip.get_small_button("Rename", self.rename_current_cell)
        self.em_name_rename = thorpy.make_group([self.em_name, self.em_rename])
##        self.em_name_rename = thorpy.Clickable.make(elements=[self.em_name, self.em_rename])
##        thorpy.store(self.em_name_rename)
        self.em_name_rename.fit_children()
        self.em_mat_img_img = thorpy.Image.make(pygame.Surface(cell_size))
        self.em_mat_img = thorpy.Clickable.make(elements=[self.em_mat_img_img])
        self.em_mat_img.fit_children()
        self.em_mat_name = guip.get_text("")
        self.em_obj_name = guip.get_text("")
        self.em_mat_obj = thorpy.make_group([self.em_mat_name,  self.em_obj_name], "v")
        self.em_mat = thorpy.make_group([self.em_mat_img, self.em_mat_obj])
##        self.em_elements = [self.em_title, thorpy.Line.make(self.wline), self.em_mat, self.em_coord, self.em_altitude, self.em_name_rename]
        self.em_elements = [self.em_title, thorpy.Line.make(self.wline), self.em_mat, self.em_coord, self.em_name_rename]
        self.em = thorpy.Box.make(self.em_elements)
        self.em.set_main_color((200,200,200,150))
        self.launched = False
        self.redraw = redraw
        self.external_e = external_e
        reac = thorpy.Reaction(thorpy.THORPY_EVENT, self.set_unlaunched,
                                {"id":thorpy.constants.EVENT_UNLAUNCH})
        external_e.add_reaction(reac)
        self.last_cell_clicked = None

    def set_unlaunched(self, e):
        if e.launcher.launched == self.em:
            self.launched = False

    def update_em(self, cell): #at rmb
        new_img = cell.get_static_img_at_zoom(0)
        self.em_mat_img_img.set_image(new_img)
        #
        text = cell.material.name
        for obj in cell.objects:
            if obj.is_ground:
                text = obj.name.capitalize()
                break
        self.em_mat_name.set_text(text)
        #
        objs = set([])
        for obj in cell.objects:
            if obj.is_ground:
                if "bridge" in obj.str_type:
                    objs.add("Bridge")
            else:
                if not obj.name[0] == "*":
                    objs.add(obj.name) #split to not take the id
##                    if obj.str_type == "fire":
##                        n = obj.game.burning[obj.cell.coord]
##                        objs.add("fire ("+str(n)+" turns)")
##                    else:
##                        objs.add(obj.name) #split to not take the id
        text = ", ".join([name for name in objs])
        self.em_obj_name.set_text(text.capitalize())
        #
        thorpy.store(self.em_mat, mode="h")
        self.em_coord.set_text("Coordinates: "+str(cell.coord))
##        self.em_altitude.set_text("Altitude: "+str(round(cell.get_altitude()))+"m")
        if not cell.name:
            cellname = "This location has no name"
        else:
            cellname = cell.name
        self.em_name.set_text(cellname)
        thorpy.store(self.em_name_rename, mode="h")
        self.em.store()
        self.em.fit_children()

    def launch_em(self, cell, pos, rect):
        if not self.launched:
            self.launched = True
            self.redraw()
            self.update_em(cell)
            #
            self.em.set_visible(False)
            for e in self.em.get_descendants():
                e.set_visible(False)
            thorpy.launch_nonblocking(self.em,True)
            self.em.set_visible(True)
            for e in self.em.get_descendants():
                e.set_visible(True)
            self.em.set_center(pos)
            self.em.clamp(rect)
            self.em.blit()
            self.em.update()


    def rename_current_cell(self):
        varset = thorpy.VarSet()
        varset.add("newname", "", "New name")
##        ps = thorpy.ParamSetterLauncher.make(varset)
        ps = thorpy.ParamSetter.make([varset])
        for h in ps.get_handlers():
            ins = ps.handlers[h]
        ins.set_main_color((200,200,200,150))
        ps.center()
        ins.enter() #put focus on inserter
        thorpy.launch_blocking(ps)
        newname = ins.get_value()
        newname = newname.replace("*","")
        if newname:
            self.cell.set_name(newname)
        self.update_em(self.cell)
        self.redraw()
        self.em.blit()
        pygame.display.flip()



    def update_e(self, cell): #at hover
        self.cell = cell
        # text for material and ground
        text = cell.material.name
        for obj in cell.objects:
            if obj.is_ground:
                text = obj.name.capitalize()
                break
        self.e_mat_name.set_text(text)
        # text for other objects, including units
        objs = set()
        for obj in cell.objects:
            if obj.is_ground:
                if "bridge" in obj.str_type:
                    objs.add("Bridge")
            else:
                if not obj.name[0] == "*":
                    if obj.str_type == "flag":
                        text = "flag"
                    else:
                        text = obj.name
                    objs.add(text) #split to not take the id
        objs = list(objs)
        text = ""
        if len(objs) > 1:
            text = objs[0] + "(...)"
        elif len(objs) == 1:
            text = objs[0]
        self.e_obj_name.set_text(text.capitalize())
        #
##        new_img = self.me.extract_image(cell)
        new_img = cell.get_static_img_at_zoom(0)
        self.e_mat_img.set_image(new_img)
        if len(objs) > 0:
            thorpy.store(self.e_mat_obj)
            self.e_mat_obj.fit_children()
        else:
            self.e_mat_name.stick_to(self.e_mat_img,"right","left")
            self.e_obj_name.center(element=self.e_mat_name)
            self.e_mat_name.move((3,0))
        thorpy.store(self.e_mat, mode="h")
        self.e_mat.fit_children()
        #
##        altitude = round(cell.get_altitude())
##        alt_text = str(altitude) + "m"
        coord_text = str(cell.coord)# + "     "
##        self.e_coordalt.set_text(coord_text+alt_text)
        self.e_coordalt.set_text(coord_text)
        self.e_coordalt.fit_children()
##        self.e_coordalt.recenter()
        thorpy.store(self.e)

    def can_be_launched(self, cell, me):
        if cell:
            if not me.unit_info.launched and not self.launched:
                if cell is not self.last_cell_clicked:
                    return True
        return False



class UnitInfo: #name, image, nombre(=vie dans FS!)
    def __init__(self, me, size, cell_size, redraw, external_e):
        self.me = me
        self.wline = int(0.75*size[0])
        self.unit = None
##        self.cell = None probleme
        self.e_img = thorpy.Image.make(pygame.Surface(cell_size))
##        self.e_img = thorpy.Image.make(pygame.Surface((1,1)))
        self.blank_img = pygame.Surface(cell_size)
        self.e_name = guip.get_text("")
        self.e_race = guip.get_text("")
        self.e_name_and_race = thorpy.Box([self.e_name, self.e_race])
        self.e_name_and_race.fit_children()
        ghost = thorpy.Ghost([self.e_img, self.e_name_and_race])
        ghost.finish()
        self.e_img.set_center_pos(ghost.get_fus_center())
        self.e_name.set_center_pos(self.e_img.get_fus_center())
        ghost.fit_children()
        self.e_group = ghost
        #
        self.elements = [self.e_group]
        self.e = thorpy.Box.make(self.elements)
        self.e.set_main_color((20,20,20))
        self.e.set_size((size[0],None))
        for e in self.e.get_elements():
            e.recenter()
##        #emap : to be displayed when a cell is clicked
        self.em_title = guip.get_title("Unit informations")
##        self.em_coord = guip.get_text("")
##        self.em_altitude = guip.get_text("")
##        self.em_name = guip.get_small_text("")
        self.em_rename = guip.get_small_button("Rename", self.rename_current_unit)
##        self.em_rename.scale_to_title()
##        self.em_name_rename = thorpy.make_group([self.em_name, self.em_rename])
####        self.em_name_rename = thorpy.Clickable.make(elements=[self.em_name, self.em_rename])
####        thorpy.store(self.em_name_rename)
##        self.em_name_rename.fit_children()
        self.em_unit_img_img = thorpy.Image.make(pygame.Surface(cell_size))
        self.em_unit_img = thorpy.Clickable.make(elements=[self.em_unit_img_img])
        self.em_unit_img.fit_children()
        self.em_unit_name = guip.get_text("")
        self.em_unit_race = guip.get_text("")
        self.em_nameNrace = thorpy.make_group([self.em_unit_name, self.em_unit_race], "v")
        self.em_unit = thorpy.make_group([self.em_unit_img, self.em_nameNrace])
        self.em_elements = [self.em_title, thorpy.Line.make(self.wline), self.em_unit, self.em_rename]#self.em_name_rename]
        #
        self.em_mat_img_img = thorpy.Image.make(pygame.Surface(cell_size))
        self.em_mat_img = thorpy.Clickable.make(elements=[self.em_mat_img_img])
        self.em_mat_img.fit_children()
        def show_terrain_infos():
            cell = self.unit.cell
            self.me.cell_info.last_cell_clicked = cell
            pos = self.me.cam.get_rect_at_coord(cell.coord).center
            self.me.cell_info.launch_em(cell, pos, self.me.cam.map_rect)
##        self.em_button_cell = guip.get_button("Terrain infos", show_terrain_infos)
        self.em_mat_img.user_func = show_terrain_infos
        self.em_elements += [thorpy.Line.make(self.wline), self.em_mat_img]
        self.em = thorpy.Box.make(self.em_elements)
        self.em.set_main_color((200,200,200,150))
        self.launched = False
        self.redraw = redraw
        self.external_e = external_e
        reac = thorpy.Reaction(thorpy.THORPY_EVENT, self.set_unlaunched,
                                {"id":thorpy.constants.EVENT_UNLAUNCH})
        external_e.add_reaction(reac)
        self.last_cell_clicked = None
        self.e_img.visible = False

    def can_be_launched(self, cell, me):
        if cell:
            if not me.cell_info.launched and not self.launched:
                if cell is not self.last_cell_clicked:
                    if cell.unit:
                        return True
        return False

    def set_unlaunched(self, e):
        if e.launcher.launched == self.em:
            self.launched = False

    def update_em(self, cell):
        new_img = cell.unit.get_current_img()
        def descr():
            thorpy.launch_blocking_alert("Unit infos",
                                         cell.unit.get_description(),
                                         outside_click_quit=True)
            self.me.draw()
            self.em.blit()
            pygame.display.flip()
        self.em_unit_img.user_func = descr
        self.em_unit_img_img.set_image(new_img)
        self.em_unit_name.set_text(cell.unit.name.capitalize())
        baserace = cell.unit.race.baserace.capitalize()
        playername = cell.unit.get_all_players()[0].name
        self.em_unit_race.set_text(baserace + " (" + playername + ")")
        thorpy.store(self.em_unit, mode="h")
        #
        self.em_mat_img_img.set_image(self.me.cell_info.e_mat_img.get_image())
        self.em.store()
        self.em.fit_children()

    def launch_em(self, cell, pos, rect):
        if not self.launched:
            self.launched = True
            self.redraw()
            self.update_em(cell)
            #
            self.em.set_visible(False)
            for e in self.em.get_descendants():
                e.set_visible(False)
            thorpy.launch_nonblocking(self.em,True)
            self.em.set_visible(True)
            for e in self.em.get_descendants():
                e.set_visible(True)
            self.em.set_center(pos)
            self.em.clamp(rect)
            self.em.blit()
            self.em.update()
##        else:
##            print("Already launched!")


    def rename_current_unit(self):
        varset = thorpy.VarSet()
        varset.add("newname", "", "New name")
##        ps = thorpy.ParamSetterLauncher.make(varset)
        ps = thorpy.ParamSetter.make([varset])
        for h in ps.get_handlers():
            ins = ps.handlers[h]
        ins.set_main_color((200,200,200,150))
        ps.center()
        ins.enter() #put focus on inserter
        thorpy.launch_blocking(ps)
        newname = ins.get_value()
        newname = newname.replace("*","")
        newname = newname.replace("bridge","")
        if newname:
            self.unit.name = newname
        self.update_em(self.unit.cell)
        self.redraw()
        self.em.blit()
        pygame.display.flip()

##    def em_react(self, event):
##        if self.launched:
##            self.menu.react(event)

    def update_e(self, unit):
        changed = False
        if unit:
            name = unit.name + " (" + str(unit.quantity) + ")"
##            print(unit, unit.name)
            baserace = unit.race.baserace.capitalize()
            playername = unit.get_all_players()[0].name
            raceteam = baserace + " (" + playername + ")"
            new_img = unit.get_current_img()
            self.e_img.visible = True
            changed = True
        elif self.unit is not None:
            name = "Unit infos (no unit)"
            raceteam = ""
            new_img = self.blank_img
            self.e_img.visible = False
            changed = True
        #
        if changed:
            self.e_name.set_text(name)
            self.e_race.set_text(raceteam)
            thorpy.store(self.e_name_and_race, margin=2, gap=2)
            self.e_name_and_race.fit_children()
            self.e_img.set_image(new_img)
            if self.e_img.visible:
                thorpy.store(self.e_group, mode="h")
            else:
                thorpy.store(self.e_group, [self.e_name_and_race], mode="h")
            self.unit = unit


class AlertPool:

    def __init__(self):
        self.alerts = []
        self.countdowns = {} #appear after a while only
        self.frames_on_coord = []

    def add_alert_countdown(self, element, countdown):
        self.countdowns[element] = countdown

    def add_alert(self, element, counter):
        self.alerts.append([element, counter])

    def add_frames_on_coord(self, elements, coord, counter):
        """coord is a coord of the map, not a coord of the screen"""
        self.frames_on_coord.append([elements, coord, counter])

    def refresh(self):
        for i in range(len(self.alerts)-1, -1, -1):
            self.alerts[i][1] -= 1
            if self.alerts[i][1] < 0:
                self.alerts.pop(i)
        for i in range(len(self.frames_on_coord)-1, -1, -1):
            self.frames_on_coord[i][2] -= 1
            if self.frames_on_coord[i][2] < 0:
                self.frames_on_coord.pop(i)
        for e in self.countdowns:
            self.countdowns[e] -= 1

    def draw(self, screen, x, y, gap=5):
        for i in range(len(self.alerts)-1, -1, -1):
            e = self.alerts[i][0]
            e.set_topleft((x,y))
            y += e.get_fus_size()[1] + gap
            e.blit()
        for i in range(len(self.frames_on_coord)-1, -1, -1):
            t = int(self.frames_on_coord[i][2] / 5)
            L = len(self.frames_on_coord[i][0])
            if t < 0:
                t = 0
            elif t >= L:
                t = L - 1
            e = self.frames_on_coord[i][0][t]
            prescribed_coord = self.frames_on_coord[i][1]
            prescribed_coord = self.cam.get_rect_at_coord(prescribed_coord)
            e.set_topleft(prescribed_coord.topleft)
            e.blit()
        for e in self.countdowns:
            if self.countdowns[e] < 0:
                e.set_topleft((x,y))
                e.blit()
                y += e.get_fus_size()[1] + gap




class HelpBox:

    def __init__(self, helps):
        """helps is a list of tuple on the form (title, list_of_help_texts)."""
        elements = []
        for title, texts in helps:
            e_title = guip.get_title(title)
            e_line = thorpy.Line.make(e_title.get_fus_size()[0])
            e_helps = []
            for h in texts:
                e_helps.append(get_help_text_normal(*h))
            elements += [e_line,e_title] + e_helps
        self.e = thorpy.make_ok_box(elements)
        self.b = thorpy.Element.make(size=thorpy.functions.get_screen_size())
        self.b.set_main_color((200,200,200,100))
        self.e.center()
        self.launcher = thorpy.make_button("See commands", self.launch)

    def launch(self):
        self.b.blit()
        pygame.display.flip()
        thorpy.launch_blocking(self.e)
        thorpy.functions.quit_menu_func()


class SettingBox:

    def __init__(self, helps):
        """helps is a list of tuple on the form (title, list_of_help_texts)."""
        elements = []
        for title, texts in helps:
            e_title = guip.get_title(title)
            e_line = thorpy.Line.make(e_title.get_fus_size()[0])
            e_helps = []
            for h in texts:
                e_helps.append(get_help_text_normal(*h))
            elements += [e_line,e_title] + e_helps
        self.e = thorpy.make_ok_box(elements)
        self.b = thorpy.Element.make(size=thorpy.functions.get_screen_size())
        self.b.set_main_color((200,200,200,100))
        self.e.center()
        self.launcher = thorpy.make_button("See commands", self.launch)

        thorpy.make_global_display_options("")

    def launch(self):
        self.b.blit()
        pygame.display.flip()
        thorpy.launch_blocking(self.e)
        thorpy.functions.quit_menu_func()
