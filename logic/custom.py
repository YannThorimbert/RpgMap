import os
from RpgMap.mapobjects.distributors import DistributionDescriptor


###all static forest sprites must be located in FN_STRUCTURES folder

#Declare the collection of static objects for a forest
#We specify the objects that can be spawn on rock and grass terrains.
forest = DistributionDescriptor("forest", apply_to=["Rock", "Grass"])
forest.zones_spread = [(0.5,0.2)]
forest.add("tree2.png", 1.5)
forest.add("tree3.png", 1.5)
forest.add("tree4.png", 1.5)
forest.add("tree5.png", 1.5)
forest.add("tree6.png", 1.5)
forest.add("tree7.png", 1.5)

forest_grass = DistributionDescriptor("forest", ["Grass"])
forest_grass.homogeneity = 0.6
forest.zones_spread = [(0.5,0.2)]
forest_grass.add("tree1.png", 1.5, max_relpos=[0.2,0.2], min_relpos=[-0.2,-0.2])

forest_snow = DistributionDescriptor("forest", ["Snow", "Thin snow"])
forest_snow.homogeneity = 0.5
forest_snow.zones_spread = [(0.5,0.2)]
forest_snow.add("tree8.png", 1.5, max_relpos=[0.2,0.2], min_relpos=[-0.2,-0.2])

forest_palm = DistributionDescriptor("forest", ["Sand"])
forest_palm.homogeneity = 0.5
forest_palm.zones_spread = [(0., 0.05), (0.3,0.05), (0.6,0.05)]
forest_palm.add("tree9.png", 1.7, max_relpos=[0.1,0.], min_relpos=[-0.1,0.])

bush = DistributionDescriptor("bush", ["Grass", "Rock"])
bush.max_density = 2
bush.homogeneity = 0.05
bush.zones_spread = [(0., 0.05), (0.3,0.05), (0.6,0.05)]
bush.add("tree10.png", max_relpos=[0.4,0.4], min_relpos=[-0.4,-0.4])


village = DistributionDescriptor("village", ["Grass", "Snow", "Sand"])
village.homogeneity = 0.5 #xxmettre une option pour empecher les filaments (nmax de villages par distributor)
village.zones_spread = [(0.8,0.01), (0.2,0.01)]
village.add("house0.png", 1.2, min_relpos=[0,0.01], max_relpos=[0,0.15])



distributions = [forest, forest_grass, forest_snow, forest_palm, bush, village]


#every static object has:
    #fn
    #size multiplier
    #max_relpos, min_relpos
    #is_ground
