from constants import *

import os
import pygame

os.environ['SDL_VIDEO_WINDOW_POS'] = '100,100'
pygame.init()  # Инициализация движка pygame
SIZE = WIDTH, HEIGHT = (360, 400)
screen = pygame.display.set_mode(SIZE)
MAP_WIDTH = MAP_HEIGHT = 800


class PLayer(pygame.sprite.Sprite):
    def __init__(self, x, y, is_reversed: bool, *groups):
        super().__init__(*groups, players)

        self.image = load_image(f"{DATA_DIR}/images/player/player_walk1.png")
        if is_reversed:
            self.image = pygame.transform.flip(self.image, True, False)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y


if __name__ == '__main__':
    fps = 60  # количество кадров в секунду
    clock = pygame.time.Clock()
    running = True

    players = pygame.sprite.Group()
    player1 = PLayer(0, 0, False)
    player2 = PLayer(0, 40, True)

    # camera = Camera(game_map.player, game_map.map)

    while running:  # главный игровой цикл
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # обработка остальных событий
            # ...

        # формирование кадра
        # ...

        screen.fill(white)
        players.draw(screen)

        # изменение игрового мира
        # ...

        pygame.display.flip()  # смена кадра

        # временная задержка
        clock.tick(fps)
