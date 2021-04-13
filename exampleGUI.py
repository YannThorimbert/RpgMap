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
app = thorpy.Application((W,H))
FPS = 80


def generate_map():
    mi = MapInitializer("First demo map")
##    mi.chunk = (random.randint(0,1000), random.randint(0,1000))
    mi.chunk = (217, 60)
    ####mi = maps.map1 #go in mymaps.py and PLAY with PARAMS !!!
    ##mi.village_homogeneity = 0.1
    mi.seed_static_objects = 230
    wm,hm = 32, 32
    mi.world_size = (wm,hm)
##    mi.set_terrain_type(terrain_plains, colorscale_normal)
    #dont forget to adapt terrain and colorscale to the actual map generated !
    mi.set_terrain_type(terrain_medium, colorscale_normal)
    mi.max_number_of_roads = random.randint(0, 6)
    mi.max_number_of_rivers = random.randint(0, 6)
    mi.zoom_cell_sizes = [32, 16] #two zoom levels
    ##mi.zoom_cell_sizes = [32] #one zoom level
    mi.seed_static_objects = random.randint(0,1000)
    me = mi.configure_map_editor(FPS) #me = "Map Editor"
    img = me.get_hmap_img((wm*10,hm*10))
    return me, img, mi

def refresh():
    global me, mi
    me, img, mi = generate_map()
    me.screen.fill((255,255,255))
    button_img_map.get_elements()[0].set_image(img)
    for button_genmap in buttons:
        button_genmap.blit()
    pygame.display.flip()

button_genmap = thorpy.make_button("Generate another map", refresh)
me, img, mi = generate_map()
button_img_map = thorpy.Clickable(elements=[thorpy.Image(img)])
button_img_map.fit_children()
button_img_map.user_func = thorpy.functions.quit_menu_func
buttons = [button_genmap,button_img_map]
thorpy.store("screen", buttons)
me.screen.fill((255,255,255))
pygame.display.flip()
m = thorpy.Menu(buttons)
m.play()
game = Game(me)

#<fast> : quality a bit lower if true, loading time a bit faster.
#<use_beach_tiler>: quality much better if true, loading much slower.
#<load_tilers> : Very slow but needed if you don't have Numpy but still want HQ.
game.build_map(mi, fast=False, use_beach_tiler=True, load_tilers=False)
me.set_zoom(level=0)

#adding an object that must be drawn before the others on the same cell:
game.set_fire((10,10))
#adding a smoke:
game.add_smoke("large", (10,10))

print(mi.seed_static_objects)
m = thorpy.Menu(me.e_box,fps=me.fps)
m.play()

app.quit()


