import pygame

def get_sprite_frames(fn, deltas=None, s=32, ckey=(255,255,255),
                        resize_factor=None):
    imgs = []
    sprites = pygame.image.load(fn)
    if s == "auto":
        s = sprites.get_width()
    n = sprites.get_width() // s
    h = sprites.get_height()
    if resize_factor:
        s = int(resize_factor*s)
        w,h = sprites.get_size()
        w = int(resize_factor*w)
        h = int(resize_factor*h)
        sprites = pygame.transform.scale(sprites, (w,h))
    if not deltas:
        deltas = [(0,0) for i in range(n)]
    x = 0
    print("Loading sprites", n, s, h, fn)
    for i in range(n):
        surf = pygame.Surface((s,h))
        surf.fill(ckey)
        surf.set_colorkey(ckey)
        dx, dy = deltas[i]
        surf.blit(sprites, (dx,dy), pygame.Rect(x,0,s,h))
        imgs.append(surf)
        x += s
    return imgs