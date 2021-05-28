from constants import *
from sprite_groups import *
from victory_wnd import show_victory_screen
from collections import deque

import pygame
import time
import random as rd

# Базовые переменные старта игры
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
#


def set_size(x, y):
    """ Функция устанавливает размер экрана в зависимости от размера уровня """

    global SIZE, WIDTH, HEIGHT, screen

    SIZE = WIDTH, HEIGHT = (x * TILE_SIZE, y * TILE_SIZE)
    screen = pygame.display.set_mode(SIZE)


def load_level(lvl_name):
    """ Функция загружает уровень с названием lvl_name """

    global COIN_LEFT, COIN_AMOUNT, LEVEL_NAME, LEVEL_FON

    # Загрузка уровня
    with open(f"{DATA_DIR}/levels/{lvl_name}.txt") as lvl_file:
        LEVEL_NAME = lvl_file.readline().strip()
        COIN_LEFT = int(lvl_file.readline().strip())
        LEVEL_FON = lvl_file.readline().strip()
        COIN_AMOUNT = 0
        lvl = lvl_file.readlines()
    #

    lvl_map = []
    opponents = []
    coins_place = []
    hero = None

    # Создание поля игры
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
    #

    set_size(len(lvl_map[0]), len(lvl_map))  # Установка размера карты
    hero.set_map(lvl_map)  # Загрузка уровня игроку
    for enemy in opponents:
        enemy.set_map(lvl_map)  # Загрузка уровня врагам

    return hero, opponents, lvl_map, coins_place


class MapObject(pygame.sprite.Sprite):
    """ Абстрактный класс Объекта карты, описывающий поведение всех статических объектов карты """

    def __init__(self, x, y, *groups, size=(TILE_SIZE, TILE_SIZE)):
        super().__init__(*groups, all_sprites)
        self.image = pygame.Surface(size)

        self.x_shift = 0
        self.y_shift = 0

        # Размер объекта
        self.x = x * TILE_SIZE
        self.y = y * TILE_SIZE
        #

        # Позиция объекта
        self.rect = self.image.get_rect()
        self.rect.x = self.x + self.x_shift
        self.rect.y = self.y + self.y_shift
        #


class Wall(MapObject):
    """ Класс-наследник, описывающий стену на карте """

    # Инициализация картинок и звука стены
    wall_image = f"{DATA_DIR}/images/mapObjects/wall.png"
    wall_destroyed_image = f"{DATA_DIR}/images/mapObjects/wall2.png"
    wall_destroyed_sound = init_sound("destroyed_wall_sound.mp3", 0.15)
    #

    def __init__(self, x, y, is_destroyed, *groups):
        super().__init__(x, y, *groups, map_objects)
        self.image = load_image(Wall.wall_destroyed_image if is_destroyed else Wall.wall_image)
        self.is_destroyed = is_destroyed


class Ladder(MapObject):
    """ Класс-наследник, описывающий лестницу на карте """

    # Инициализация картинки лестницы #
    ladder_image = f"{DATA_DIR}/images/mapObjects/ladder.png"

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, map_objects)
        self.image = load_image(Ladder.ladder_image)


class Bridge(MapObject):
    """ Класс-наследник, описывающий мост на карте """

    # Инициализация картинки моста #
    height = 10
    bridge_image = f"{DATA_DIR}/images/mapObjects/bridge.png"

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, map_objects, size=(TILE_SIZE, Bridge.height))
        self.image.fill(white)


class Coin(MapObject):
    """ Класс-наследник, описывающий монету на карте """

    # Инициализация звука монеты #
    sound = init_sound("coin_up.mp3", 1)

    def __init__(self, lvl_map, *groups, x=None, y=None):
        """ Инициализация Монеты """

        # Выбор позиции для монеты
        if x is None or y is None:
            x = y = script = 0
            while not (lvl_map[y][x] is None and isinstance(lvl_map[y + 1][x], Wall) and script):
                x, y = rd.randint(0, len(lvl_map[0]) - 2), rd.randint(0, len(lvl_map) - 2)
                script = lvl_index != 2 or (x not in (1, 2) and y != 2)
        lvl_map[y][x] = self
        #

        super().__init__(x, y, *groups, coins)

        # Инициализация фреймов монеты
        self.frames = [load_image(f"{DATA_DIR}/images/coins/coin{i + 1}.png") for i in range(7)]
        self.cur_frame = 0
        self.image = load_image(f"{DATA_DIR}/images/shovel.png")
        self.image = self.frames[self.cur_frame]
        #

    def update(self, *args, **kwargs) -> None:
        """ Метод циклически меняет изображение монеты """

        self.cur_frame = (self.cur_frame + 1) % (len(self.frames) * 10)
        self.image = self.frames[self.cur_frame // 10]


class Shovel(MapObject):
    """ Класс-наследник, описывающий лопату на карте """

    # Инициализация звука лопаты #
    sound = init_sound("shovel_up.mp3", 1)

    def __init__(self, lvl_map, *groups):
        """ Инициализация лопаты """

        # Выбор позиции для лопаты
        x = y = 0
        while not (lvl_map[y][x] is None and isinstance(lvl_map[y + 1][x], Wall)):
            x, y = rd.randint(0, len(lvl_map[0]) - 2), rd.randint(0, len(lvl_map) - 2)
        #

        super().__init__(x, y, *groups, shovels)

        # Инициализация изображения лопаты
        self.image = load_image(f"{DATA_DIR}/images/shovel.png")


class ManagedGameObject(pygame.sprite.Sprite):
    """ Абстрактный класс для описания Движущихся Управляемых Объектов карты """

    def __init__(self, x, y, *groups):
        super().__init__(*groups, all_sprites)

        # Инициализация физических величин и фреймов анимации
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
        #

    def get_multiplayer(self) -> float:
        """ Метод возвращает множитель движения объекта """

        self.rect.y += 1
        # Если объект касается статических элементов, то скорость остается неизменной ..
        if have_collision(self, map_objects):
            self.rect.y -= 1
            return 1

        self.rect.y -= 1
        return 0.7  # .. иначе уменьшается

    def set_map(self, lvl):
        """ Метод устанавливает карту для объекта """
        self.map = lvl

    def set_image(self, left: bool, right: bool, up: bool, down: bool) -> None:
        """ Метод меняет картинки для анимации в зависимости от типа движения объекта """

        player_class = Player if isinstance(self, Player) else Enemy
        if left or right:  # При движении влево или вправо
            self.direction = right - 1
            self.walk_index = (self.walk_index + 1) % (len(player_class.walk) * 10)
            self.climb_index = 0

            self.image = player_class.walk[self.walk_index // 10]
        elif up or down:  # При движении вниз или вверх
            self.walk_index = 0
            self.climb_index = (self.climb_index + 1) % (len(player_class.climb) * 10)

            self.image = player_class.climb[self.climb_index // 10]
        else:  # Картинка стоящего объекта
            self.image = player_class.stand

        if self.direction == -1:  # Изменение направления картинки
            self.image = pygame.transform.flip(self.image, True, False)

    @staticmethod
    def correcting_position(obj_coord, col_coord, step):
        """
        Метод корректирует положение объекта (obj_coord) относительно целевого блока (col_coord),
        с учетом ограничения максимального сдвига (step)
        """

        if obj_coord - col_coord <= -step:
            return step
        if obj_coord - col_coord >= step:
            return -step
        return -(obj_coord - col_coord)  # Корректирование движения в центр целевого объекта

    def correcting_collision(self, wall: pygame.Rect, x_shift, y_shift):
        """ Метод корректирует коллизию объекта со стеной так, чтобы не было пересечений """

        if x_shift != 0:
            self.rect.x = wall.x + TILE_SIZE * (2 * (x_shift < 0) - 1)  # Смещение за блок по оси x
        if y_shift != 0:
            self.rect.y = wall.y + TILE_SIZE * (2 * (y_shift < 0) - 1)  # Смещение за блок по оси y

    def update_map_coord(self, x, y):
        """
        Метод обновляет map-позицию объекта на карте
        (x, y - координаты игрока на экране)
        (map_x, map_y - координаты позиции игрока на карте (номер клетки))
        """

        self.map_x = (x + TILE_SIZE // 2) // TILE_SIZE
        self.map_y = (y + TILE_SIZE // 2) // TILE_SIZE
    
    def move(self, k_pressed, key_left_pressed, key_right_pressed, key_up_pressed, key_down_pressed):
        """
        Метод выполняет управляемое движение объекта с учетом всей физики движения и коллизий
        :param k_pressed: Нажата ли клавиша (True/False)
        :param key_left_pressed: Нажата ли клавиша влево (True/False)
        :param key_right_pressed: Нажата ли клавиша вправо (True/False)
        :param key_up_pressed: Нажата ли клавиша вверх (True/False)
        :param key_down_pressed: Нажата ли клавиша вниз (True/False)
        """

        # Устанавливает изображение объекта в зависимости от типа его движения #
        self.set_image(key_left_pressed, key_right_pressed, key_up_pressed, key_down_pressed)

        # Проверка на то, что игрок находится в разрушенной стене #
        if (self.map_x, self.map_y + 1) in destroyed_walls:
            self.rect.x = self.map_x * TILE_SIZE

        self.rect.y += self.speed_v            # Падение игрока (сила тяжести)
        if have_collision(self, map_objects):  # Если игрок пересекся с map-объектом - отмена падения
            self.rect.y -= self.speed_v
        self.rect.y += 1                       # Проверка на устойчивое положение игрока
        if have_collision(self, map_objects):  # Если позиция устойчивая, то корректируем коллизию
            if have_collision(self, bridges) and (isinstance(self, Player) or not self.is_bot):
                # Если объект управляется игроком (причем не важно Player или Enemy),
                # то корректируем его позицию при коллизии с мостом
                y = have_collision(self, bridges).rect.y
                self.rect.y -= 1 if self.rect.y - y == 1 else 2 if self.rect.y - y > 1 else 0
            else:
                self.rect.y -= 1

        # Обработка нажатой клавиши
        x_shift = y_shift = 0
        if k_pressed:
            multiplayer = self.get_multiplayer()  # Получение множителя движения
            if key_left_pressed:  # Движение влево
                self.rect.x -= (self.speed_h * multiplayer)
                x_shift -= (self.speed_h * multiplayer)
            if key_right_pressed:  # Движение вправо
                self.rect.x += (self.speed_h * multiplayer)
                x_shift += (self.speed_h * multiplayer)

            if key_down_pressed:  # Движение вниз
                self.rect.y += 1  # Проверка коллизии с лестницами и мостами
                if not (have_collision(self, ladders) or have_collision(self, bridges)):
                    self.rect.y -= 1

            if have_collision(self, ladders):           # Если есть коллизия с лестницами
                ladder = have_collision(self, ladders)
                if key_up_pressed:                      # Корректировка позиции при движении вверх
                    self.rect.x += self.correcting_position(self.rect.x, ladder.rect.x, 6)
                    self.rect.y -= self.speed_h

                    x_shift = 0
                    y_shift -= self.speed_h
                if key_down_pressed:                    # Корректировка позиции при движении вниз
                    self.rect.x += self.correcting_position(self.rect.x, ladder.rect.x, 6)
                    self.rect.y += self.speed_h

                    x_shift = 0
                    y_shift += self.speed_h

            # Если есть коллизия с мостами и идет движение вниз (вверх невозможно при таких условиях)
            if have_collision(self, bridges) and key_down_pressed:
                # Плавная корректировка движения относительно моста
                if self.rect.y >= have_collision(self, bridges).rect.y:
                    self.rect.y += Bridge.height
                    y_shift += Bridge.height
                else:
                    self.rect.y += self.speed_h
                    y_shift += self.speed_h
        #

        # Если при движении произошла коллизия со стенами, то корректируем позицию относительно стены
        if have_collision(self, walls) and x_shift + y_shift != 0:
            self.correcting_collision(have_collision(self, walls).rect, x_shift, y_shift)
            if have_collision(self, ladders) and x_shift != 0:
                self.rect.y -= 1  # Корректирование малой коллизии при подъеме по лестнице
            while have_collision(self, walls):
                self.rect.y += 1


class Player(ManagedGameObject):
    """ Класс-наследник, описывающий основного игрока """

    # Инициализация картинок для анимация движения
    dir = f"{DATA_DIR}/images/player/"
    walk = [load_image(f"{dir}player_walk1.png"), load_image(f"{dir}player_walk2.png")]
    climb = [load_image(f"{dir}player_climb1.png"), load_image(f"{dir}player_climb2.png")]
    stand = load_image(f"{dir}player_stand.png")
    #

    died_sound = init_sound('death5.mp3')  # Инициализация звука смерти игрока

    def __init__(self, x, y, *groups):
        super().__init__(x, y, *groups, player)
        self.image = load_image(f"{DATA_DIR}/images/player/player_stand.png")
        self.mask = pygame.mask.from_surface(self.image)
        self.can_dig = CAN_DIG

        # Инициализация скорости игрока
        self.speed_h = 5
        self.speed_v = 4
        #

    def update(self, *args, **kwargs) -> None:
        """ Метод обновляет позицию игрока """

        # получение нажатых клавиш
        keys = pygame.key.get_pressed()

        k_pressed = sum(keys) != 0
        key_left_pressed = keys[pygame.K_LEFT]
        key_right_pressed = keys[pygame.K_RIGHT]
        key_up_pressed = keys[pygame.K_UP]
        key_down_pressed = keys[pygame.K_DOWN]
        #

        # Обработка копания стен
        if keys[pygame.K_l] and self.can_dig:
            x, y = self.map_x, self.map_y
            d = self.direction * 2 + 1

            # Если объект в стороне движения можно сломать ..
            if isinstance(self.map[y + 1][x], MapObject) and \
                    isinstance(self.map[y + 1][x + d], Wall) and self.map[y + 1][x + d].is_destroyed:

                # .. разрушаем стену ..
                destroyed_walls[(x + d, y + 1)] = time.time()
                self.map[y + 1][x + d].kill()
                self.map[y + 1][x + d] = None

                # .. проигрываем звук разрушения и создаем частицы разрушенной стены
                play_sound(Wall.wall_destroyed_sound)
                create_particles(((x + d) * TILE_SIZE + TILE_SIZE // 2,
                                  (y + 1) * TILE_SIZE + TILE_SIZE // 2))
                #

        # Движение игрока и обновление его позиции
        self.move(k_pressed, key_left_pressed, key_right_pressed, key_up_pressed, key_down_pressed)
        self.update_map_coord(self.rect.x, self.rect.y)
        #

    def draw_label(self):
        """ Метод рисует метку над игроком """

        # Текст метки
        font = pygame.font.Font(None, 18)
        text = font.render("Player 1", True, yellow)
        #

        # Позиция метки
        tw, th = text.get_size()
        x, y = self.rect.x + TILE_SIZE // 2 - tw // 2, self.rect.y - th
        #

        pygame.draw.rect(screen, blue, (x - 2, y - 2, tw + 4, th + 4), 2)
        screen.blit(text, (x, y))


class Enemy(ManagedGameObject):
    """ Класс-наследник, описывающий поведение врага """

    # Инициализация картинок для анимация движения
    dir = f"{DATA_DIR}/images/enemy/"
    walk = [load_image(f"{dir}zombie_walk1.png"), load_image(f"{dir}zombie_walk2.png")]
    climb = [load_image(f"{dir}zombie_climb1.png"), load_image(f"{dir}zombie_climb2.png")]
    stand = load_image(f"{dir}/zombie_stand.png")
    #

    # Инициализация звука смерти зомби
    died_sound = init_sound("zombie_died_sound.mp3")

    def __init__(self, x, y, can_set_control_to_player, *groups, is_bot=True):
        super().__init__(x, y, enemies, *groups)

        # Инициализация маски для коллизии и основных функция врага
        self.image = load_image(f"{DATA_DIR}/images/enemy/zombie_stand.png")
        self.mask = pygame.mask.from_surface(self.image)
        self.update = self.update_as_bot if is_bot else self.update_as_player
        self.can_set_control_to_player = can_set_control_to_player
        self.is_bot = is_bot
        #

        self.x = x
        self.y = y

        self.path = []

        # Инициализация скорости врага
        self.speed_h = 3
        self.speed_v = 3
        #

    def set_control_to_player(self):
        """ Метод устанавливает контроль врага за игроком """
        self.update = self.update_as_player
        self.is_bot = False

    def get_all_enemies_pos(self):
        """ Получение позиций всех врагов для предотвращения их коллизий между собой """

        assert isinstance(game_map, Map)
        self.enemies_pos = [(en.map_x, en.map_y) for en in game_map.enemies]

    def get_player_pos(self):
        """ Получение позиции игрока для поиска пути к нему """
        assert isinstance(game_map, Map)
        self.px, self.py = game_map.player.map_x, game_map.player.map_y

    def draw_label(self):
        """ Метод рисует метку над врагом """

        if self.is_bot:  # Рисование происходит, если врагом управляет игрок
            return

        # Текст метки
        font = pygame.font.Font(None, 18)
        text = font.render("Player 2", True, yellow)
        #

        # положение метки
        tw, th = text.get_size()
        x, y = self.rect.x + TILE_SIZE // 2 - tw // 2, self.rect.y - th
        #

        pygame.draw.rect(screen, red, (x - 2, y - 2, tw + 4, th + 4), 2)
        screen.blit(text, (x, y))

    def update_map_coord(self, p_rect, t_rect):
        """ Обновление map-позиции врага на карте """

        collision = p_rect.clip(t_rect)
        # Определение относительной площади пересечения врага и целевого блока
        if (collision.w * collision.h) / (TILE_SIZE ** 2) >= 0.9:
            self.map_x = t_rect.x // TILE_SIZE
            self.map_y = t_rect.y // TILE_SIZE

    def update_as_bot(self, *args, **kwargs) -> None:
        """ Обновление позиции врага, если это бот """

        # Построение пути к игроку
        self.get_player_pos()
        self.get_all_enemies_pos()
        path = self.find_path((self.map_x, self.map_y), (self.px, self.py))
        #

        # Если путь найден или еще определен (в случае когда до игрока не удается построить маршрут)
        if path or len(self.path) > 2:
            x, y = self.path[-1]
            xc, yc = x * TILE_SIZE, y * TILE_SIZE
            px, py = self.rect.x, self.rect.y

            if any(pos == (x, y) for pos in self.enemies_pos):  # Предотвращение коллизий врагов
                return

            # Симуляция нажатых клавиш, в зависимости от того, куда надо двигаться боту
            k_pressed = px != xc or py != yc
            k_left_pressed = k_right_pressed = k_up_pressed = k_down_pressed = False
            # Определение движения в сторону большей разницы координат врага и игрока
            if abs(px - xc) > abs(py - yc):   # Проверка движения по оси x
                self.rect.y = yc
                if px > xc:                   # Движение влево
                    k_left_pressed = px > xc
                elif px < xc:                 # Движение вправо
                    k_right_pressed = px < xc
            else:                             # Проверка движения по оси y
                self.rect.x = xc
                if py > yc:                   # Движение вверх
                    k_up_pressed = py > yc
                elif py < yc:                 # Движение вниз
                    k_down_pressed = py < yc

            # Движение бота и обновление его позиции на карте
            self.move(k_pressed, k_left_pressed, k_right_pressed, k_up_pressed, k_down_pressed)
            self.update_map_coord(self.rect, pygame.Rect([xc, yc, TILE_SIZE, TILE_SIZE]))
            #

            # Если дошли до одного блока из пути, то удаляем этот блок из массива пути
            if (self.map_x, self.map_y) == self.path[-1]:
                self.path.pop()
        else:  # Если пути не найдено то бот стоит на месте**
            # ** При отсутствии пути происходит симуляция движения вниз для анимации "зомби злится"
            self.move(False, False, False, False, True)

    def update_as_player(self, *args, **kwargs) -> None:
        """ Обновление позиции врага, если им управляет игрок """

        # Получение нажатых клавиш
        keys = pygame.key.get_pressed()

        k_pressed = sum(keys) != 0
        key_left_pressed = keys[pygame.K_a]
        key_right_pressed = keys[pygame.K_d]
        key_up_pressed = keys[pygame.K_w]
        key_down_pressed = keys[pygame.K_s]
        #

        # Движение врага и обновление его map-позиции родительским методом
        self.move(k_pressed, key_left_pressed, key_right_pressed, key_up_pressed, key_down_pressed)
        super(Enemy, self).update_map_coord(self.rect.x, self.rect.y)

    def is_free(self, x, y, dx, dy) -> bool:
        """ Метод проверяет возможность движения в клетку (x+dx, y+dy) """

        if isinstance(self.map[y + dy][x + dx], Wall):
            return False
        if dy == -1 and not isinstance(self.map[y][x], Ladder):
            return False
        if (dx != 0 and not isinstance(self.map[y + 1][x], (Wall, Ladder))
                and not isinstance(self.map[y][x], Bridge)):
            return False
        return True

    def find_path(self, start: (list, tuple), target: (list, tuple)) -> bool:
        """ Метод строит маршрут на карте между 2 точками, используя волновой алгоритм """

        if start == target:  # Если мы пришли в целевую точку - путь найден
            return True

        # Инициализация переменных для алгоритма
        inf = float('inf')
        w, h = len(self.map[0]), len(self.map)
        x, y = start
        distances = [[inf] * w for _ in range(h)]
        distances[y][x] = 0
        prev = [[None] * w for _ in range(h)]
        queue = deque([(x, y)])
        #

        # Обход в ширину
        while queue:
            x, y = queue.popleft()
            for dx, dy in (-1, 0), (0, -1), (1, 0), (0, 1):
                next_x, next_y = x + dx, y + dy
                if (0 <= next_x < w and 0 <= next_y < h and
                        self.is_free(x, y, dx, dy) and distances[next_y][next_x] == inf):
                    distances[next_y][next_x] = distances[y][x] + 1
                    prev[next_y][next_x] = (x, y)
                    queue.append((next_x, next_y))
        #

        x, y = target
        try:  # Проверка на возможность нахождения пути
            if distances[y][x] == inf:
                print_warning(f'Warning caused in find_path method. Program cant find '
                              f'path from enemy({self.map_x},{self.map_y}) to player({x},{y})')
                return False
        except IndexError:  # Ошибка индекса. Необходимо проверить корректность загрузки карты
            print_error(f'Error caused in find_path method. Wrong index: target({x},{y}),' +
                        f'map({len(self.map[0])},{len(self.map)})')
            return False

        # Составление обновленного пути
        self.path.clear()
        while prev[y][x] is not None:
            self.path.append((x, y))
            x, y = prev[y][x]
        #

        return True  # Путь найден


class Map:
    """ Класс для реализации карты уровня """

    def __init__(self, players_number):
        """ Инициализация всех объектов карты """

        self.player = None
        self.enemies = []
        self.map = []
        self.players_number = players_number
        self.coins_on_map = 0
        self.forced_lose = False

    def __str__(self):
        """ Удобное отображение карты """
        return '\n'.join(str(row) for row in self.map)

    def load(self, lvl):
        """ Загрузка уровня """

        # Начальная загрузка монет
        self.player, self.enemies, self.map, coins_dislocation = load_level(lvl)
        for y, x, in coins_dislocation:
            Coin(self.map, x=x, y=y)
        self.coins_on_map = len(coins_dislocation)
        #

        # Если идет игра вдвоем, то выбор врага, которым будет управлять второй игрок
        if self.players_number == 2:
            suit_enemies = list(filter(lambda en: en.can_set_control_to_player, self.enemies))
            if suit_enemies:
                rd.choice(suit_enemies).set_control_to_player()
        #

    def check_lose(self) -> bool:
        """ Метод проверяет поражение в игрена карте """

        for enemy in enemies:
            # Если хоть один из врагов имеет коллизию с игроком - поражение
            if pygame.sprite.collide_mask(self.player, enemy) is not None or self.forced_lose:
                play_sound(lose_sound if LIVES != 1 else Player.died_sound)
                is_win = False
                return True
        return False

    @staticmethod
    def check_win() -> bool:
        """ Метод проверяет победу на карте """

        global is_win
        if COIN_LEFT == 0:  # Если все монеты собраны - победа
            is_win = True
            play_sound(win_sound)
            return True
        return False

    def check_player_takes_coin(self):
        """ Метод не проверяет подобрал ли игрок монету (лопату) """

        global COIN_AMOUNT, COIN_LEFT, CAN_DIG
        collision_coins = pygame.sprite.spritecollide(self.player, coins, True)
        collision_shovels = pygame.sprite.spritecollide(self.player, shovels, True)

        if collision_coins or collision_shovels:  # Если подобрана монета - обновляем счетчики
            play_sound(Coin.sound if collision_coins else Shovel.sound)
            COIN_AMOUNT += 1
            COIN_LEFT -= 1
            self.coins_on_map -= 1

        if collision_shovels:  # Если подобрана лопата - обновляем счетчики и разрешаем игроку копать
            CAN_DIG = True
            self.player.can_dig = True
            for shovel in shovels:
                shovel.kill()
                self.coins_on_map -= 1

    def check_destroyed_walls(self):
        """ Метод проверяет необходимость восстанавливать разрушенные стены """

        if not destroyed_walls:  # Если нет разрушенных стен - выход
            return

        for (x, y), start_time in destroyed_walls.items():
            # Для каждой разрушенной стены смотрим, сколько времени она разрушена
            if time.time() - start_time >= DESTROYED_TIME:
                self.map[y][x] = Wall(x, y, True, walls)
                destroyed_walls.pop((x, y))

                # Если игрок находится в коллизии восстанавливаемой стены - форсируем проигрыш
                if have_collision(self.player, walls):
                    self.forced_lose = True

                for enemy in self.enemies:
                    # Если один из врагов оказался в коллизии восстанавливаемой стены - убиваем врага
                    if have_collision(enemy, walls):
                        enemy.kill()
                        self.enemies.remove(enemy)
                        self.enemies.append(Enemy(enemy.x, enemy.y, enemy.can_set_control_to_player,
                                                  is_bot=enemy.is_bot))
                        play_sound(Enemy.died_sound)
                        break
                break

    def update_coins(self):
        """ Метод обновляет монеты на уровне """

        if (self.coins_on_map < min(MAX_COINS, COIN_LEFT + 1) and rd.random() < COINS_PROBABILITY or
                self.coins_on_map == 0 and COIN_LEFT > 0):
            # Скрипт для создания лопаты на 2 уровне в конце уровня
            if lvl_index == 1 and COIN_LEFT - self.coins_on_map <= 1 and not self.player.can_dig:
                Shovel(self.map)
            else:
                Coin(self.map)
            #
            self.coins_on_map += 1

    def update(self):
        """ Метод обновляет все параметры уровня """

        self.check_player_takes_coin()
        self.check_destroyed_walls()
        self.update_coins()


class Animation(pygame.sprite.Sprite):
    """ Класс анимации """

    def __init__(self, level_name: str, *groups):
        super().__init__(*groups, all_sprites, animations)

        # Инициализация позиции анимации
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
        #

    def __bool__(self):
        return self.image.get_alpha() != 0

    def set_shift(self, x_shift, y_shift):
        """ Метод двигает анимацию по осям x и y """
        self.rect = self.rect.move(x_shift, y_shift)

    def update(self, *args, **kwargs) -> None:
        """ Обновление анимации """

        # Проверка состояния паузы игры
        if kwargs.get('is_pause', None) is True:
            self.increase = False
            self.image.set_alpha(0)
        #

        # Изменение visibility анимации
        if self.increase:
            self.image.set_alpha(min(255, self.image.get_alpha() + 2))
            self.increase = self.image.get_alpha() < 255
        elif self.image.get_alpha() != 0:
            self.image.set_alpha(max(0, self.image.get_alpha() - 4))
        else:
            self.kill()
        #


class DestroyedWallAnimation(pygame.sprite.Sprite):
    """ Класс анимации разрушения стены """

    wall_destroyed_image = load_image(f"{DATA_DIR}/images/mapObjects/wall2.png")

    # Создание анимированных частиц
    fire = []
    for scale in (5, 10, 20):
        fire.append(pygame.transform.scale(wall_destroyed_image, (scale, scale)))
    #

    def __init__(self, pos, dx, dy):
        super().__init__(all_sprites)
        self.image = rd.choice(self.fire)
        self.rect = self.image.get_rect()

        # Физические величины частиц анимации
        self.velocity = [dx, dy]
        self.rect.x, self.rect.y = pos
        self.gravity = 1
        #

    def update(self, *args, **kwargs):
        """ Метод обновляет позиции частиц """

        self.velocity[1] += self.gravity
        self.rect.x += self.velocity[0]
        self.rect.y += self.velocity[1]

        # Если частицы вылетели за границы экрана - уничтожаем их
        if not self.rect.colliderect(pygame.Rect([0, 0, *SIZE])):
            self.kill()


def create_particles(position):
    """ Функция создает частицы разрушенной стены произвольного размера и скорости """

    particle_count = 50
    numbers = range(-5, 6)

    for _ in range(particle_count):
        DestroyedWallAnimation(position, rd.choice(numbers), rd.choice(numbers))


def draw(is_pause):
    """ Метод рисует все объекты на экране """

    # Фон
    fon = pygame.transform.scale(load_image(f"{DATA_DIR}/images/gameFon/{LEVEL_FON}", scale=None),
                                 SIZE)
    screen.blit(fon, (0, 0))
    #

    # Спрайты
    all_sprites.draw(screen)
    coins.draw(screen)
    player.draw(screen)
    enemies.draw(screen)
    animations.draw(screen)
    #

    # Текст
    show_text(screen, f'Жизней:', (0, 0), color=yellow)
    show_text(screen, heart_char * LIVES, (75, -8), 26, "segoeuisymbol", red)
    show_text(screen, f'Собрано монет: {COIN_AMOUNT}', (0, 24), color=yellow)
    show_text(screen, f'Осталось монет: {COIN_LEFT}', (0, 48), color=yellow)
    if is_pause:
        show_text(screen, 'Пауза', (WIDTH // 2 - 100, HEIGHT // 2 - 50), size=108, color=black)
    #

    # Метки игроков
    assert isinstance(game_map, Map)
    for game_object in [game_map.player] + game_map.enemies:
        game_object.draw_label()
    #


def play_game(lvl_name, players_number: int, is_new_game=False):
    """ Функция запускает и обрабатывает игровой цикл """

    global LIVES, CAN_DIG, game_map, destroyed_walls, lvl_index, tick_time, is_win

    # Фоновая музыка
    sound = rd.choice(fon_game_music)
    play_sound(sound, -1, fade_ms=5000)
    #

    # Основные переменные игры
    clock = pygame.time.Clock()
    running = True

    game = True
    pause = False
    event = None
    is_win = None

    destroyed_walls = {}
    #

    if is_new_game:  # Обновление переменных, если игра новая
        tick_time = timer()
        TIMERS.clear()
        CAN_DIG = False
        LIVES = 5
        lvl_index = 0

    # Загрузка уровня
    game_map = Map(players_number)
    game_map.load(lvl_name)
    #

    if lvl_index == 2:  # Скрипт для сообщения о возможности копания
        anim = Animation("Now you can dig weak walls (press L)!")
        anim.set_shift(0, -50)
        anim1 = Animation(LEVEL_NAME)
        anim1.set_shift(0, 50)
    else:  # Анимация нового уровня
        anim = Animation(LEVEL_NAME)

    while running:  # главный игровой цикл
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

            # Обработка событий игры
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and game:
                    pause = not pause
                    if pause:
                        TIMERS.append(timer() - tick_time)
                    else:
                        tick_time = timer()
                if event.key == pygame.K_ESCAPE:
                    stop_sound(sound)
                    for sprite in all_sprites:
                        sprite.kill()

                    return False
            #

        # формирование кадра
        if game and not pause and not anim:
            all_sprites.update(event)
            game_map.update()
        else:
            animations.update(event, is_pause=pause)
        #

        draw(pause)

        # изменение игрового мира
        if game and not pause:  # Проверка продолжения игры
            game = not game_map.check_lose()
            if not game:
                LIVES -= 1
                anim = Animation('Вы проиграли' if LIVES != 0 else 'Вас убили!')
        if game and not pause:  # Проверка продолжения игры (победа)
            game = not game_map.check_win()
            if not game:
                TIMERS.append(timer() - tick_time)
                anim = Animation('Вы победили')

        if not (game or anim):  # Если уровень завершен (победа/поражение) - очистка уровня
            stop_sound(sound)
            for sprite in all_sprites:
                sprite.kill()

            if LIVES != 0:                    # Проверка запуска нового уровня*
                if is_win:                    # * Если победа то новый уровень
                    lvl_index += 1
                    tick_time = timer()
                print(lvl_index)
                if lvl_index >= len(LEVELS):  # Если уровни закончились - глобальная победа
                    show_victory_screen(LIVES, int(sum(TIMERS)))
                    return False
                running = play_game(LEVELS[lvl_index], players_number)  # Запуск нового уровня
            else:
                print('end')
                return False
        #

        pygame.display.flip()  # смена кадра

        # временная задержка
        clock.tick(fps)

    return False


if __name__ == '__main__':
    play_game('level3', 1)
