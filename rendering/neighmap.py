from RpgMap.thornoise.purepython.noisegen import colorscale_normal
from RpgMap.rendering.camera import Camera

import time
class NeighMap:

    def __init__(self, me, chunk):
        self.me = me
        lm = self.me.lm
        mi = me.map_initializer
##        mi.chunk = chunk
        #
        fast, use_beach_tiler, load_tilers = False, True, False
        self.lm = mi.build_neigh(self.me, chunk)
        self.lm.chunk = chunk
        self.cam = self.me.cam.copy(self.lm)
        self.lm.cam = self.cam
        self.map_initializer = mi
        self.me.add_lm_to_object_dict(self.lm)

    def get_chunk(self):
        return self.lm.chunk
