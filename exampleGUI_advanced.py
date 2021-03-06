#First, test the dependecies and show the user a message if smth is missing.
import dependenciescheck as dc
dc.check_console("pygame")
dc.check_console("thorpy") #for GUI and graphic effects - see www.thorpy.org
dc.check_gui("numpy")
dc.check_gui("PIL")
#Now the imports
import random, pygame, thorpy
from logic.game import Game
from RpgMap.editor.mapbuilding import MapInitializer, terrain_medium
from RpgMap.thornoise.purepython.noisegen import colorscale_normal
from RpgMap.sprites.load import get_sprite_frames
from RpgMap.mapobjects.objects import MapObject
#End of imports ################################################################

def generate_map():
    mi = MapInitializer("First demo map")
##    mi.chunk = (random.randint(0,1000), random.randint(0,1000))
    mi.seed = (1310,15)
    mi.chunk_size = (64,64) #size of a chunk
##    mi.set_terrain_type(terrain_plains, colorscale_normal)
    #dont forget to adapt terrain and colorscale to the actual map generated.
    mi.set_terrain_type(terrain_medium, colorscale_normal)
    mi.max_number_of_roads = 0
    mi.max_number_of_rivers = 4
    mi.min_river_length = 12
##    mi.zoom_cell_sizes = [32, 16] #two zoom levels
    mi.zoom_cell_sizes = [64] #one zoom level
    me = mi.configure_map_editor(FPS) #me = "Map Editor"
    img = me.get_hmap_img((mi.chunk_size[0]*10,mi.chunk_size[1]*10))
    return me, img, mi

def refresh():
    global me, mi
    me, img, mi = generate_map()
    me.screen.fill((255,255,255))
    img = thorpy.get_resized_image(img, (300,300))
    button_img_map.get_elements()[0].set_image(img)
    for button_genmap in buttons:
        button_genmap.blit()
    pygame.display.flip()

W,H = 1000, 700 #screen size
app = thorpy.Application((W,H))
FPS = 80

button_genmap = thorpy.make_button("Generate another map", refresh)
me, img, mi = generate_map()
img = thorpy.get_resized_image(img, (300,300))
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

#creating a new type of structure:
##windmill_imgs = get_sprite_frames("sprites/windmill_idle.png")
##windmill = MapObject(me, windmill_imgs, "windmill")
##windmill.set_animation_speed("midslow")
##windmill.min_relpos = [0, -0.15]
##windmill.max_relpos = [0, -0.15]
##windmill.randomize_relpos()
#add the created structure
##game.add_object((3,3), windmill, 1)
##game.add_object((5,3), windmill, 1)

#adding fire:
##game.set_fire((10,10), ("village","forest","windmill"))
#adding a smoke:
##game.add_smoke("large", (10,10))

me.refresh_neigh_maps()

m = thorpy.Menu(me.e_box,fps=me.fps)
m.play()

app.quit()


#CAMPAGNE DE DEBOGUAGE FONDAMENTAL

#F)
##checker les xx


#CAMPAGNE DE NETTOYAGE FONDAMENTAL

#voir xx custom

#lac de riviere doit pas avoir de cellules voisines a une riviere....

#blit_intelligent a enorm??ment d'overlaps ! comment les ??viter ?

#tous les objets sont toujours statiques. a chaque fois qu'on pose un objet, on reblitte les voisins. que des petites listes a trier.

#map slownesses : centralisees dans structure a part
#synchro des frames eau
#arreter d'appeler autre chose que draw as neigh dans func_reac_time

#petit a petit, au moment du blit des objets, bliter en statique. Tout est fait dans mapgrid pour un reblit optimise des statiques en zbuffer.

#static object existe plus ?
#draw objects : faire + rapide que "bridge" etc.

#utiliser numpy uniquement ! ?...
#normaliser par une constante (qui est une fonction des octaves!?) et controler les overflow : parametriser


#zoom a corriger
#refaire sur screen directement et mesurer impact
################################################################################
################################################################################

#bugs mouse navigation
#bug click droit, affichage trop haut
#virer is_main, heights
#pour les arbres, on va plutot faire un bouge feuille al??atoire, avec un reblit d'une cellule de temps ?? autres

#lac : transformer en VRAI shallow qui bouge et qui est ground, sinon moche
#faire un lac si riviere finit pas dans water : taille et forme du lac
#chemin est inverse d'une riviere : minimise le changement d'altitude
#bug fumee
#rename Game -> Map
#ce qui est fait dans custom devrait etre fait dans le main de l'exemple !

#finir propre le custom
#add static/dynamic objects

#ombres, reflets et fleurs. + d'objets statiques anim??s (windmill statique, add?)
#adapter riviere/chemins params a taille carte. Faire sur grille grossi??re, puis chercher de point a point a + petite echelle...

#enlever unit juste pour le git
#adapter gui

#opti : basegrid utilise la periodicite. Si on enleve ??a, peut gagner qques operations.

#map de static peut etre moins bien resolue, puis interpolation