from constants import *
from sprite_groups import *
from victory_wnd import show_victory_screen
from collections import deque

import pygame
import time
import random as rd

SIZE = WIDTH, HEIGHT = (800, 600)
screen = pygame.display.set_mode(SIZE)
pygame.init()  # Инициализация движка pygame

LEVEL_NAME = ""
LEVEL_FON = ""
CAN_DIG = False
LIVES = 5
COIN_AMOUNT = 0
COIN_LEFT = 0

destroyed_walls = {}
lvl_index = 0
tick_time = 0
game_map = None
is_win = None


def set_size(x, y):
    global SIZE, WIDTH, HEIGHT, screen

    SIZE = WIDTH, HEIGHT = (x * TILE_SIZE, y * TILE_SIZE)
    screen = pygame.display.set_mode(SIZE)


def load_level(lvl_name):
    global COIN_LEFT, COIN_AMOUNT, LEVEL_NAME, LEVEL_FON

    with open(f"{DATA_DIR}/levels/{lvl_name}.txt") as lvl_file:
        LEVEL_NAME = lvl_file.readline().strip()
        COIN_LEFT = int(lvl_file.readline().strip())
        LEVEL_FON = lvl_file.readline().strip()
        COIN_AMOUNT = 0
        lvl = lvl_file.readlines()

    lvl_map = []
    opponents = []
    coins_place = []
    hero = None

    for i, row in enumerate(lvl):
        lvl_map.append([])
        for j, elem in enumerate(row.strip()):
            if elem == '0':
                map_object = None
            elif elem == '1':
                map_object = Wall(j, i, False, walls)
            elif elem == '2':
                map_object = Wall(j, i, True, walls)
            elif elem == '3':
                map_object = Ladder(j, i, ladders)
            elif elem == '4':
                map_object = Bridge(j, i, bridges)
            elif elem == '5':
                hero = Player(j, i)
                lvl_map[i].append(hero)
                continue
            elif elem in ('6', '8'):
                enemy = Enemy(j, i, elem == '6')
                opponents.append(enemy)
                lvl_map[i].append(enemy)
                continue
            elif elem == '7':
                map_object = None
                coins_place.append((i, j))
            else:
                raise Exception(f"Incorrect data in level file: pos({i},{j}) elem - {elem}")
            lvl_map[i].append(map_object)

    set_size(len(lvl_map[0]), len(lvl_map))
    hero.set_map(lvl_map)
    for enemy in opponents:
        enemy.set_map(lvl_map)

    return hero, opponents, lvl_map, coins_place


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
    wall_image = f"{DATA_DIR}/images/mapObjects/wall.png"
    wall_destroyed_image = f"{DATA_DIR}/images/mapObjects/wall2.png"

    def __init__(self, x, y, is_destroyed, *groups):
        super().__init__(x, y, *groups, map_objects)
        self.image = load_image(Wall.wall_destroyed_image if is_destroyed else Wall.wall_image)
        self.is_destroyed = is_destroyed


class Ladder(MapObject):
    ladder_image = f"{DATA_DIR}/images/mapObjects/ladder.png"

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, map_objects)
        self.image = load_image(Ladder.ladder_image)


class Bridge(MapObject):
    height = 10
    bridge_image = f"{DATA_DIR}/images/mapObjects/bridge.png"

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, map_objects, size=(TILE_SIZE, Bridge.height))
        self.image.fill(white)


class Coin(MapObject):
    sound = init_sound("coin_up.mp3", 1)

    def __init__(self, lvl_map, *groups, x=None, y=None):
        if x is None or y is None:
            x = y = script = 0
            while not (lvl_map[y][x] is None and isinstance(lvl_map[y + 1][x], Wall) and script):
                x, y = rd.randint(0, len(lvl_map[0]) - 2), rd.randint(0, len(lvl_map) - 2)
                script = lvl_index != 2 or (x not in (1, 2) and y != 2)
        lvl_map[y][x] = self

        super().__init__(x, y, *groups, coins)
        self.frames = [load_image(f"{DATA_DIR}/images/coins/coin{i + 1}.png") for i in range(7)]
        self.cur_frame = 0
        self.image = load_image(f"{DATA_DIR}/images/shovel.png")
        self.image = self.frames[self.cur_frame]

    def update(self, *args, **kwargs) -> None:
        self.cur_frame = (self.cur_frame + 1) % (len(self.frames) * 10)
        self.image = self.frames[self.cur_frame // 10]


class Shovel(MapObject):
    sound = init_sound("shovel_up.mp3", 1)

    def __init__(self, lvl_map, *groups):
        x = y = 0
        while not (lvl_map[y][x] is None and isinstance(lvl_map[y + 1][x], Wall)):
            x, y = rd.randint(0, len(lvl_map[0]) - 2), rd.randint(0, len(lvl_map) - 2)

        super().__init__(x, y, *groups, shovels)
        self.image = load_image(f"{DATA_DIR}/images/shovel.png")


class ManagedGameObject(pygame.sprite.Sprite):
    def __init__(self, x, y, *groups):
        super().__init__(*groups, all_sprites)
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
        self.walk_index = 0
        self.climb_index = 0
        self.direction = 0
        self.is_bot = None
        
        self.speed_h = 0
        self.speed_v = 0

        self.map_x = x
        self.map_y = y
        self.map = []
        
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

    def get_multiplayer(self) -> float:
        self.rect.y += 1
        if have_collision(self, map_objects):
            self.rect.y -= 1
            return 1

        self.rect.y -= 1
        return 0.7

    def set_map(self, lvl):
        self.map = lvl

    def set_image(self, left: bool, right: bool, up: bool, down: bool) -> None:
        player_class = Player if isinstance(self, Player) else Enemy
        if left or right:
            self.direction = right - 1
            self.walk_index = (self.walk_index + 1) % (len(player_class.walk) * 10)
            self.climb_index = 0

            self.image = player_class.walk[self.walk_index // 10]
        elif up or down:
            self.walk_index = 0
            self.climb_index = (self.climb_index + 1) % (len(player_class.climb) * 10)

            self.image = player_class.climb[self.climb_index // 10]
        else:
            self.image = player_class.stand

        if self.direction == -1:
            self.image = pygame.transform.flip(self.image, True, False)

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
    
    def move(self, k_pressed, key_left_pressed, key_right_pressed, key_up_pressed, key_down_pressed):
        self.set_image(key_left_pressed, key_right_pressed, key_up_pressed, key_down_pressed)

        if (self.map_x, self.map_y + 1) in destroyed_walls:
            self.rect.x = self.map_x * TILE_SIZE

        self.rect.y += self.speed_v
        if have_collision(self, map_objects):
            self.rect.y -= self.speed_v
        self.rect.y += 1
        if have_collision(self, map_objects):
            if have_collision(self, bridges) and (isinstance(self, Player) or not self.is_bot):
                y = have_collision(self, bridges).rect.y
                self.rect.y -= 1 if self.rect.y - y == 1 else 2 if self.rect.y - y > 1 else 0
            else:
                self.rect.y -= 1

        x_shift = y_shift = 0
        if k_pressed:
            multiplayer = self.get_multiplayer()
            if key_left_pressed:
                self.rect.x -= (self.speed_h * multiplayer)
                x_shift -= (self.speed_h * multiplayer)
            if key_right_pressed:
                self.rect.x += (self.speed_h * multiplayer)
                x_shift += (self.speed_h * multiplayer)

            if key_down_pressed:
                self.rect.y += 1
                if not (have_collision(self, ladders) or have_collision(self, bridges)):
                    self.rect.y -= 1

            if have_collision(self, ladders):
                ladder = have_collision(self, ladders)
                if key_up_pressed:
                    self.rect.x += self.correcting_position(self.rect.x, ladder.rect.x, 6)
                    self.rect.y -= self.speed_h

                    x_shift = 0
                    y_shift -= self.speed_h
                if key_down_pressed:
                    self.rect.x += self.correcting_position(self.rect.x, ladder.rect.x, 6)
                    self.rect.y += self.speed_h

                    x_shift = 0
                    y_shift += self.speed_h

            if have_collision(self, bridges) and key_down_pressed:
                if self.rect.y >= have_collision(self, bridges).rect.y:
                    self.rect.y += Bridge.height
                    y_shift += Bridge.height
                else:
                    self.rect.y += self.speed_h
                    y_shift += self.speed_h

        if have_collision(self, walls) and x_shift + y_shift != 0:
            self.correcting_collision(have_collision(self, walls).rect, x_shift, y_shift)
            if have_collision(self, ladders) and x_shift != 0:
                self.rect.y -= 1
            while have_collision(self, walls):
                self.rect.y += 1


class Player(ManagedGameObject):
    dir = f"{DATA_DIR}/images/player/"
    walk = [load_image(f"{dir}player_walk1.png"), load_image(f"{dir}player_walk2.png")]
    climb = [load_image(f"{dir}player_climb1.png"), load_image(f"{dir}player_climb2.png")]
    stand = load_image(f"{dir}player_stand.png")

    died_sound = init_sound('death5.mp3')

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, player)
        self.image = load_image(f"{DATA_DIR}/images/player/player_stand.png")
        self.mask = pygame.mask.from_surface(self.image)
        self.can_dig = CAN_DIG

        self.speed_h = 5
        self.speed_v = 4

    def update(self, *args, **kwargs) -> None:
        keys = pygame.key.get_pressed()

        k_pressed = sum(keys) != 0
        key_left_pressed = keys[pygame.K_LEFT]
        key_right_pressed = keys[pygame.K_RIGHT]
        key_up_pressed = keys[pygame.K_UP]
        key_down_pressed = keys[pygame.K_DOWN]

        if keys[pygame.K_f] and self.can_dig:
            x, y = self.map_x, self.map_y
            d = self.direction * 2 + 1
            if isinstance(self.map[y + 1][x], MapObject) and \
                    isinstance(self.map[y + 1][x + d], Wall) and self.map[y + 1][x + d].is_destroyed:
                destroyed_walls[(x + d, y + 1)] = time.time()
                self.map[y + 1][x + d].kill()
                self.map[y + 1][x + d] = None
        
        self.move(k_pressed, key_left_pressed, key_right_pressed, key_up_pressed, key_down_pressed)
        self.update_map_coord(self.rect.x, self.rect.y)

    def draw_label(self):
        font = pygame.font.Font(None, 18)
        text = font.render("Player 1", True, yellow)

        tw, th = text.get_size()
        x, y = self.rect.x + TILE_SIZE // 2 - tw // 2, self.rect.y - th

        pygame.draw.rect(screen, blue, (x - 2, y - 2, tw + 4, th + 4), 2)
        screen.blit(text, (x, y))


class Enemy(ManagedGameObject):
    dir = f"{DATA_DIR}/images/enemy/"
    walk = [load_image(f"{dir}zombie_walk1.png"), load_image(f"{dir}zombie_walk2.png")]
    climb = [load_image(f"{dir}zombie_climb1.png"), load_image(f"{dir}zombie_climb2.png")]
    stand = load_image(f"{dir}/zombie_stand.png")

    died_sound = init_sound("zombie_died_sound.mp3")

    def __init__(self, x, y, can_set_control_to_player, *groups, is_bot=True):
        super().__init__(x, y, enemies, *groups)

        self.image = load_image(f"{DATA_DIR}/images/enemy/zombie_stand.png")
        self.mask = pygame.mask.from_surface(self.image)
        self.update = self.update_as_bot if is_bot else self.update_as_player
        self.can_set_control_to_player = can_set_control_to_player
        self.is_bot = is_bot

        self.x = x
        self.y = y

        self.path = []

        self.speed_h = 3
        self.speed_v = 3

    def set_control_to_player(self):
        self.update = self.update_as_player
        self.is_bot = False

    def get_all_enemies_pos(self):
        assert isinstance(game_map, Map)
        self.enemies_pos = [(en.map_x, en.map_y) for en in game_map.enemies]

    def get_player_pos(self):
        assert isinstance(game_map, Map)
        self.px, self.py = game_map.player.map_x, game_map.player.map_y

    def draw_label(self):
        if self.is_bot:
            return

        font = pygame.font.Font(None, 18)
        text = font.render("Player 2", True, yellow)

        tw, th = text.get_size()
        x, y = self.rect.x + TILE_SIZE // 2 - tw // 2, self.rect.y - th

        pygame.draw.rect(screen, red, (x - 2, y - 2, tw + 4, th + 4), 2)
        screen.blit(text, (x, y))

    def update_map_coord(self, p_rect, t_rect):
        collision = p_rect.clip(t_rect)
        if (collision.w * collision.h) / (TILE_SIZE ** 2) >= 0.9:
            self.map_x = t_rect.x // TILE_SIZE
            self.map_y = t_rect.y // TILE_SIZE

    def update_as_bot(self, *args, **kwargs) -> None:
        self.get_player_pos()
        self.get_all_enemies_pos()
        path = self.find_path((self.map_x, self.map_y), (self.px, self.py))

        if path or len(self.path) > 2:
            x, y = self.path[-1]
            xc, yc = x * TILE_SIZE, y * TILE_SIZE
            px, py = self.rect.x, self.rect.y

            if any(pos == (x, y) for pos in self.enemies_pos):
                return

            k_pressed = px != xc or py != yc
            k_left_pressed = k_right_pressed = k_up_pressed = k_down_pressed = False
            if abs(px - xc) > abs(py - yc):
                self.rect.y = yc
                if px > xc:
                    k_left_pressed = px > xc
                elif px < xc:
                    k_right_pressed = px < xc
            else:
                self.rect.x = xc
                if py > yc:
                    k_up_pressed = py > yc
                elif py < yc:
                    k_down_pressed = py < yc

            self.move(k_pressed, k_left_pressed, k_right_pressed, k_up_pressed, k_down_pressed)
            self.update_map_coord(self.rect, pygame.Rect([xc, yc, TILE_SIZE, TILE_SIZE]))

            if (self.map_x, self.map_y) == self.path[-1]:
                self.path.pop()
        else:
            self.move(False, False, False, False, True)

    def update_as_player(self, *args, **kwargs) -> None:
        keys = pygame.key.get_pressed()

        k_pressed = sum(keys) != 0
        key_left_pressed = keys[pygame.K_a]
        key_right_pressed = keys[pygame.K_d]
        key_up_pressed = keys[pygame.K_w]
        key_down_pressed = keys[pygame.K_s]

        self.move(k_pressed, key_left_pressed, key_right_pressed, key_up_pressed, key_down_pressed)
        super(Enemy, self).update_map_coord(self.rect.x, self.rect.y)

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
        try:
            if distances[y][x] == inf:
                print_warning(f'Warning caused in find_path method. Program cant find '
                              f'path from enemy({self.map_x},{self.map_y}) to player({x},{y})')
                return False
        except IndexError:
            print_error(f'Error caused in find_path method. Wrong index: target({x},{y}),' +
                        f'map({len(self.map[0])},{len(self.map)})')
            return False

        self.path.clear()
        while prev[y][x] is not None:
            self.path.append((x, y))
            x, y = prev[y][x]

        return True


class Map:
    def __init__(self, players_number):
        self.player = None
        self.enemies = []
        self.map = []
        self.players_number = players_number
        self.coins_on_map = 0
        self.forced_lose = False

    def __str__(self):
        return '\n'.join(str(row) for row in self.map)

    def load(self, lvl):
        self.player, self.enemies, self.map, coins_dislocation = load_level(lvl)
        for y, x, in coins_dislocation:
            Coin(self.map, x=x, y=y)
        self.coins_on_map = len(coins_dislocation)

        if self.players_number == 2:
            suit_enemies = list(filter(lambda en: en.can_set_control_to_player, self.enemies))
            if suit_enemies:
                rd.choice(suit_enemies).set_control_to_player()

    def check_lose(self) -> bool:
        global is_win

        for enemy in enemies:
            if pygame.sprite.collide_mask(self.player, enemy) is not None or self.forced_lose:
                play_sound(lose_sound if LIVES != 1 else Player.died_sound)
                is_win = False
                return True
        return False

    @staticmethod
    def check_win() -> bool:
        global is_win
        if COIN_LEFT == 0:
            is_win = True
            play_sound(win_sound)
            return True
        return False

    def check_player_takes_coin(self):
        global COIN_AMOUNT, COIN_LEFT, CAN_DIG
        collision_coins = pygame.sprite.spritecollide(self.player, coins, True)
        collision_shovels = pygame.sprite.spritecollide(self.player, shovels, True)

        if collision_coins or collision_shovels:
            play_sound(Coin.sound if collision_coins else Shovel.sound)
            COIN_AMOUNT += 1
            COIN_LEFT -= 1
            self.coins_on_map -= 1

        if collision_shovels:
            CAN_DIG = True
            self.player.can_dig = True
            for shovel in shovels:
                shovel.kill()
                self.coins_on_map -= 1

    def check_destroyed_walls(self):
        if not destroyed_walls:
            return

        for (x, y), start_time in destroyed_walls.items():
            if time.time() - start_time >= 2:
                self.map[y][x] = Wall(x, y, True, walls)
                destroyed_walls.pop((x, y))

                if have_collision(self.player, walls):
                    self.forced_lose = True

                for enemy in self.enemies:
                    if have_collision(enemy, walls):
                        enemy.kill()
                        self.enemies.remove(enemy)
                        self.enemies.append(Enemy(enemy.x, enemy.y, enemy.can_set_conytol_to_player,
                                                  is_bot=enemy.is_bot))
                        play_sound(Enemy.died_sound)
                        break
                break

    def update_coins(self):
        if (self.coins_on_map < min(MAX_COINS, COIN_LEFT + 1) and rd.random() < COINS_PROBABILITY or
                self.coins_on_map == 0 and COIN_LEFT > 0):
            if lvl_index == 1 and COIN_LEFT - self.coins_on_map <= 1 and not self.player.can_dig:
                Shovel(self.map)
            else:
                Coin(self.map)
            self.coins_on_map += 1

    def update(self):
        self.check_player_takes_coin()
        self.check_destroyed_walls()
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

    def set_shift(self, x_shift, y_shift):
        self.rect = self.rect.move(x_shift, y_shift)

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
    fon = pygame.transform.scale(load_image(f"{DATA_DIR}/images/gameFon/{LEVEL_FON}"), SIZE)
    screen.blit(fon, (0, 0))

    all_sprites.draw(screen)
    coins.draw(screen)
    player.draw(screen)
    enemies.draw(screen)
    animations.draw(screen)

    show_text(screen, f'Жизней:', (0, 0), color=yellow)
    show_text(screen, heart_char * LIVES, (75, -8), 26, "segoeuisymbol", red)
    show_text(screen, f'Собрано монет: {COIN_AMOUNT}', (0, 24), color=yellow)
    show_text(screen, f'Осталось монет: {COIN_LEFT}', (0, 48), color=yellow)
    if is_pause:
        show_text(screen, 'Пауза', (WIDTH // 2 - 100, HEIGHT // 2 - 50), size=108, color=black)

    assert isinstance(game_map, Map)
    for game_object in [game_map.player] + game_map.enemies:
        game_object.draw_label()
    for enemy in game_map.enemies:
        for x, y in enemy.path:
            pygame.draw.circle(screen, green, ((x + 0.5) * TILE_SIZE, (y + 0.5) * TILE_SIZE), 10)


def play_game(lvl_name, players_number: int, is_new_game=False):
    global LIVES, game_map, lvl_index, tick_time

    sound = rd.choice(fon_game_music)
    play_sound(sound, -1, fade_ms=5000)

    clock = pygame.time.Clock()
    running = True

    game = True
    pause = False
    event = None

    if is_new_game:
        tick_time = timer()
        TIMERS.clear()
        LIVES = 5
        lvl_index = 0

    game_map = Map(players_number)
    game_map.load(lvl_name)
    if lvl_index == 2:
        anim = Animation("Now you can dig weak walls!")
        anim.set_shift(0, -50)
        anim1 = Animation(LEVEL_NAME)
        anim1.set_shift(0, 50)
    else:
        anim = Animation(LEVEL_NAME)

    while running:  # главный игровой цикл
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game:
                    pause = not pause
                    if pause:
                        TIMERS.append(timer() - tick_time)
                    else:
                        tick_time = timer()

            # обработка остальных событий
            # ...

        # формирование кадра
        if game and not pause and not anim:
            all_sprites.update(event)
            game_map.update()
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
                TIMERS.append(timer() - tick_time)
                anim = Animation('Вы победили')

        if not (game or anim):
            stop_sound(sound)
            for sprite in all_sprites:
                sprite.kill()

            if LIVES != 0:
                if is_win:
                    lvl_index += 1
                    tick_time = timer()
                if lvl_index >= len(LEVELS):
                    show_victory_screen(LIVES, int(sum(TIMERS)))
                    return False
                running = play_game(LEVELS[lvl_index], players_number)
            else:
                return False
        # ...
        pygame.display.flip()  # смена кадра

        # временная задержка
        clock.tick(fps)

    return False


if __name__ == '__main__':
    play_game('level3', 2)
