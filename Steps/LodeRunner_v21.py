# LodeRunner clone game
# This project is for studying python programming

# V 2.1
# Load level file and show it with sprites in window

# После решения базовой проблемы -- вывода уровня на экран,
# займёмся мелочами. Поправим в коде то, чего я не знал до сих пор о
# python и pygame

# Первое -- немного исправим имеющийся код, чтобы он был более логичным и лаконичным
# Второе -- разобъём загружаемый уровень на четыре составляющие:
#   * неизменяемые тайлы -- фон
#   * анимированные тайлы (пока реализовывать не будем, на будущее) -- лава, ещё что-нибудь такое
#   * сокровища -- то, что собирается, а, следовательно, уменьшается количество элементов для отрисовки
#   * персонажи -- всё, что двигается само или пользователем.
# Возможно, правильным было бы хранить сокровища в анимированных тайлах (они могут быть анимированными)
# и просто удалять их из этого списка по мере сборки
# Третье    -- нужен счётчик сокровищ на уровне. Устанавливается при загрузке оного
# Четвёртое -- лестница-выход не должна отображаться вообще. Она рисуется и учитывается только тогда, когда
# все сокровища собраны. Поэтому при загрузке её надо вынести в отдельный список символов, а в карте экрана
# заменить эти места пробелом.

import os

import pygame
from pygame.locals import *

BLOCK_WIDTH = 45
LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22

FPS = 25

glBeasts = list()
glTreasuresCount = 0
glClock = pygame.time.Clock()


class Block(pygame.sprite.Sprite):
    """Спрайт уровня. Неподвижный, с разными характеристиками проницаемости"""
    def __init__(self, img):
        super().__init__()
        base_images_folder = os.path.join(os.path.dirname(__file__), "images")

        self.image = pygame.image.load(os.path.join(base_images_folder, img)).convert_alpha()
        self.size = self.image.get_size()
        self.rect = self.image.get_rect(center=(self.size[0] / 2, self.size[1] / 2))


class Character(Block):
    """Базовый класс игрового персонажа. Анимированный, перемещается"""
    pos = list()

    def __init__(self, img, position=[0, 0]):
        self.pos = position
        super().__init__(img)


def init_screen(width, height):
    pygame.init()

    canvas = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Lode Runner")
    return canvas


def load_level(filename):
    global glTreasuresCount

    static_layer = list()       # Layer for static tiles
    animated_layer = list()     # Layer for animated tiles and treasures
    exit_layer = list()         # Layer for exit ladder
    beasts = list()             # List of all beasts (NPC)

    with open(filename, 'r') as lvl_stream:
        row = 0

        for line in lvl_stream:
            static_line = ""
            exit_line = ""
            animated_line = ""

            col = 0

            for ch in line[0:LEVEL_WIDTH]:
                if ch == 'P':
                    exit_line += ch
                    ch = ' '
                else:
                    exit_line += ' '

                if ch == '+':
                    glTreasuresCount += 1
                    animated_line += ch
                    ch = ' '
                else:
                    animated_line += ' '

                if ch == 'X':
                    ch = ' '
                    glBeasts.append(Character("beast.png", [col, row]))

                # Персонаж может быть только один, поэтому данный алгоритм вернёт последнее найденное положение
                if ch == 'I':
                    glPlayer.pos = [col, row]
                    ch = ' '

                static_line += ch
                col += BLOCK_WIDTH

            static_layer.append(static_line)
            animated_layer.append(animated_line)
            exit_layer.append(exit_line)

            row += BLOCK_WIDTH

    # Return tuple of layer in defined order
    return (static_layer, animated_layer, exit_layer)


def show_layer(canvas: pygame.Surface, level: list, sprites: dict) -> None:
    y = 0

    for row in level:
        x = 0
        for block in row:
            curBlock = sprites.get(block)

            if curBlock != None:
                canvas.blit(curBlock.image, curBlock.image.get_rect(topleft=(x * BLOCK_WIDTH, y * BLOCK_WIDTH)))
            x += 1
        y += 1
    pass

# =========
# Main body
# =========


canvas = init_screen(BLOCK_WIDTH * LEVEL_WIDTH, BLOCK_WIDTH * LEVEL_HEIGHT)
level_blocks = {'Z': Block("block.png"),
                'H': Block("ladder.png"),
                'O': Block("solid.png"),
                '-': Block("bar.png"),
                'P': Block("exit_ladder.png"),
                '+': Block("treasure.png")
                }

glPlayer = Character("player.png")

glCurrentLevel = load_level("01.lvl")

glStaticCanvas = pygame.Surface(canvas.get_size())
show_layer(glStaticCanvas, glCurrentLevel[0], level_blocks)

canvas.blit(glStaticCanvas, glStaticCanvas.get_rect())
show_layer(canvas, glCurrentLevel[1], level_blocks)
show_layer(canvas, glCurrentLevel[2], level_blocks)

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    for beast in glBeasts:
        canvas.blit(beast.image,beast.pos)
    canvas.blit(glPlayer.image, glPlayer.pos)

    pygame.display.update()
    glClock.tick(FPS)

pygame.quit()
