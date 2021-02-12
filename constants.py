import os
import sys
import time
import pygame

pygame.init()

# Цвета
black = pygame.Color('black')
white = pygame.Color('white')
red = pygame.Color('red')
green = pygame.Color('green')
blue = pygame.Color('blue')
orange = pygame.Color('orange')
yellow = pygame.Color('yellow')
gray = pygame.Color('gray')

have_collision = pygame.sprite.spritecollideany
heart_char = chr(10_084)
fps = 60

DATA_DIR = "F:/3_Programming/Python/Python_Projects/GoldRunnerGame/resources"
MY_DB = "game_highscores.sqlite"
LEVELS = ["level1", "level2", "level3"]
TIMERS = []
TILE_SIZE = 40
MAX_COINS = 5
DESTROYED_TIME = 2
COINS_PROBABILITY = 0.005


def init_sound(sound_name, volume=0.5):
    sound = pygame.mixer.Sound(f"{DATA_DIR}/sounds/{sound_name}")
    sound.set_volume(volume)

    return sound


def play_sound(sound, loops=0, start=0, fade_ms=0):
    sound.play(loops, start, fade_ms)


def stop_sound(sound):
    sound.stop()


fon_game_music = [init_sound("game_fon.mp3", 0.1), init_sound("game_fon1.mp3", 0.1),
                  init_sound("game_fon2.mp3", 0.1), init_sound("game_fon3.mp3", 0.1)]
fon_menu_music = init_sound("menu_fon.mp3", 0.1)
victory_music = init_sound("victory_music.mp3", 0.1)
lose_sound = init_sound("lose.mp3", 0.15)
win_sound = init_sound("win.mp3")


def terminate():
    pygame.quit()
    sys.exit()


def timer():
    return time.time()


def print_warning(*args):
    for text in args:
        print("\033[33m{}\033[0m".format(str(text)), end=' ')
    print()


def print_error(*args):
    for text in args:
        print("\033[31m{}\033[0m".format(str(text)), end=' ')
    print()


def show_text(surface, text, position: (list, tuple), size=26, font=None, color=black,
              is_centered_coordinates=False):
    font = pygame.font.SysFont(font, size)
    text = font.render(text, True, color)
    text_x, text_y = position

    if is_centered_coordinates:
        position = (text_x - text.get_width() // 2, text_y - text.get_height() // 2)
    surface.blit(text, position)


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
        print_error(f"Файл с изображением '{full_name}' не найден")
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
