import pygame, thorpy

def fade_to_black_screen(t=1., n=None, color=(0,0,0), target_alpha=255., fps=60):
    """n = number of steps until black.
    t = time in secondes until black. Excludes n."""
    if n is None:
        n = int(t * fps)
    screen = thorpy.get_screen()
    rect = pygame.Surface(screen.get_size()).convert()
    rect.fill(color)
    clock = pygame.time.Clock()
    for i in range(n+1):
        alpha = min(int(target_alpha * i / n), 255)
        rect.set_alpha(alpha)
        screen.blit(rect, (0,0))
        pygame.display.flip()
        clock.tick(fps)

def fade_from_black_screen(surface,
                        t=1., n=None, color=(0,0,0), target_alpha=255., fps=60):
    """n = number of steps until black.
    t = time in secondes until black. Excludes n."""
    surface = surface.copy()
    if n is None:
        n = int(t * fps)
    screen = thorpy.get_screen()
    rect = pygame.Surface(screen.get_size()).convert()
    rect.fill(color)
    clock = pygame.time.Clock()
    for i in range(n+1):
        screen.blit(surface, (0,0))
        alpha = min(int(target_alpha * i / n), 255)
        rect.set_alpha(255 - alpha)
        screen.blit(rect, (0,0))
        pygame.display.flip()
        clock.tick(fps)

def fade_message(text, font_size=50, font_color=(255,255,255)):
    fade_to_black_screen()
    e = thorpy.make_text(text, font_size, color)
    e.center()
    e.blit()
    e.update()