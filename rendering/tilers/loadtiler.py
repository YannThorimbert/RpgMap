import os
from thorpy._utils.images import load_image
import pygame

class LoadTiler: #emulate a tiler.

    def __init__(self, name, size):
        folder = os.path.dirname(name)
        name = os.path.basename(name)
        self.imgs = {}
        for fn in os.listdir(folder):
            if name in fn:
                img = load_image(os.path.join(folder,fn))
                img = pygame.transform.scale(img,size)
                type_ = fn.split("_")[-1].replace(".png","")
                self.imgs[type_] = img

