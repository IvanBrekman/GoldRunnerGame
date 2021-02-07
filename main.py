import game
from constants import *

import pygame
import pygame_gui
import sqlite3
import datetime as dt

SIZE = WIDTH, HEIGHT = (800, 600)
screen = pygame.display.set_mode(SIZE)

pygame.init()  # Инициализация движка pygame
manager = pygame_gui.UIManager(SIZE)

fon = pygame.transform.scale(load_image(f"{DATA_DIR}/images/gameFon/menu_fon.jpg"), SIZE)

button = pygame_gui.elements.UIButton

start_btn = button(pygame.Rect(WIDTH // 2 - 100, 200, 200, 50), "Начать", manager)
one_player_btn = button(pygame.Rect(WIDTH // 2 - 250, 250, 200, 100), "1 Игрок", manager)
two_player_btn = button(pygame.Rect(WIDTH // 2 + 50, 250, 200, 100), "2 Игрока", manager)

description_btn = button(pygame.Rect(WIDTH // 2 - 100, 275, 200, 50), "Как играть", manager)
highscores_btn = button(pygame.Rect(WIDTH // 2 - 100, 350, 200, 50), "Доска лидеров", manager)

exit_btn = button(pygame.Rect(WIDTH // 2 - 100, 425, 200, 50), "Выйти из игры", manager)
back_btn = button(pygame.Rect(WIDTH // 2 - 100, 500, 200, 50), "Назад", manager)
clock = pygame.time.Clock()


def get_highscores() -> iter:
    con = sqlite3.connect(f"{DATA_DIR}/database/{MY_DB}")
    cur = con.cursor()

    request = """SELECT player_name, time, lives FROM highscores
                 ORDER BY time, lives DESC, player_name LIMIT 5"""
    info = cur.execute(request).fetchall()

    con.close()
    return enumerate(info, 1)


def hide():
    start_btn.hide()
    description_btn.hide()
    highscores_btn.hide()
    exit_btn.hide()
    back_btn.show()


def draw_main_view():
    start_btn.show()
    description_btn.show()
    highscores_btn.show()
    exit_btn.show()

    one_player_btn.hide()
    two_player_btn.hide()
    back_btn.hide()

    screen.blit(fon, (0, 0))
    show_text(screen, "Расхититель гробниц", (WIDTH // 2, 100), 60, None, white, True)


def draw_description_view():
    hide()
    screen.blit(fon, (0, 0))

    show_text(screen, "Как играть:", (50, 100), 60, None, white)
    show_text(screen, "Перемещайте игрока с помощью стрелок", (50, 200), 48, None, white)
    show_text(screen, "и собирайте монеты", (50, 240), 48, None, white)
    show_text(screen, "Чтобы поставить/снять игру с паузы", (50, 300), 48, None, white)
    show_text(screen, "нажмите пробел", (50, 340), 48, None, white)


def draw_highscores_view():
    hide()
    screen.blit(fon, (0, 0))

    show_text(screen, "Доска лидеров", (WIDTH // 2, 75), 60, None, red, True)
    scores = get_highscores()

    show_text(screen, "Игрок" + " " * 28 + "Время" + " " * 28 + "Жизни", (130, 125), 36,
              color=yellow)
    for pos, (player, seconds, lives) in scores:
        show_text(screen, f"{pos}.  {player}", (100, 110 + pos * 65), 36, color=white)
        show_text(screen, dt.timedelta(seconds=seconds).__str__(), (400, 110 + pos * 65), 36,
                  color=white)
        show_text(screen, str(lives), (700, 110 + pos * 65), 36, color=white)


def draw_select_game_mode_view():
    hide()
    one_player_btn.show()
    two_player_btn.show()

    screen.blit(fon, (0, 0))

    show_text(screen, "Выберите режим игры", (WIDTH // 2, 75), 60, None, white, True)


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
                        draw = draw_select_game_mode_view
                    if e.ui_element in (one_player_btn, two_player_btn):
                        stop_sound(fon_menu_music)
                        game.play_game('level1', (e.ui_element == two_player_btn) + 1, True)

                        play_sound(fon_menu_music, -1)
                        draw = draw_main_view
                        screen = pygame.display.set_mode(SIZE)
                    if e.ui_element == description_btn:
                        draw = draw_description_view
                    if e.ui_element == highscores_btn:
                        draw = draw_highscores_view
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
    play_sound(fon_menu_music, -1)
    start_screen()
