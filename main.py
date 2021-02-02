import os
import sys

import game
from constants import *

import pygame
import pygame_gui

SIZE = WIDTH, HEIGHT = (800, 600)
screen = pygame.display.set_mode(SIZE)

pygame.init()  # Инициализация движка pygame
manager = pygame_gui.UIManager(SIZE)

start_btn = pygame_gui.elements.UIButton(pygame.Rect(WIDTH // 2 - 100, 200, 200, 50),
                                         "Начать", manager)
exit_btn = pygame_gui.elements.UIButton(pygame.Rect(WIDTH // 2 - 100, 400, 200, 50),
                                        "Выйти из игры", manager)


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


def draw():
    intro_text = "Расхититель гробниц"
    fon = pygame.transform.scale(load_image(f"{DATA_DIR}/images/menu_fon.jpg"), SIZE)
    screen.blit(fon, (0, 0))

    font = pygame.font.Font(None, 60)
    text = font.render(intro_text, True, white)
    screen.blit(text, (WIDTH // 2 - text.get_width() // 2, 100))


def start_screen():
    global screen

    while True:
        time_del = clock.tick(fps) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                terminate()

            if e.type == pygame.USEREVENT:
                if e.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if e.ui_element == start_btn:
                        game.start_game('level1', True)
                        screen = pygame.display.set_mode(SIZE)
                    if e.ui_element == exit_btn:
                        terminate()

            manager.process_events(e)

        draw()

        manager.update(time_del)
        manager.draw_ui(screen)

        pygame.display.flip()
        clock.tick(fps)


def terminate():
    pygame.quit()
    sys.exit()


if __name__ == '__main__':
    fps = 60  # количество кадров в секунду
    clock = pygame.time.Clock()

    start_screen()
