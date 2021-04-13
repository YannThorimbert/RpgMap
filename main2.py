"""
Fantasy Strategia - A 2D, turn-based strategy game in a fantasy universe.
(C) Yann Thorimbert - 2020
yann.thorimbert@gmail.com
"""


################################################################################
############################ OBJECTIF IMMEDIAT #################################
################################################################################

################################################################################
#TEST !! - V a1

##laisser tomber fakebattle et utiliser une heuristique, car tte facon marche pas

#windmill static (TOUT EST PRET)

#visualiser zone de danger
#son celebration
#reserver channel fire
#load/save
#editeur terrain
#preprocess gui davantage

##toujours possible d'annuler un deplacement si rien d'autre n'a ete fait depuis (comme dans aw)
#ajouter objets en statiques car tte façon mieux pour perfs !!!

#en 64pixels, disp des battle marchent pas.
#temps de construction depend de la sante de celui qui construit ?

#plus belles attaques, mais problem timing. Gros impact sur FakeBattle !!!

#refaire thorpy avec le seul changement que on enleve tous les pygame.update. C'est l'utilisateur qui fait un flip.
#et il n'y a pas de unblit. On reblit tout chaque frame.

#virer InteractiveObject : ne sert a rien !!! (cf windmills)
#==> remove_from_game devient remove_unit_from_game

#remettre l'altitude, et compte dans bataille ! Mais pas l'altitude par cell : juste l'altitude correspondant au material, sinon pas assez lisible au niveau gameplay

#archers en priorite !!! (implique d'attacher fumee et sons aux classes de projectils)

#faire unite = joueur = stratege/general sur un cheval

##Mettre des monuments (objets comme drapeaux mais avec image differente) qui augmentent le prestige(rayonnement).
## rayonnement = somme( 1. / distance à capitale ennemie de chaque monument). Les monuments coutent cher et sont construits par villageois/ouvriers?.

#Population~nourriture, or~population*impots, rayonnement~monuments, crainte/respect~choix (viols etc)
#couper bois ? ressourece bois, avec camp de bucherons ?

#barre de choix d'impots : (c = curseur)
##Low tax, raise people popularity <------c----------------> High tax, lower people popularity

#pour augmenter le respect, il faut soi-même participer aux batailles de temps a autres
#2 popularites : celle du peuple (people popularity) et celle de l'armee (army popularity)
# case a cocher : allow rapes, allow pillages, ==> curseur entre celle du peuple et de l'armee

#au final, la popularite totale (armee + people) determine:
##    *les rebellions spontanees (villages soudain neutres)
##    *si on peut debloquer certains unites/fonctions/ameliorations

#murailles: au niveau de l'implementation, sont des types d'unites! (static unit)
#       Les chateaux sont juste des villages entoures de murailles
#dans l'editeur, set_material fera en realite un set_height !

#rappel : il n'y a pas de haches/epees/lances etc ; c'est la race qui change ca dans sa propre infanterie !!!

#certaines unites ne sont produites que dans les donjons : (arch)wizards, kings, ...

#impots, incendie, viols ==> depend de ce qu'on cherche a avoir, de la popularite
#       aupres de ses soldats deja existants ou bien des futurs ressortissants des villes prises
#3 scores : score militaire, score moral, score economique

#chateaux : villages/donjons entoures de murailles, avec armes de jet a l'interieur


################################################################################



from __future__ import print_function, division

import dependenciescheck as dc
dc.check_console("thorpy")
dc.check_gui("numpy")
dc.check_gui("PIL")

import pygame
import thorpy #for GUI and other graphics - see www.thorpy.org

##import maps.maps as maps
import gui.gui as gui
from logic.races import Race, LUNAR, STELLAR, SOLAR
from logic.game import Game, get_sprite_frames
import gui.theme as theme
from logic.player import Player
################################################################################

theme.set_theme("round")

W,H = 1200, 700 #screen size
app = thorpy.Application((W,H))

##W,H = thorpy.functions.get_max_screen_size()
##app = thorpy.Application((W,H), flags=pygame.FULLSCREEN)

FPS = 60

####mi = maps.map1 #go in mymaps.py and PLAY with PARAMS !!!
##maps.map1.chunk = (1322, 43944)
##maps.map1.max_number_of_roads = 5 #5
##maps.map1.max_number_of_rivers = 5 #5
##maps.map1.village_homogeneity = 0.1
##maps.map1.seed_static_objects = 15
##maps.map1.zoom_cell_sizes = [32]
##
##
##for mi in [maps.map1, maps.map0, maps.map2, maps.map3]:
##    me = mi.configure_map_editor(FPS) #me = "Map Editor"
##    app.get_screen().fill((0,0,0))
##    me.show_hmap()

import random
from PyWorld2D.editor.mapbuilding import MapInitializer, terrain_plains, terrain_flat, terrain_small, terrain_medium
from PyWorld2D.thornoise.purepython.noisegen import colorscale_plains, colorscale_flat, colorscale_normal

def generate_map():
    mi = MapInitializer("First demo map")
    mi.chunk = (random.randint(0,1000), random.randint(0,1000))
    wm,hm = 32,32
    mi.world_size = (wm,hm)
##    mi.set_terrain_type(terrain_plains, colorscale_normal)
    mi.set_terrain_type(terrain_medium, colorscale_normal)
    mi.max_number_of_roads = random.randint(0, 6)
    mi.max_number_of_rivers = random.randint(0, 6)
    mi.zoom_cell_sizes = [32, 16]
    mi.seed_static_objects = random.randint(0,1000)
    me = mi.configure_map_editor(FPS) #me = "Map Editor"
    img = me.get_hmap_img((wm*10,hm*10))
    print("CHUNK", mi.chunk, mi.seed_static_objects)
    return me, img, mi

def refresh():
    global me, mi
    me, img, mi = generate_map()
    me.screen.fill((255,255,255))
    ei.get_elements()[0].set_image(img)
    for e in els:
        e.blit()
    pygame.display.flip()

e = thorpy.make_button("Generate another map", refresh)
me, img, mi = generate_map()
ei = thorpy.Clickable(elements=[thorpy.Image(img)])
ei.fit_children()
ei.user_func = thorpy.functions.quit_menu_func
els = [e,ei]
me.screen.fill((255,255,255))
pygame.display.flip()
thorpy.store("screen", els)
m = thorpy.Menu(els)
m.play()

game = Game(me)


humans = Race("Coco", "human", LUNAR, me, "green", team=1) #LUNAR, STELLAR or SOLAR
humans.dist_factor = 10
humans.finalize() #always call this function to finish initialize a race !!!

humans2 = Race("Turtudur Buldur", "human", LUNAR, me, "blue", team=2)
humans2.dist_factor = 10
humans2.finalize()

players = [ Player(1, humans.name, humans),
            Player(2, humans2.name, humans2)]
game.set_players(players)

#<fast> : quality a bit lower if true, loading time a bit faster.
#<use_beach_tiler>: quality much better if true, loading much slower. Req. Numpy!
#<load_tilers> : Very slow but needed if you don't have Numpy but still want hi quality.
game.build_map(mi, fast=False, use_beach_tiler=True, load_tilers=False)


def add_unit(pn, unit_type, near_what):
    nx,ny = game.get_map_size()
    unit = game.players[pn].race[unit_type]
    unit.team = game.players[pn].race.team
    for v in game.get_all_objects_by_str_type(near_what):
        flag = game.get_object("flag", v.cell.coord)
        if flag:
            team = flag.team
        else:
            team = None
        if team == unit.team:
            dx,dy = random.choice([(-1,0),(1,0),(0,-1),(0,1),(0,0)])
            cell = game.get_cell_at(v.cell.coord[0]+dx,v.cell.coord[1]+dy)
            if cell:
                if not cell.unit:
                    if cell.name != "river":
                        if not("water" in cell.material.name.lower()):
                            game.add_unit((v.cell.coord[0]+dx,v.cell.coord[1]+dy), unit, 20)
                            return
    if not list(game.get_units_of_player(game.players[pn])):
        for x in range(nx):
            for y in range(ny):
                cell = game.get_cell_at(x,y)
                if not cell.objects:
                    if cell.name != "river":
                        if not("water" in cell.material.name.lower()):
                            if random.random() < 0.5:
                                game.add_unit((x,y), unit, 20)
                                return

for i in range(2):
    for unit in ["villager", "infantry"]:
        for team in [0,1]:
            add_unit(team, unit, "village")

ui = gui.Gui(game)
me.set_zoom(level=0)
game.check_integrity()
game.set_ambiant_sounds(True)
game.initialize_money(200, compensation=5)

dans roundtiler.py et autres, optimiser : x-x0**2 dans les boucles peut etre calcule en avance ! Dans tous les tilers !
De +, travailler avec les carrés plutôt qu'avec la racine

m = thorpy.Menu(me.e_box,fps=me.fps)
m.play()

app.quit()
