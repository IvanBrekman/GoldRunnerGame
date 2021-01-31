import os
import sys

import pygame

import random as rd
from collections import deque

pygame.init()  # Инициализация движка pygame

SIZE = WIDTH, HEIGHT = 1200, 600  # Размеры окна
MAP_WIDTH = MAP_HEIGHT = 0

screen = pygame.display.set_mode(SIZE)  # Создание холста
pygame.display.set_caption('Золотоискатель')  # Изменение заголовка

# Цвета
black = pygame.Color('black')
white = pygame.Color('white')
red = pygame.Color('red')
green = pygame.Color('green')
blue = pygame.Color('blue')
orange = pygame.Color('orange')
yellow = pygame.Color('yellow')
gray = pygame.Color('gray')

DATA_DIR = "F:/3_Programming/Python/Yandex/2_Second_Year/24. Защита проекта PyGame/resources"
LEVEL_NAME = ""
TILE_SIZE = 40
MAX_COINS = 5
COINS_PROBABILITY = 0.005
LIVES = 5
COIN_AMOUNT = 0
COIN_LEFT = 0

heart_char = chr(10_084)
have_collision = pygame.sprite.spritecollideany


def print_warning(text):
    print("\033[33m{}\033[0m".format(text))


def set_size(x, y):
    global MAP_WIDTH, MAP_HEIGHT

    MAP_WIDTH = x * TILE_SIZE
    MAP_HEIGHT = y * TILE_SIZE


def load_image(image_path, color_key=None):
    """
    Функция загружает изображение и возвращает объект типа pygame.image
    Если программа не может найти/открыть файл программа завершит свою работу
    :param image_path: Путь к картинке
    :param color_key: Цвет прозрачного фона (None (по умолчанию) если изобрадение уже прозрачно).
                      укажите -1, чтобы сделать прозрачнфм цветот левый верхний пиксель картинки
    """
    full_name = os.path.join(image_path)

    if not os.path.isfile(full_name):
        print(f"Файл с изображением '{full_name}' не найден")
        sys.exit()
    image = pygame.image.load(full_name)

    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()

    return image


def load_level(lvl_name):
    global COIN_LEFT, LEVEL_NAME
    with open(f"{DATA_DIR}/levels/{lvl_name}.txt") as lvl_file:
        LEVEL_NAME = lvl_file.readline()
        COIN_LEFT = int(lvl_file.readline().strip())
        lvl = lvl_file.readlines()

    lvl_map = []
    opponents = []
    hero = None

    for i, row in enumerate(lvl):
        lvl_map.append([])
        for j, elem in enumerate(row.strip()):
            if elem == '0':
                map_object = None
            elif elem == '1':
                map_object = Wall(j, i, walls)
            elif elem == '2':
                map_object = Ladder(j, i, ladders)
            elif elem == '3':
                map_object = Bridge(j, i, bridges)
            elif elem == '4':
                hero = Player(j, i)
                lvl_map[i].append(hero)
                continue
            elif elem == '5':
                enemy = Enemy(j + 1, i)
                opponents.append(enemy)
                lvl_map[i].append(enemy)
                continue
            else:
                raise Exception(f"Incorrect data in level file: pos({i},{j}) elem - {elem}")
            lvl_map[i].append(map_object)

    set_size(len(lvl[0]), len(lvl))
    for enemy in opponents:
        enemy.set_map(lvl_map)

    return hero, opponents, lvl_map


class MapObject(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups, size=(TILE_SIZE, TILE_SIZE)):
        super().__init__(*groups, all_sprites, map_objects)
        self.image = pygame.Surface(size)

        self.x_shift = 0
        self.y_shift = 0

        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE

        self.rect = self.image.get_rect()
        self.rect.x = self.x + self.x_shift
        self.rect.y = self.y + self.y_shift

    def update_position(self, x, y):
        self.x_shift = x
        self.y_shift = y

        self.rect.x = self.x + self.x_shift
        self.rect.y = self.y + self.y_shift


class Wall(MapObject):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.image.fill(orange)


class Ladder(MapObject):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups)
        self.image.fill(yellow)


class Bridge(MapObject):
    height = 10

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, size=(TILE_SIZE, Bridge.height))
        self.image.fill(white)


class Coin(MapObject):
    def __init__(self, lvl_map, *groups):
        x = y = 0
        false_enemy = Enemy(1, 1)
        false_enemy.set_map(lvl_map)
        while not (lvl_map[y][x] is None and isinstance(lvl_map[y + 1][x], Wall)):
            x, y = rd.randint(0, WIDTH // TILE_SIZE - 1), rd.randint(0, HEIGHT // TILE_SIZE - 1)
        false_enemy.kill()
        lvl_map[y][x] = self
        
        super().__init__(x, y, *groups, coins)
        self.image.fill(green)


class ManagedGameObject(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups, all_sprites)
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])

        self.x_shift = 0
        self.y_shift = 0

        self.map_x = x
        self.map_y = y
        self.map = []
        self.buffer = None

        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE

        self.rect = self.image.get_rect()
        self.rect.x = self.x + self.x_shift
        self.rect.y = self.y + self.y_shift

    def get_multiplayer(self):
        self.rect.y += 1
        if have_collision(self, map_objects):
            self.rect.y -= 1
            return 1

        self.rect.y -= 1
        return 0.7

    @staticmethod
    def correcting_position(obj_coord, col_coord, step):
        if obj_coord - col_coord <= -step:
            return step
        if obj_coord - col_coord >= step:
            return -step
        return -(obj_coord - col_coord)

    def correcting_collision(self, wall: pygame.Rect, x_shift, y_shift):
        if x_shift != 0:
            self.rect.x = wall.x + TILE_SIZE * (2 * (x_shift < 0) - 1)
        if y_shift != 0:
            self.rect.y = wall.y + TILE_SIZE * (2 * (y_shift < 0) - 1)

    def update_position(self, x, y):
        self.x_shift = x
        self.y_shift = y

        self.rect.x = self.x + self.x_shift
        self.rect.y = self.y + self.y_shift

    def update_map_coord(self, x, y):
        self.map_x = (x + TILE_SIZE // 2) // TILE_SIZE
        self.map_y = (y + TILE_SIZE // 2) // TILE_SIZE


class Player(ManagedGameObject):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, player)
        self.image.fill(blue)

        self.speed_h = 5
        self.speed_v = 3

    def update(self, *args, **kwargs) -> None:
        self.rect.y += self.speed_v
        if have_collision(self, map_objects) and not have_collision(self, coins):
            self.rect.y -= self.speed_v
        self.rect.y += 1
        if have_collision(self, map_objects):
            if have_collision(self, bridges):
                y = have_collision(self, bridges).rect.y
                self.rect.y -= 1 if self.rect.y - y == 1 else 2 if self.rect.y - y > 1 else 0
            else:
                self.rect.y -= 1

        x_shift = y_shift = 0
        if args and args[0].type == pygame.KEYDOWN:
            multiplayer = self.get_multiplayer()
            if args[0].key == pygame.K_LEFT:
                self.rect.x -= (self.speed_h * multiplayer)
                x_shift -= (self.speed_h * multiplayer)
            if args[0].key == pygame.K_RIGHT:
                self.rect.x += (self.speed_h * multiplayer)
                x_shift += (self.speed_h * multiplayer)

            if args[0].key == pygame.K_DOWN:
                self.rect.y += 1
                if not (have_collision(self, ladders) or have_collision(self, bridges)):
                    self.rect.y -= 1

            if have_collision(self, ladders):
                ladder = have_collision(self, ladders)
                if args[0].key == pygame.K_UP:
                    self.rect.x += self.correcting_position(self.rect.x, ladder.rect.x, 6)
                    self.rect.y -= self.speed_h

                    x_shift = 0
                    y_shift -= self.speed_h
                if args[0].key == pygame.K_DOWN:
                    self.rect.x += self.correcting_position(self.rect.x, ladder.rect.x, 6)
                    self.rect.y += self.speed_h

                    x_shift = 0
                    y_shift += self.speed_h

            if have_collision(self, bridges):
                if args[0].key == pygame.K_DOWN:
                    self.rect.y += Bridge.height
                    y_shift += Bridge.height

        if have_collision(self, walls) and x_shift + y_shift != 0:
            self.correcting_collision(have_collision(self, walls).rect, x_shift, y_shift)
            if have_collision(self, ladders) and x_shift != 0:
                self.rect.y -= 1
            while have_collision(self, walls):
                self.rect.y += 1

        self.x = self.rect.x
        self.y = self.rect.y

        if x_shift + y_shift != 0:
            self.update_map_coord(self.x, self.y)


class Enemy(ManagedGameObject):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, enemies, *groups)
        self.image.fill(red)
        self.path = []

        self.speed_h = 3
        self.speed_v = 3

    def set_map(self, lvl):
        self.map = lvl

    def get_all_enemies_pos(self):
        self.enemies_pos = [(en.map_x, en.map_y) for en in game_map.enemies]

    def get_player_pos(self):
        self.px, self.py = game_map.player.map_x, game_map.player.map_y

    def update(self, *args, **kwargs) -> None:
        self.get_player_pos()
        self.get_all_enemies_pos()
        self.find_path((self.map_x, self.map_y), (self.px, self.py))

        if self.path:
            x, y = self.path[-1]
            xc, yc = x * TILE_SIZE, y * TILE_SIZE
            rect = self.rect

            if any(pos == (x, y) for pos in self.enemies_pos):
                return

            if rect.x != xc or rect.y != yc:
                rect.x += self.correcting_position(rect.x, xc, self.speed_h)
                rect.y += self.correcting_position(rect.y, yc, self.speed_h)
            else:
                self.update_map_coord(self.rect.x, self.rect.y)
                self.path.pop()

    def is_free(self, x, y, dx, dy) -> bool:
        if isinstance(self.map[y + dy][x + dx], Wall):
            return False
        if dy == -1 and not isinstance(self.map[y][x], Ladder):
            return False
        if (dx != 0 and not isinstance(self.map[y + 1][x], (Wall, Ladder))
                and not isinstance(self.map[y][x], Bridge)):
            return False
        return True

    def find_path(self, start: (list, tuple), target: (list, tuple)) -> bool:
        if start == target:
            return True

        inf = float('inf')
        w, h = len(self.map[0]), len(self.map)
        x, y = start
        distances = [[inf] * w for _ in range(h)]
        distances[y][x] = 0
        prev = [[None] * w for _ in range(h)]
        queue = deque([(x, y)])

        while queue:
            x, y = queue.popleft()
            for dx, dy in (-1, 0), (0, -1), (1, 0), (0, 1):
                next_x, next_y = x + dx, y + dy
                if (0 <= next_x < w and 0 <= next_y < h and
                        self.is_free(x, y, dx, dy) and distances[next_y][next_x] == inf):
                    distances[next_y][next_x] = distances[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))

        x, y = target
        if distances[y][x] == inf:
            print_warning(f'Warning caused in find_path method. Program cant find path from enemy(' +
                          f'{self.map_x},{self.map_y}) to player({x}, {y})')
            return False

        self.path.clear()
        while prev[y][x] is not None:
            self.path.append((x, y))
            x, y = prev[y][x]

        return True


class Camera:
    def __init__(self, main_player: pygame.sprite.Sprite, sprites: (list, tuple)):
        assert isinstance(main_player, Player),\
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


class Map:
    def __init__(self):
        self.player = None
        self.enemies = []
        self.map = []
        self.coins_on_map = 0

    def __str__(self):
        return '\n'.join(str(row) for row in self.map)

    def load(self, lvl):
        self.player, self.enemies, self.map = load_level(lvl)

    def check_lose(self) -> bool:
        return pygame.sprite.spritecollideany(self.player, enemies) is None

    @staticmethod
    def check_win() -> bool:
        return COIN_LEFT == 0

    def check_player_takes_coin(self):
        global COIN_AMOUNT, COIN_LEFT
        if pygame.sprite.spritecollide(self.player, coins, True):
            COIN_AMOUNT += 1
            COIN_LEFT -= 1
            self.coins_on_map -= 1
    
    def update_coins(self):
        if (self.coins_on_map < min(MAX_COINS, COIN_LEFT) and rd.random() < COINS_PROBABILITY or
                self.coins_on_map == 0 and COIN_LEFT > 0):
            Coin(self.map)
            self.coins_on_map += 1

    def update(self):
        self.check_player_takes_coin()
        self.update_coins()


class NewLevelAnimation(pygame.sprite.Sprite):
    def __init__(self, level_name: str, *groups):
        super().__init__(*groups, all_sprites, animations)

        font = pygame.font.Font(None, 108)
        text = font.render(level_name, True, white)

        self.image = pygame.Surface(text.get_size())
        self.image.blit(text, (0, 0))
        self.image = self.image.convert()
        self.image.set_colorkey(black)
        self.image.set_alpha(0)

        self.increase = True

        self.rect = self.image.get_rect().move(WIDTH // 2 - text.get_width() // 2,
                                               HEIGHT // 2 - text.get_height() // 2)

    def update(self, *args, **kwargs) -> None:
        if self.increase:
            self.image.set_alpha(min(255, self.image.get_alpha() + 2))
            self.increase = self.image.get_alpha() < 255
        elif self.image.get_alpha() != 0:
            self.image.set_alpha(max(0, self.image.get_alpha() - 4))


def show_message(surface, text, position: (list, tuple), font=None, color=black):
    font = pygame.font.SysFont(font, 26)
    text = font.render(text, True, color)
    text_x, text_y = position

    surface.blit(text, (text_x, text_y))


def draw():  # Функция отрисовки кадров
    screen.fill(gray)

    all_sprites.draw(screen)
    coins.draw(screen)
    player.draw(screen)
    enemies.draw(screen)

    show_message(screen, f'Жизней:', (0, 0))
    show_message(screen, str(heart_char * LIVES), (75, -8), "segoeuisymbol", red)
    show_message(screen, f'Собрано монет: {COIN_AMOUNT}', (0, 24))
    show_message(screen, f'Осталось монет: {COIN_LEFT}', (0, 48))

    # pygame.draw.rect(screen, blue, camera.camera_rect, 1)
    for enemy in game_map.enemies:
        for x, y in enemy.path:
            pygame.draw.circle(screen, green, ((x + 0.5) * TILE_SIZE, (y + 0.5) * TILE_SIZE), 10)


if __name__ == '__main__':
    fps = 60  # количество кадров в секунду
    clock = pygame.time.Clock()
    running = True

    """ Сделать главное меню с переходом на 1 уровень """

    all_sprites = pygame.sprite.Group()
    map_objects = pygame.sprite.Group()
    animations = pygame.sprite.Group()

    walls = pygame.sprite.Group()
    ladders = pygame.sprite.Group()
    bridges = pygame.sprite.Group()
    coins = pygame.sprite.Group()

    player = pygame.sprite.Group()
    enemies = pygame.sprite.Group()

    game = True
    pause = False
    event = None

    game_map = Map()
    game_map.load('level1')

    anim = NewLevelAnimation('Stage 1')

    # camera = Camera(game_map.player, game_map.map)

    while running:  # главный игровой цикл
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    pause = not pause

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
