import pygame

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

DATA_DIR = "F:/3_Programming/Python/Python_Projects/GoldRunnerGame/resources"
LEVELS = ["level1", "level2"]
TILE_SIZE = 40
MAX_COINS = 5
COINS_PROBABILITY = 0.005
