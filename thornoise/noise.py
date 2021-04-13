from __future__ import print_function, division
import random, math
import matplotlib.pyplot as plt

def generate_constraints(n_octaves, S, chunk):
    """Generates random height constraints used by terrain generation.
    THIS IS NOT THE ACTUAL TERRAIN GENERATION FUNCTION."""
    min_res = int(S / 2**(n_octaves-1))
    hmap_size = S//min_res + 1
    random.seed(chunk)
    h = [[random.random() for x in range(hmap_size)] for y in range(hmap_size)]
    #
    XCOORD, YCOORD = chunk
    #left
    random.seed((XCOORD,YCOORD))
    for y in range(hmap_size):
        h[0][y] = random.random()
    #right
    random.seed((XCOORD+1,YCOORD))
    for y in range(hmap_size):
        h[-1][y] = random.random()
    #top
    random.seed((XCOORD,YCOORD))
    for x in range(hmap_size):
        h[x][0] = random.random()
    #bottom
    random.seed((XCOORD,YCOORD+1))
    for x in range(hmap_size):
        h[x][-1] = random.random()
    random.seed((XCOORD,YCOORD))
    h[0][0] = random.random()
    random.seed((XCOORD+1,YCOORD+1))
    h[-1][-1] = random.random()
    random.seed((XCOORD,YCOORD+1))
    h[0][-1] = random.random()
    random.seed((XCOORD+1,YCOORD))
    h[-1][0] = random.random()
    return h, min_res

def generate_terrain(size, n_octaves=None, chunk=(0,0), persistance=2.):
    """Returns a <S> times <S> array of heigth values for <n_octaves>, using
    <chunk> as seed."""
    S = size
    if n_octaves is None: #automatic max number of octaves
        n_octaves = int(math.log(S,2))
    h, min_res = generate_constraints(n_octaves, S, chunk) #h is the hmap constraint
    terrain = [[0. for x in range(S)] for y in range(S)] #actual heightmap
    res = int(S) #resolution for the current octave
    step = res//min_res #space step in pixels for the current octave
    change_cell = True #indicates when polynomial coeffs have to be recomputed
    amplitude = persistance
    for i in range(n_octaves):
        delta = 1./res #size of current cell
        x_rel = 0. #x-pos in the current cell
        for x in range(S): #here x is coord of pixel
            y_rel = 0. #y-pos in the current cell
            x2 = x_rel*x_rel;
            smoothx = 3.*x2 - 2.*x_rel*x2;
            for y in range(S):
                y2 = y_rel*y_rel
                smoothy = 3.*y2 - 2.*y_rel*y2
                diag_term = x_rel*y_rel - smoothx*y_rel - smoothy*x_rel
                if change_cell:
                    idx0, idy0 = int(x/res)*step, int(y/res)*step
                    idx1, idy1 = idx0+step, idy0+step
                    h00 = h[idx0][idy0]
                    h01 = h[idx0][idy1]
                    h10 = h[idx1][idy0]
                    h11 = h[idx1][idy1]
                    #
                    dx = h10 - h00
                    dy = h01 - h00
                    A = dx - h11 + h01
                    change_cell = False
                dh = h00 + smoothx*dx + smoothy*dy + A*diag_term
                terrain[x][y] += amplitude*dh
                #
                y_rel += delta
                if y_rel >= 1.: #periodicity
                    change_cell = True
                    y_rel = 0.
            x_rel += delta
            if x_rel >= 1.: #periodicity
                change_cell = True
                x_rel = 0.
        res //= 2
        step = res//min_res
        amplitude /= persistance
    return terrain

def normalize(terrain):
    """Normalize in place the values of <terrain>."""
    M = max([max(line) for line in terrain])
    m = min([min(line) for line in terrain])
    S = len(terrain)
    for x in range(S):
        for y in range(S):
            terrain[x][y] = (terrain[x][y] - m)/(M-m)
    return terrain


resolution = 128
terrain = generate_terrain(size=resolution, n_octaves=8, persistance=1.5)
normalize(terrain)
#here we add an offset (don't add offset if you just want natural noise)
offset_amplitude = -2.5/resolution
for x in range(resolution):
    for y in range(resolution):
        terrain[x][y] += x*offset_amplitude
plt.imshow(terrain, cmap="Blues")
plt.show()
#note: matplotlib swap the axes compared to the matrix format used here
#cool cmaps for terrain : "terrain", "gist_earth", ... (see https://matplotlib.org/users/colormaps.html)
