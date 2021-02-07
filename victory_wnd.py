from constants import *

import pygame
import pygame_gui
import sqlite3
import datetime as dt

SIZE = WIDTH, HEIGHT = (800, 600)
screen = pygame.display.set_mode(SIZE)

pygame.init()  # Инициализация движка pygame
manager = pygame_gui.UIManager(SIZE)

menu_btn = pygame_gui.elements.UIButton(pygame.Rect(WIDTH // 2 - 100, 500, 200, 50),
                                        "Главное меню", manager)
player_name_tel = pygame_gui.elements.UITextEntryLine(pygame.Rect(325, 403, 400, 100), manager)
player_name_tel.set_text_length_limit(10)
player_name_tel.set_text("Player")

clock = pygame.time.Clock()


def save_score(name, total_time, lives):
    con = sqlite3.connect(f"{DATA_DIR}/database/{MY_DB}")
    cur = con.cursor()

    request = f"""INSERT INTO highscores(player_name, time, lives)
                  VALUES ('{name or 'Player'}', {total_time}, {lives})"""
    cur.execute(request)

    con.commit()
    con.close()


def draw(lives, seconds):
    fon = pygame.transform.scale(load_image(f"{DATA_DIR}/images/gameFon/menu_fon.jpg"), SIZE)
    screen.blit(fon, (0, 0))

    show_text(screen, "Итоговый счет", (WIDTH // 2, 100), 60, None, white, True)
    show_text(screen, f"Оставшиеся жизни: {lives}", (WIDTH // 2, 200), 60, None, white, True)
    show_text(screen, f"Время прохождения: {dt.timedelta(seconds=seconds).__str__()}",
              (WIDTH // 2, 300), 60, None, white, True)
    show_text(screen, "Имя игрока: ", (WIDTH // 2 - 300, 400), 48, None, white)


def show_victory_screen(lives, seconds):
    global screen
    screen = pygame.display.set_mode(SIZE)
    play_sound(victory_music, -1)

    while True:
        time_del = clock.tick(fps) / 1000
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                terminate()

            if e.type == pygame.USEREVENT:
                if e.user_type == pygame_gui.UI_BUTTON_PRESSED:
                    if e.ui_element == menu_btn:
                        save_score(player_name_tel.text, seconds, lives)
                        stop_sound(victory_music)
                        return

            manager.process_events(e)

        draw(lives, seconds)

        manager.update(time_del)
        manager.draw_ui(screen)

        pygame.display.flip()
        clock.tick(fps)


if __name__ == '__main__':
    show_victory_screen(5, 12)
