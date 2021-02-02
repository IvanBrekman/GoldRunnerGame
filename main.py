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
description_btn = pygame_gui.elements.UIButton(pygame.Rect(WIDTH // 2 - 100, 300, 200, 50),
                                               "Как играть", manager)
exit_btn = pygame_gui.elements.UIButton(pygame.Rect(WIDTH // 2 - 100, 400, 200, 50),
                                        "Выйти из игры", manager)
back_btn = pygame_gui.elements.UIButton(pygame.Rect(WIDTH // 2 - 100, 500, 200, 50),
                                        "Назад", manager)


def draw_main_view():
    start_btn.show()
    description_btn.show()
    exit_btn.show()
    back_btn.hide()
    fon = pygame.transform.scale(load_image(f"{DATA_DIR}/images/menu_fon.jpg"), SIZE)
    screen.blit(fon, (0, 0))

    show_text(screen, "Расхититель гробниц", (WIDTH // 2, 100), 60, None, white, True)


def draw_description_view():
    start_btn.hide()
    description_btn.hide()
    exit_btn.hide()
    back_btn.show()

    fon = pygame.transform.scale(load_image(f"{DATA_DIR}/images/menu_fon.jpg"), SIZE)
    screen.blit(fon, (0, 0))

    show_text(screen, "Как играть:", (50, 100), 60, None, white)
    show_text(screen, "Перемещайте игрока с помощью стрелок", (50, 200), 48, None, white)
    show_text(screen, "и собирайте монеты", (50, 240), 48, None, white)
    show_text(screen, "Чтобы поставить/снять игру с паузы", (50, 300), 48, None, white)
    show_text(screen, "нажмите пробел", (50, 340), 48, None, white)


def start_screen():
    global screen
    draw = draw_main_view

    while True:
        time_del = clock.tick(fps) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                terminate()

            if e.type == pygame.USEREVENT:
                if e.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if e.ui_element == start_btn:
                        game.play_game('level1', True)
                        screen = pygame.display.set_mode(SIZE)
                    if e.ui_element == description_btn:
                        draw = draw_description_view
                    if e.ui_element == exit_btn:
                        terminate()
                    if e.ui_element == back_btn:
                        draw = draw_main_view

            manager.process_events(e)

        draw()

        manager.update(time_del)
        manager.draw_ui(screen)

        pygame.display.flip()
        clock.tick(fps)


if __name__ == '__main__':
    fps = 60  # количество кадров в секунду
    clock = pygame.time.Clock()

    start_screen()
