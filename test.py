from game import *
from constants import *

import pygame

pygame.init()  # Инициализация движка pygame

MAP_WIDTH = MAP_HEIGHT = 800


class Camera:
    def __init__(self, main_player: pygame.sprite.Sprite, sprites: (list, tuple)):
        assert isinstance(main_player, Player), \
            'Error. Camera get non Player object as main_player parameter'

        self.camera_size = (800, 600)
        self.edge_percent = 0.8
        self.start_zone = pygame.Rect([0, 0, *self.camera_size])
        self.camera_rect = pygame.Rect([0, 0, *self.camera_size])
        self.sprites = [sprite for row in sprites for sprite in row if sprite is not None]
        self.target = main_player

        self.set_camera_start_position()

    def set_camera_start_position(self):
        self.update(False)
        self.start_zone = self.camera_rect.copy()

        print(self.start_zone)

    def update(self, need_to_update_objects_position=True):
        x_shift = y_shift = 0

        rect = self.target.rect
        if rect.x + rect.width > self.camera_rect.width * self.edge_percent + self.camera_rect.x:
            x_shift = (rect.x + rect.width) - (self.camera_rect.width * self.edge_percent +
                                               self.camera_rect.x)
        elif rect.x < self.camera_rect.width * (1 - self.edge_percent) + self.camera_rect.x:
            x_shift = rect.x - (self.camera_rect.width * (1 - self.edge_percent) +
                                self.camera_rect.x)

        if rect.y + rect.height > self.camera_rect.height * self.edge_percent + self.camera_rect.y:
            y_shift = (rect.y + rect.height) - (self.camera_rect.height * self.edge_percent +
                                                self.camera_rect.y)
        elif rect.y < self.camera_rect.height * (1 - self.edge_percent) + self.camera_rect.y:
            y_shift = rect.y - (self.camera_rect.height * (1 - self.edge_percent) +
                                self.camera_rect.y)

        self.camera_rect = pygame.Rect([self.camera_rect.x + x_shift, self.camera_rect.y + y_shift,
                                        *self.camera_size])
        self.check_map_end()
        if need_to_update_objects_position:
            x_shift = self.start_zone.x - self.camera_rect.x
            y_shift = self.start_zone.y - self.camera_rect.y
            self.update_objects_dislocation(x_shift, y_shift)
        print(self.target.rect, end='\n\n')

    def check_map_end(self):
        if self.camera_rect.x < 0:
            self.camera_rect = self.camera_rect.move(-self.camera_rect.x, 0)
        elif self.camera_rect.x + self.camera_rect.width > MAP_WIDTH:
            self.camera_rect = self.camera_rect.move(MAP_WIDTH - (self.camera_rect.x +
                                                                  self.camera_rect.width), 0)

        if self.camera_rect.y < 0:
            self.camera_rect = self.camera_rect.move(0, -self.camera_rect.y)
        elif self.camera_rect.y + self.camera_rect.height > MAP_HEIGHT:
            self.camera_rect = self.camera_rect.move(0, MAP_HEIGHT - (self.camera_rect.y +
                                                                      self.camera_rect.height))

    def update_objects_dislocation(self, x_shift, y_shift):
        print(x_shift, y_shift, self.target.rect)
        for sprite in self.sprites:
            sprite.update_position(x_shift, y_shift)


if __name__ == '__main__':
    fps = 60  # количество кадров в секунду
    clock = pygame.time.Clock()
    running = True

    """ Сделать главное меню с переходом на 1 уровень """

    game = True
    pause = False
    event = None

    game_map = Map()
    game_map.load(LEVELS[0])

    anim = Animation(LEVEL_NAME)

    # camera = Camera(game_map.player, game_map.map)

    while running:  # главный игровой цикл
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pause = not pause
                if event.key == pygame.K_r:
                    game_map = Map()
                    game_map.load(LEVELS[0])

                    anim = Animation(LEVEL_NAME)
                    game = True

            # обработка остальных событий
            # ...

        # формирование кадра
        if game and not pause:
            # camera.update()
            game_map.update()
            all_sprites.update(event)
        # ...

        draw()

        # изменение игрового мира
        if game and not pause:
            """ Сделать окно проигрыша (с рестартом) """
            game = game_map.check_lose()
        if game and not pause:
            """ Сделать окно победы и переход на новый уровень """
            game = not game_map.check_win()
            """ Сделать финальное окно """
        # ...

        pygame.display.flip()  # смена кадра

        # временная задержка
        clock.tick(fps)
