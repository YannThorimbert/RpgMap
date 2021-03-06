import random

from RpgMap.mapobjects.objects import MapObject


##def get_river_source_end(md):
##    #1) pick one random end
##    if "shallow water" in md:
##        cell_end = random.choice(md["shallow water"])
##    elif "grass" in md:
##        cell_end = random.choice(md["grass"])
##    elif "snow" in md:
##        cell_end = random.choice(md["snow"])
##    else:
##        return
##    #2) pick one random source
##    if "snow" in md:
##        cell_source = random.choice(md["snow"])
##    elif "thin snow" in md:
##        cell_source = random.choice(md["thin snow"])
##    elif "rock" in md:
##        cell_source = random.choice(md["rock"])
##    else:
##        return
##    return cell_source, cell_end

def get_river_source(md):
    #2) pick one random source
    if "snow" in md:
        cell_source = random.choice(md["snow"])
    elif "thin snow" in md:
        cell_source = random.choice(md["thin snow"])
    elif "rock" in md:
        cell_source = random.choice(md["rock"])
    else:
        return
    return cell_source




def add_river_greedy(me, lm, material_dict, imgs, rounded_river,
                        min_length):
    """Computes and draw a random river."""
    print("     Building random river...")
    cell_source = get_river_source(material_dict)
    if not(cell_source):
        print("no cell source")
        return
    xi,yi = cell_source
    cell_source = lm.cells[xi][yi]
    path = [cell_source]
    cell_xy = cell_source
    maxn = 1000
    it = 0
    should_finish = False
    margin = 0.01
    lake_probability = 0.5
    while True:
        if it > maxn:
            break
        elif "water" in cell_xy.material.name.lower():
            break
        elif should_finish:
            break
        it += 1
        section_length = random.randint(2,10)
        if random.random() < 0.5:
            sign = 1
        else:
            sign = -1
        if random.random() < 0.5:
            dx, dy = sign, 0
        else:
            dx, dy = 0, sign
##        print(dx,dy,section_length)
        ################################################
        for i in range(section_length):
            if should_finish:
                break
            x = cell_xy.coord[0] + dx
            y = cell_xy.coord[1] + dy
            new_cell = lm.get_cell_at(x,y)
            if new_cell is None:
                break
            elif new_cell.h - margin > cell_xy.h:
                if cell_xy.material.name != new_cell.material.name:
                    break
            elif new_cell in path:
                break
            elif new_cell.name != "river":
                is_valid = True
                for neigh in new_cell.get_neighbors_von_neuman():
                    if neigh:
                        if not(neigh is cell_xy):
                            if neigh.name == "river":
                                is_valid = False
                                break
                            elif "water" in neigh.material.name.lower():
                                should_finish = True
                            elif neigh in path:
                                is_valid = False
                                break
                if is_valid:
                    cell_xy = new_cell
                    path.append(new_cell)
##                    print("OK",dx,dy,section_length)
                else:
                    break
            else:
                break
    #4) change the end to first shallow shore cell
    actual_path = []
    for cell in path:
        if cell.name == "river":
            break
        actual_path.append(cell)
        if "water" in cell.material.name.lower():
            break
        else: #LAKE ?
            next_to_water = False
            for neigh in cell.get_neighbors_von_neuman():
                if neigh:
                    if "water" in neigh.material.name.lower():
                        next_to_water = True
                        break
            if next_to_water:
                break
    if len(actual_path) < min_length:
        return
    if actual_path[0].material.name == actual_path[-1].material.name:
        return
    elif not("water" in actual_path[-1].material.name.lower()):
        if random.random() < lake_probability:
            pass
        else:
            return
    #build images of river
    objs = {}
    for delta in imgs: #imgs[(dx,dy)][zoom]
        river_obj = MapObject(me, imgs[delta][0], "river", 1.)
        river_obj.is_ground = True
        river_obj.lm = lm
        objs[delta] = river_obj
    #5) add river cells to map and layer
    for i,cell in enumerate(actual_path):
        prepare_cell_for_river(lm, cell)
        dx,dy,corner = get_path_orientation(i, cell, actual_path)
        if rounded_river:
            c = objs.get((dx,dy,corner))
        else:
            c = objs.get((dx,dy,None))
        if not c:
            raise Exception("No river object for delta", dx, dy, corner)
        assert cell.name != "river"
        c = c.add_copy_on_cell(cell)
        cell.name = "river"
        lm.static_objects.append(c)

    if actual_path:
##        print("RIVER BUILT:", [cell.coord for cell in actual_path])
        if not("water" in actual_path[-1].material.name.lower()):
            for neigh in actual_path[-1].get_neighbors_moore():
                if neigh and neigh.name != "river":
                    prepare_cell_for_river(lm, neigh)
                    river_obj = MapObject(me, imgs[(0,0,None)][0], "river", 1.)
                    river_obj.is_ground = True
                    river_obj.lm = lm
                    river_obj = river_obj.add_copy_on_cell(neigh)
                    neigh.name = "river"
                    lm.static_objects.append(river_obj)
    return objs


def prepare_cell_for_river(lm, cell):
    for o in cell.objects:
        if o.name != "river":
            lm.static_objects.remove(o)
            cell.objects.remove(o)

    above = lm.me.game.get_cell_at(lm.chunk, (cell.coord[0],cell.coord[1]-1))
    if not above: #maybe this is the first initialization (chunk (0,0))
        if cell.coord[1]-1 >= 0:
            above = lm.get_cell_at(cell.coord[0],cell.coord[1]-1)
    if above:
        for o in above.objects:
            if not o.is_ground:
                above.lm.static_objects.remove(o)
                above.objects.remove(o)


##            rect, img = o.get_rect_and_img()
##            ybefore = rect.y
##            rect.bottom = lm.current_gm.get_rect_at_cell(o.cell.coord).bottom
##            relpos = (rect.y - ybefore) / lm.get_current_cell_size()
##            o.min_relpos = [0,relpos]
##            o.max_relpos = [0,relpos]
##            o.randomize_relpos()

def get_path_orientation(i, cell, path):
    dx, dy = 0, 0
    has_previous = False
    has_next = False
    if i > 0: #if there is a previous cell
        dx += cell.coord[0] - path[i-1].coord[0]
        dy += cell.coord[1] - path[i-1].coord[1]
        has_previous = True
    if i + 1 < len(path): #if there is a next cell
        dx += path[i+1].coord[0] - cell.coord[0]
        dy += path[i+1].coord[1] - cell.coord[1]
        has_next = True
    if dx > 0:
        dx = 1
    elif dx < 0:
        dx = -1
    if dy > 0:
        dy = 1
    elif dy < 0:
        dy = -1
    #now determine the corner
    if dx and dy:
        x,y = cell.coord
        if dx>0 and dy>0: #topright or bottomleft
            if has_previous:
                if path[i-1].coord[1] == y:
                    return dx, dy, "topright"
                else:
                    return dx, dy, "bottomleft"
            elif has_next:
                if path[i+1].coord[0] == x:
                    return dx, dy, "bottomleft"
                else:
                    return dx, dy, "topright"
        elif dx>0 and dy<0: #topleft or bottomright
            if has_previous:
                if path[i-1].coord[1] == y:
                    return dx, dy, "bottomright"
                else:
                    return dx, dy, "topleft"
            elif has_next:
                if path[i+1].coord[0] == x:
                    return dx, dy, "topleft"
                else:
                    return dx, dy, "bottomright"
        elif dx<0 and dy>0: #topleft or bottomright
            if has_previous:
                if path[i-1].coord[1] == y:
                    return dx, dy, "topleft"
                else:
                    return dx, dy, "bottomright"
            elif has_next:
                if path[i+1].coord[0] == x:
                    return dx, dy, "bottomright"
                else:
                    return dx, dy, "topleft"
        elif dx<0 and dy<0: #topright or bottomleft
            if has_previous:
                if path[i-1].coord[1] == y:
                    return dx, dy, "bottomleft"
                else:
                    return dx, dy, "topright"
            elif has_next:
                if path[i+1].coord[0] == x:
                    return dx, dy, "topright"
                else:
                    return dx, dy, "bottomleft"
        return dx, dy, None
    else:
        return dx, dy, None