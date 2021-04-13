class State(object):
    """
    Generic datatype for storing a state.
    A state is defined by:
        - its cell
        - its parent state (i.e the (unique) state whose child is self).
        - its cost so far (note that this is redundant, since it could be computed
          from parents, but here we explicitly compute it each time a Solution
          is created).
    """

    def __init__(self, cell, parent, time_so_far):
        self.cell = cell
        self.parent = parent
        self.time_so_far = time_so_far

    def get_all_parents(self):
        if self.parent:
            return self.parent.get_all_parents() + [self.cell]
        else:
            return [self.cell]


class BranchAndBoundForMap:
    def __init__(self, lm, cell_i, cell_f, costs_materials, costs_objects,
                 possible_materials, possible_objects):
        self.lm = lm
        self.cell_i = cell_i
        self.cell_f = cell_f
        self.costs_materials = costs_materials
        self.costs_objects = costs_objects
        self.possible_materials = possible_materials
        self.possible_objects = possible_objects
        self.lnl = [] #lnl = Live Nodes List
        self.enode = None #enode = Expanding-Node

    def cost(self, state):
        return self.distance(state) + state.time_so_far

    def distance(self, state):
        x0,y0 = state.cell.coord
        dx = abs(x0 - self.cell_f.coord[0])
        dy = abs(y0 - self.cell_f.coord[1])
        return dx + dy

    def get_children(self, state):
        x, y = state.cell.coord
        children = []
        up = self.lm.get_cell_at(x,y-1)
        down = self.lm.get_cell_at(x,y+1)
        right = self.lm.get_cell_at(x+1,y)
        left = self.lm.get_cell_at(x-1,y)
        for cell in [up,down,right,left]:
            if cell:
                obj_type = None
                possible = False
                if cell.objects:
                    obj_type = cell.objects[0].int_type
                    if obj_type in self.possible_objects:
                        possible = True #e.g, bridge is on material water!
                else:
                    possible = True
                if possible:
                    really_possible = False
                    time = 0.
                    if cell.objects:
                        time += self.costs_objects.get(obj_type,0.)
                        really_possible = True
                    elif cell.material.name in self.possible_materials:
                        time += self.costs_materials.get(cell.material.name,0.)
                        really_possible = True
##                    elif cell.objects:
##                        really_possible = True
                    if really_possible:
                        child = State(cell, state, state.time_so_far + time)
                        children.append(child)
        return children

    def solve(self):
        solution = self.process()
        #
        if solution is None:
            return []
        return solution.get_all_parents()

    def process(self):
        initial_state = State(self.cell_i, None, self.costs_materials[self.cell_i.material.name])
        self.lnl = [initial_state]
        self.enode = self.lnl.pop()
        already = set([self.enode.cell.coord])
        i = 0
        while True:
##            print(self.enode.cell.coord, self.distance(self.enode))
            if self.distance(self.enode) == 0:
                return self.enode
            else:
                if i > 1e5:
                    return
                self.lnl += self.get_children(self.enode)
                if not self.lnl:
                    return
                else:
                    #sort the lnl and reverse so that default pop function can be called
                    self.lnl.sort(key=self.cost, reverse=True)
                    #updates enode
                    self.enode = self.lnl.pop()
                    while self.enode.cell.coord in already and self.lnl:
                        self.enode = self.lnl.pop()
                    already.add(self.enode.cell.coord)
                    i += 1
