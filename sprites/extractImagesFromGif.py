import thorpy, pygame

app = thorpy.Application((100,100))
e = thorpy.AnimatedGif("./fire2.gif")



name = "extracted"

colors =[(28,)*3]
bckgr = (255,)*3

n = len(e.frames)
n = min(n, 10)
s = pygame.Surface((n*e.frames[0].get_width(),
                    e.frames[0].get_height()))

for i,img in enumerate(e.frames):
    if i >= 10:
        break
    fn = name+str(i).zfill(6)+".png"
    print("Writing ",fn)
    for c in colors:
        thorpy.change_color_on_img_ip(img, c, bckgr)
    thorpy.change_color_on_img_ip(img, img.get_at((0,0)), bckgr)
    s.blit(img,(i*img.get_width(),0))
    pygame.image.save(img, fn)

pygame.image.save(s, name+"spritesheet.png")


app.quit()
