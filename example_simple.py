#First, test the dependecies and show the user a message if smth is missing.
import dependenciescheck as dc
dc.check_console("pygame")
dc.check_console("thorpy") #for GUI and graphic effects - see www.thorpy.org
dc.check_gui("numpy")
dc.check_gui("PIL")
#Now the imports
import random, pygame, thorpy
from logic.game import Game
from PyWorld2D.editor.mapbuilding import MapInitializer, terrain_medium
from PyWorld2D.thornoise.purepython.noisegen import colorscale_normal
#End of imports ################################################################

W,H = 1200, 700 #screen size
FPS = 80
pygame.init()
screen = pygame.display.set_mode((W,H))

mi = MapInitializer("First demo map")
mi.chunk = (random.randint(0,1000), random.randint(0,1000))
wm,hm = 32,16
mi.world_size = (wm,hm)
mi.set_terrain_type(terrain_medium, colorscale_normal)
mi.max_number_of_roads = random.randint(0, 6)
mi.max_number_of_rivers = random.randint(0, 6)
mi.zoom_cell_sizes = [32, 16]
mi.seed_static_objects = random.randint(0,1000)
me = mi.configure_map_editor(FPS) #me = "Map Editor"
img = me.get_hmap_img((wm*10,hm*10))
game = Game(me)

#<fast> : quality a bit lower if true, loading time a bit faster.
#<use_beach_tiler>: quality much better if true, loading much slower.
#<load_tilers> : Very slow but needed if you don't have Numpy but still want HQ.
game.build_map(mi, fast=False, use_beach_tiler=True, load_tilers=False)
me.set_zoom(level=0)

##game.set_fire((3,7))
##game.add_smoke("large",(4,4))

clock = pygame.time.Clock()
done = False
while not done:
    clock.tick(FPS)
    screen.fill((0,0,0))
    me.cam.draw_grid(screen, show_grid_lines=False)
    me.cam.draw_objects(screen, me.dynamic_objects, draw_ui=False)
    game.refresh_smokes()
    game.t += 1
    me.lm.next_frame()
    pygame.display.flip()
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            done = True



pygame.quit()
