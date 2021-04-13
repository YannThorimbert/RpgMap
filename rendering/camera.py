import pygame
from pygame.math import Vector2 as V2
from RpgMap.gui.parameters import RMOUSE_COLOR


##DELTA_STATIC_OBJECTS = [(1,0),(-1,0),(0,-1),(0,1),(0,0),
##                        (1,1), (-1,1), (1,-1), (-1,-1)]
DELTA_STATIC_OBJECTS = [(1,0),(-1,0),(0,-1),(0,1),(0,0)]
class Camera:

    def __init__(self):
        self.lm = None #responsible for drawing map and storing map infos
        self.cell_size = None #in pixels
        self.pos_cells = V2() #in cell units, float! (fraction of cells allowed)
        self.nx, self.ny = 0, 0 #in cell units
        self.map_size_pix = None
        self.me = None
        self.surface = None

    def copy(self, lm):
        c = Camera()
        c.lm = lm
        c.cell_size = self.cell_size
        c.pos_cells = self.pos_cells
        c.nx, c.ny = self.nx, self.ny
        c.map_size_pix = self.map_size_pix
        c.me = self.me
        c.surface = pygame.Surface(self.surface.get_size())
        return c

    def set_parameters(self, world_size, cell_size):
        self.cell_size = cell_size
        self.nx, self.ny = world_size
        self.map_size_pix = (self.nx*self.cell_size, self.ny*self.cell_size)
        self.surface = pygame.Surface((self.me.W, self.me.H))
##        map_size = self.nx*self.cell_size, self.ny*self.cell_size
##        self.map_rect_pix = pygame.Rect((0,0), map_size)
##        self.map_rect_pix.center = self.me.W//2, self.me.H//2

    def reinit_pos(self):
        self.pos_cells = V2()

    def set_map_data(self, lm):
        self.lm = lm
        assert lm.nx == self.nx and lm.ny == self.ny

    def get_pos_cell(self):
        return int(self.pos_cells.x), int(self.pos_cells.y)

    def get_dpix(self):
        """Returns the offset within the current cell"""
##        x = (self.pos_pix.x - self.pos_cells.x)*self.cell_size
##        y = (self.pos_pix.y - self.pos_cells.y)*self.cell_size
        x,y = self.get_pos_cell()
        dx = self.pos_cells.x-x
        dy = self.pos_cells.y-y
        return dx*self.cell_size, dy*self.cell_size

    def draw_map(self, screen, show_grid_lines):
        r = self.get_visible_map_rect()
        xpix, ypix = self.get_dpix()
        self.lm.draw(self.surface, xpix, ypix)
        if show_grid_lines:
            self.draw_grid_lines(self.surface)
        screen.blit(self.surface, r.topleft, r)

    def draw_map_smart(self, screen, show_grid_lines):
        r = self.get_visible_map_rect()
        xpix, ypix = self.get_dpix()
        #
        topleft = self.get_coord_at_pix(r.topleft)
        bottomright = self.get_coord_at_pix(r.bottomright)
##        print("***",topleft, bottomright)
        #
        self.lm.draw_smart(self.surface, xpix, ypix, topleft, bottomright)
        if show_grid_lines:
            self.draw_grid_lines(self.surface)
        screen.blit(self.surface, r.topleft, r)

    def get_visible_map_rect(self):
        x,y = self.get_rect_at_coord((0,0)).topleft
        x2,y2 = self.get_rect_at_coord((self.nx-1, self.ny-1)).bottomright
        return pygame.Rect(x,y,x2-x,y2-y).clip(self.me.screen_rect)

    def draw_grid_lines(self, screen):
        map_rect = self.get_visible_map_rect()
        xpix, ypix = 0, 0
        for x in range(self.nx+1):
            p1 = (map_rect.left+xpix, map_rect.top-20)
            p2 = (map_rect.left+xpix, map_rect.bottom+20)
            pygame.draw.line(screen, (0,0,0), p1, p2)
            xpix += self.cell_size
        for y in range(self.ny+1):
            p1 = (map_rect.left-20, map_rect.top+ypix)
            p2 = (map_rect.right+20, map_rect.top+ypix)
            pygame.draw.line(screen, (0,0,0), p1, p2)
            ypix += self.cell_size

    def refresh_gm_pos(self):
        x,y = self.get_pos_cell()
        self.lm.current_x = x
        self.lm.current_y = y

    def move(self, delta_pix):
        dx_cell = delta_pix[0]/self.cell_size
        dy_cell = delta_pix[1]/self.cell_size
        self.pos_cells += (dx_cell, dy_cell)
##        self.me.game.translate_smokes(delta)
        self.me.game.recompute_smokes_position()

    def get_cell_at_pix(self, pix):
##        if self.map_rect.collidepoint(pix):
        if not self.me.e_box.get_fus_rect().collidepoint(pix): #menu box
            coord = self.get_coord_at_pix(pix)
            return self.me.get_cell_at_coord(coord)

    def center_on_cell(self, coord):
        self.pos_cells = V2(coord)


    def get_rect_at_coord(self, coord):
        dx, dy = self.get_dpix()
        shift_x = (coord[0] - self.lm.current_x) * self.cell_size - int(dx)
        shift_y = (coord[1] - self.lm.current_y) * self.cell_size - int(dy)
        pos = (shift_x,shift_y)
        rect = pygame.Rect(pos, (self.cell_size, self.cell_size))
        return rect

    def get_coord_at_pix(self, pix):
        pos = V2(self.get_dpix()) + pix
        pos.x *= self.nx/self.map_size_pix[0]
        pos.y *= self.ny/self.map_size_pix[1]
        #now pos represents the exact (not integer) coord relative to the first displayed coord !
        deltax, deltay = 0, 0
        if pos.x < 0:
            deltax = -1
        if pos.y < 0:
            deltay = -1
        return (int(pos.x) + self.lm.current_x + deltax,
                int(pos.y) + self.lm.current_y + deltay)

    def get_rect_at_pix(self, pix):
        return self.get_rect_at_coord(self.get_coord_at_pix(pix))

    def log_static_objects_around(self, o, to_sort, drawn_last):
        """Blit the neighboring objects according to their y-coordinate."""
        x,y = o.cell.coord
        s = self.lm.get_current_cell_size()
        for dx,dy in DELTA_STATIC_OBJECTS: #includes 4 neighs + (0,0)
            cell = self.lm.get_cell_at(x+dx, y+dy)
            if cell:
                r = self.get_rect_at_coord(cell.coord)
                for so in cell.objects:
                    if so is not o:
                        if not so.is_ground: #if ground no need to reblit
                            so_rect, so_img = so.get_fakerect_and_img(s)
                            if so.always_drawn_last:
                                drawn_last.add((so_rect,so_img,so))
                            else:
                                to_sort.add((so_rect,so_img,so))

    #How it works:
    #   We collect all the objects to be drawn, plus the static objects around them.
    #   Then, we sort this big list by rect bottom coord, and we draw them.
    def draw_objects(self, screen, objs, draw_ui):
        s = self.lm.get_current_cell_size()
        if draw_ui:
            self.ui_manager.draw_before_objects(s)
        to_sort = set()
        drawn_last = set()
        force_drawn_first = set()
        for o in objs:
            if o.hide:
                continue
            rect, img = o.get_fakerect_and_img(s)
            if o.always_drawn_last:
                drawn_last.add((rect,img,o))
            else:
                if o.is_ground:
                    force_drawn_first.add((rect,img,o))
                elif "bridge" in o.str_type:
                    force_drawn_first.add((rect,img,o))
                else:
                    to_sort.add((rect,img,o))
            self.log_static_objects_around(o, to_sort, drawn_last)
        ########################################################################
        force_drawn_first = [(img,rect) for rect,img,o in force_drawn_first if not o.hide]
        drawn_second = [(img,rect) for rect,img,o in to_sort if not o.hide]
        drawn_second.sort(key=lambda x:x[1][3])
        drawn_last = [(img,rect) for rect,img,o in drawn_last if not o.hide]
        screen.blits(force_drawn_first)
        screen.blits(drawn_second)
        screen.blits(drawn_last)
        if draw_ui:
            self.ui_manager.draw_after_objects(s)



