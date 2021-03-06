import os, random
import RpgMap.logic.constants as const
from RpgMap.mapobjects.objects import MapObject

def put_static_obj(obj, lm, coord, layer):
    cop = obj.add_copy_on_cell(lm[coord])
    layer.static_objects.append(cop)
    return cop

def remove_objects_from_layer(cell, layer):
    if cell.objects:
        for obj in cell.objects:
            layer.static_objects.remove(obj)
        cell.objects = []

class DistributionDescriptor:

    def __init__(self, name, apply_to):
        self.descriptors = {}
        self.objects = None
        self.apply_to = apply_to
        self.name = name
        self.max_density = 1 #number of time an object can be added to a cell
        self.homogeneity = 0.2 #probability of actually adding 1 object to a cell
        self.zones_spread = [(0.,1.)] #Seq. of (altitude, altitude_spread)
        self.exclusive = True
        #e.g : (0.5, 0.2) means you will find this object from h=0.3 to h=0.7

    def get(self, name):
        return self.descriptors(name)

    def add(self, fn, size_multiplier=1., max_relpos=(0,0), min_relpos=(0,0),
            is_ground=False, flip=True):
        od = ObjectDescriptor(fn, size_multiplier, max_relpos, min_relpos,
                            is_ground, flip)
##        if self.name == "caca":
##            print(od.max_relpos, od.min_relpos)
##            assert False
        self.descriptors[od.name] = od #silently replace existing ones !

    def build_objects(self, me):
        self.objects = []
        for od in self.descriptors.values():
            o = od.build_object(me, self.name)
##            if self.name == "caca":
##                print(od.max_relpos, od.min_relpos)
##                print(o.name, o.max_relpos, o.min_relpos)
##                assert False
            self.objects.append(o)
            if o.flip:
                self.objects.append(o.flip())

##    def set_objects_lm(self, lm):
##        for o in self.objects:
##            o.lm = lm

    def get_distributor(self, me, lm, omap):
        distributor = get_distributor(me, lm, self.objects, omap, self.apply_to,
                                        limit_relpos_y=False)
        distributor.max_density = self.max_density
        distributor.homogeneity = self.homogeneity
        distributor.zones_spread = self.zones_spread
        return distributor

class ObjectDescriptor:

    def __init__(self, fn, size_multiplier, max_relpos, min_relpos, is_ground,
                    flip):
        self.fn = os.path.join(const.FN_STRUCTURES, fn)
        self.size_multiplier = size_multiplier
        self.max_relpos = list(max_relpos)
        self.min_relpos = list(min_relpos)
##        if max_relpos[0] or max_relpos[1] or min_relpos[0] or min_relpos[1]:
##            self.randomize_relpos = True
##        else:
##            self.randomize_relpos = False
        self.is_ground = is_ground
        self.name = self.fn.split(".")[0]
        self.flip = flip

    def build_object(self, me, txt):
        o = MapObject(me, self.fn, txt, self.size_multiplier)
        o.max_relpos = [self.max_relpos[0],self.max_relpos[1]]
        o.min_relpos = [self.min_relpos[0],self.min_relpos[1]]
        o.is_ground = self.is_ground
##        if self.randomize_relpos:
##            o.randomize_relpos()
        return o



def get_distributor(me, lm, objects, forest_map, material_names,
                    limit_relpos_y=True):
    if limit_relpos_y: #then the max_relpos is set according to obj's factor
        for obj in objects:
            obj.max_relpos[1] = (1. - obj.factor)/2.
            if obj.min_relpos[1] > obj.max_relpos[1]:
                obj.min_relpos[1] = obj.max_relpos[1]
    distributor = RandomObjectDistribution(objects, forest_map, lm)
    for name in material_names:
        if name in me.materials:
            distributor.materials.append(me.materials[name])
    distributor.max_density = 3
    distributor.homogeneity = 0.75
    distributor.zones_spread = [(0.1, 0.02), (0.5,0.02), (0.9,0.02)]
    return distributor

class RandomObjectDistribution:

    def __init__(self, objs, hmap, master_map):
        self.objs = objs
        self.hmap = hmap
        self.master_map = master_map
        assert master_map.nx <= len(hmap) and master_map.ny <= len(hmap[0])
        self.materials = []
        self.max_density = 1
        self.homogeneity = 0.5
        self.zones_spread = [(0.,1.)]


    def distribute_objects(self, lm, exclusive=False):
        """If exclusive is True, will remove all other objects on cell"""
        nx,ny = self.master_map.nx, self.master_map.ny
        dx, dy = random.randint(0,nx-1), random.randint(0,ny-1)
        for x,y in self.master_map:
            h = self.hmap[(x+dx)%nx][(y+dy)%ny]
            right_h = False
            for heigth,spread in self.zones_spread:
                if abs(h-heigth) < spread:
                    right_h = True
                    break
            if right_h:
                cell = self.master_map.cells[x][y]
                if cell.material in self.materials:
                    if exclusive: #remove all other objects
                        remove_objects_from_layer(cell, lm)
                    for i in range(self.max_density):
                        if random.random() < self.homogeneity:
                            obj = random.choice(self.objs)
                            obj = obj.add_copy_on_cell(cell)
                            obj.lm = lm
                            obj.is_static = True
                            obj.randomize_relpos()
                            lm.static_objects.append(obj)

def simple_distribution(me, objs, materials, n):
    lm = me.lm
    ntry = 10*n
    counter = 0
    nx,ny = lm.nx, lm.ny
    for i in range(ntry):
        if counter > n:
            return
        x = random.randint(0,nx-1)
        y = random.randint(0,ny-1)
        cell = lm.get_cell_at(x,y)
##        print("***Trying", x, y, cell)
        if cell:
##            print("     ", cell.material.name, materials)
            if cell.material.name in materials:
                remove_objects_from_lm(cell, lm)
                obj = random.choice(objs)
                obj = obj.add_copy_on_cell(cell)
                obj.is_static = True
                obj.max_relpos = [0.1, 0.1]
                obj.min_relpos = [-0.1, 0.1]
                obj.randomize_relpos()
                lm.static_objects.append(obj)
                counter += 1

##class RandomInteractiveObjectDistribution:
##
##    def __init__(self, objs, hmap, master_map):
##        self.objs = objs
##        self.hmap = hmap
##        self.master_map = master_map
##        assert master_map.nx <= len(hmap) and master_map.ny <= len(hmap[0])
##        self.materials = []
##        self.max_density = 1
##        self.homogeneity = 0.5
##        self.zones_spread = [(0.,1.)]
##
##    def distribute_objects(self, game, n_per_cell=1, rand_relpos=True):
##        nx,ny = self.master_map.nx, self.master_map.ny
##        dx, dy = random.randint(0,nx-1), random.randint(0,ny-1)
##        for x,y in self.master_map:
##            h = self.hmap[(x+dx)%nx][(y+dy)%ny]
##            right_h = False
##            for heigth,spread in self.zones_spread:
##                if abs(h-heigth) < spread:
##                    right_h = True
##                    break
##            if right_h:
##                cell = self.master_map.cells[x][y]
##                if cell.material in self.materials:
##                    for i in range(self.max_density):
##                        if random.random() < self.homogeneity:
##                            obj = random.choice(self.objs)
##                            game.add_object((x,y), obj, n_per_cell, rand_relpos)