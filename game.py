from constants import *
from sprite_groups import *
from victory_wnd import show_victory_screen
from collections import deque

import pygame
import random as rd

pygame.init()  # Инициализация движка pygame

SIZE = WIDTH, HEIGHT = (800, 600)
screen = pygame.display.set_mode(SIZE)

LEVEL_NAME = ""
LIVES = 5
COIN_AMOUNT = 0
COIN_LEFT = 0

lvl_index = 0
start_time = 0
game_map = None
is_win = None


def print_warning(*args):
    for text in args:
        print("\033[33m{}\033[0m".format(str(text)), end=' ')
    print()


def print_error(*args):
    for text in args:
        print("\033[31m{}\033[0m".format(str(text)), end=' ')
    print()


def set_size(x, y):
    global SIZE, WIDTH, HEIGHT, screen
    SIZE = WIDTH, HEIGHT = (x * TILE_SIZE, y * TILE_SIZE)
    screen = pygame.display.set_mode(SIZE)


def load_level(lvl_name):
    global COIN_LEFT, COIN_AMOUNT, LEVEL_NAME

    with open(f"{DATA_DIR}/levels/{lvl_name}.txt") as lvl_file:
        LEVEL_NAME = lvl_file.readline().strip()
        COIN_LEFT = int(lvl_file.readline().strip())
        COIN_AMOUNT = 0
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
                enemy = Enemy(j, i)
                opponents.append(enemy)
                lvl_map[i].append(enemy)
                continue
            else:
                raise Exception(f"Incorrect data in level file: pos({i},{j}) elem - {elem}")
            lvl_map[i].append(map_object)

    set_size(len(lvl_map[0]), len(lvl_map))
    for enemy in opponents:
        enemy.set_map(lvl_map)

    return hero, opponents, lvl_map


class MapObject(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups, size=(TILE_SIZE, TILE_SIZE)):
        super().__init__(*groups, all_sprites)
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
        super().__init__(x, y, *groups, map_objects)
        self.image.fill(orange)


class Ladder(MapObject):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, map_objects)
        self.image.fill(yellow)


class Bridge(MapObject):
    height = 10

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, map_objects, size=(TILE_SIZE, Bridge.height))
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
        if have_collision(self, map_objects):
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

        self.update_map_coord(self.x, self.y)


class Enemy(ManagedGameObject):
    def __init__(self, x, y, *groups):
        super().__init__(x, y, enemies, *groups)
        self.image.fill(red)
        self.path = []
        self.__map = []

        self.speed_h = 3
        self.speed_v = 3

    def set_map(self, lvl):
        self.__map = lvl

    def get_all_enemies_pos(self):
        assert isinstance(game_map, Map)
        self.enemies_pos = [(en.map_x, en.map_y) for en in game_map.enemies]

    def get_player_pos(self):
        assert isinstance(game_map, Map)
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
        if isinstance(self.__map[y + dy][x + dx], Wall):
            return False
        if dy == -1 and not isinstance(self.__map[y][x], Ladder):
            return False
        if (dx != 0 and not isinstance(self.__map[y + 1][x], (Wall, Ladder))
                and not isinstance(self.__map[y][x], Bridge)):
            return False
        return True

    def find_path(self, start: (list, tuple), target: (list, tuple)) -> bool:
        if start == target:
            return True

        inf = float('inf')
        w, h = len(self.__map[0]), len(self.__map)
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
        try:
            if distances[y][x] == inf:
                print_warning(f'Warning caused in find_path method. Program cant find'
                              f'path from enemy({self.map_x},{self.map_y}) to player({x}, {y})')
                return False
        except IndexError:
            print_error(f'Error caused in find_path method. Wrong index: target({x}, {y}),' +
                        f'map({len(self.__map[0])},{len(self.__map)})')
            return False

        self.path.clear()
        while prev[y][x] is not None:
            self.path.append((x, y))
            x, y = prev[y][x]

        return True


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
        global is_win
        if pygame.sprite.spritecollideany(self.player, enemies) is None:
            return False
        is_win = False
        return True

    @staticmethod
    def check_win() -> bool:
        global is_win
        if COIN_LEFT == 0:
            is_win = True
            return True
        return False

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


class Animation(pygame.sprite.Sprite):
    def __init__(self, level_name: str, *groups):
        super().__init__(*groups, all_sprites, animations)

        font = pygame.font.Font(None, 108)
        text = font.render(level_name, True, white)

        self.image = pygame.Surface(text.get_size())
        self.image.blit(text, (0, 0))
        self.image = self.image.convert()
        self.image.set_colorkey(black)
        self.image.set_alpha(1)

        self.increase = True

        self.rect = self.image.get_rect().move(WIDTH // 2 - text.get_width() // 2,
                                               HEIGHT // 2 - text.get_height() // 2)

    def __bool__(self):
        return self.image.get_alpha() != 0

    def update(self, *args, **kwargs) -> None:
        if kwargs.get('is_pause', None) is True:
            self.increase = False
            self.image.set_alpha(0)

        if self.increase:
            self.image.set_alpha(min(255, self.image.get_alpha() + 2))
            self.increase = self.image.get_alpha() < 255
        elif self.image.get_alpha() != 0:
            self.image.set_alpha(max(0, self.image.get_alpha() - 4))
        else:
            self.kill()


def draw(is_pause):  # Функция отрисовки кадров
    screen.fill(gray)

    all_sprites.draw(screen)
    coins.draw(screen)
    player.draw(screen)
    enemies.draw(screen)
    animations.draw(screen)

    show_text(screen, f'Жизней:', (0, 0))
    show_text(screen, heart_char * LIVES, (75, -8), 26, "segoeuisymbol", red)
    show_text(screen, f'Собрано монет: {COIN_AMOUNT}', (0, 24))
    show_text(screen, f'Осталось монет: {COIN_LEFT}', (0, 48))
    if is_pause:
        show_text(screen, 'Пауза', (WIDTH // 2 - 100, HEIGHT // 2 - 50), size=108, color=black)

    assert isinstance(game_map, Map)
    for enemy in game_map.enemies:
        for x, y in enemy.path:
            pygame.draw.circle(screen, green, ((x + 0.5) * TILE_SIZE, (y + 0.5) * TILE_SIZE), 10)


def play_game(lvl_name, is_new_game=False):
    global LIVES, game_map, lvl_index, start_time

    fps = 60  # количество кадров в секунду
    clock = pygame.time.Clock()
    running = True

    game = True
    pause = False
    event = None

    if is_new_game:
        start_time = timer()
        LIVES = 5
        lvl_index = 0

    game_map = Map()
    game_map.load(lvl_name)

    anim = Animation(LEVEL_NAME)

    while running:  # главный игровой цикл
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game:
                    pause = not pause

            # обработка остальных событий
            # ...

        # формирование кадра
        if game and not pause:
            game_map.update()
            all_sprites.update(event)
        else:
            animations.update(event, is_pause=pause)
        # ...

        draw(pause)

        # изменение игрового мира
        if game and not pause:
            game = not game_map.check_lose()
            if not game:
                LIVES -= 1
                anim = Animation('Вы проиграли' if LIVES != 0 else 'Вас убили!')
        if game and not pause:
            game = not game_map.check_win()
            if not game:
                anim = Animation('Вы победили')

        if not (game or anim):
            for sprite in all_sprites:
                sprite.kill()

            if LIVES != 0:
                lvl_index += is_win
                if lvl_index >= len(LEVELS):
                    show_victory_screen(LIVES, int(timer() - start_time))
                    return False
                running = play_game(LEVELS[lvl_index])
            else:
                return False
        # ...

        pygame.display.flip()  # смена кадра

        # временная задержка
        clock.tick(fps)

    return False


if __name__ == '__main__':
    play_game('level2')
