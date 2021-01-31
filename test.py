import pygame
import sys


unistr = chr(10_084)
print(pygame.font.get_fonts())
print('segoeuisymbol' in pygame.font.get_fonts())
pygame.font.init()
srf = pygame.display.set_mode((500,500))
f = pygame.font.SysFont('segoeuisymbol',64)
srf.blit(f.render(unistr,True,(255,0,0)),(0,0))
pygame.display.flip()

while True:
    srf.blit(f.render(unistr,True,(255,255,255)),(0,0))
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()