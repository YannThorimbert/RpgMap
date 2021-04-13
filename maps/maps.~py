from PyWorld2D.editor.mapbuilding import MapInitializer, terrain_plains, terrain_flat, terrain_small
from PyWorld2D.thornoise.purepython.noisegen import colorscale_plains, colorscale_flat, colorscale_normal

#Here I simply define some properties of differnt maps. No programmation, just
#configuration.

#For a description of each parameter, please go the file PyWorld2D/editor/mapbuilding.py
#and have a look at the MapInitializer constructor

# ##############################################################################
map0 = MapInitializer("Map0")
map0.chunk = (1400,0)
map0.world_size = (16,16)
##map0.set_terrain_type(terrain_flat, colorscale_flat)
##map0.set_terrain_type(terrain_plains, colorscale_plains)
map0.set_terrain_type(terrain_small, colorscale_normal)
map0.max_number_of_rivers = 1
map0.max_number_of_roads = 1
##map0.h(12,12,"sand")
##for x in range(10):
##    for y in range(10):
##        map0.h(x,y,"sand")

# ##############################################################################
map1 = MapInitializer("First demo map")
map1.chunk = (0,0)
map1.reverse_hmap = True
map1.world_size = (32,32)
map1.set_terrain_type(terrain_plains, colorscale_plains)
##map1.set_terrain_type(terrain_small, colorscale_normal)
map1.max_number_of_roads = 5
map1.max_number_of_rivers = 3
map1.zoom_cell_sizes = [32,]
map1.seed_static_objects = 11
map1.add_object("oak", 6, 5)
map1.add_object("oak", 7, 5)
map1.add_object("oak", 5, 5)
map1.add_object("oak", 6, 6)
map1.add_object("oak", 6, 4)
map1.add_object("oak", 14, 7)
map1.add_object("bridge_h", 13,4)
##map1.add_object("bush", 16, 8)
map1.zoom_cell_sizes = [40,32]



# ##############################################################################
map2 = MapInitializer("Second demo map")
map2.world_size = (64, 32) #with big maps it is better to use lower persistance
map2.persistance = 1.3 #The higher, the bigger are the "continents"
map2.palm_homogeneity = 0.9
map2.chunk = (12345,0)


# ##############################################################################
map3 = MapInitializer("Third demo map")
map3.chunk = (6666,6666)
map3.world_size = (64, 64)
map3.persistance = 1.5
#Note : it is better to start the cells sizes with a power of 2. Then it doesn't matter.
map3.zoom_cell_sizes = [32,20,8]
map3.max_number_of_roads = 0
map1.set_terrain_type(terrain_plains, colorscale_plains)







### ##############################################################################
##map2 = MapInitializer("Second demo map")
##map2.world_size = (256, 128) #with big maps it is better to use lower persistance
##map2.persistance = 1.3 #The higher, the bigger are the "continents"
##map2.palm_homogeneity = 0.9
##map2.chunk = (12345,0)
##
##
### ##############################################################################
##map3 = MapInitializer("Third demo map")
##map3.chunk = (6666,6666)
##map3.world_size = (128,128)
##map3.persistance = 1.5
###Note : it is better to start the cells sizes with a power of 2. Then it doesn't matter.
##map3.zoom_cell_sizes = [32,20,8]
##map3.max_number_of_roads = 0
