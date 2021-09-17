# LodeRunner clone game
# This project is for studying python programming

# V 2.2
# Game itself

# Итак, уровень загружен, разнесён на различные структуры и отображается.
# Займёмся базовой игровой механикой -- перемещением игрока по уровню и сбором сокровищ
# Пока никаких монстров
# Однако, в классе Character уже должно быть реализовано действие гравитации и контроль
# пространства. Т.е. персонажи не должны падать ниже пола и должны виснуть на перекладине

# Но первое, что я сделал -- изменил логику хранения слоя анимированных спрайтов уровня
# Теперь это словарь спрайтов типа AnimatedBlock. Так намного проще всё это отрисовывать.
# Ключи -- строка "x:y:t" (t - символ из карты уровня, обозначающий блок) -- координаты анимированного спрайта.
# Он используется для проверки столкновения со спрайтом и, например, подбора сокровища игроком

import os

import pygame
from pygame.locals import *

BLOCK_WIDTH = 45
LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22

FPS = 25

glBeasts = list()
glAnimatedEntities = dict()
glClock = pygame.time.Clock()


class Block(pygame.sprite.Sprite):
    """Спрайт уровня. Неподвижный, с разными характеристиками проницаемости"""

    def __init__(self, img):
        super().__init__()
        base_images_folder = os.path.join(os.path.dirname(__file__), "images")

        if img is not None:
            self.image = pygame.image.load(os.path.join(base_images_folder, img)).convert_alpha()
            self.size = self.image.get_size()
            self.rect = self.image.get_rect(center=(self.size[0] / 2, self.size[1] / 2))


class AnimatedBlock(Block):
    """Анимированный спрайт уровня. Неподвижный"""
    pos = list()

    def __init__(self, img, position=None):
        # TODO Change this to pass None and provide code for loading an image set (img must be a tuple in this case)
        super(AnimatedBlock, self).__init__(None if img is list else img)
        self.pos = [0, 0] if position is None else position


class Character(Block):
    """Базовый класс игрового персонажа. Анимированный, перемещается"""
    pos = list()

    def __init__(self, img, position=None):
        self.pos = [0, 0] if position is None else position
        super().__init__(img)


def init_screen(width, height):
    pygame.init()

    scr = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Lode Runner")
    return scr


def load_level(filename):
    static_layer = list()  # Layer for static tiles
    exit_layer = list()  # Layer for exit ladder

    glBeasts.clear()
    glAnimatedEntities.clear()

    with open(filename, 'r') as lvl_stream:
        row = 0

        for line in lvl_stream:
            static_line = ""
            exit_line = ""

            col = 0

            for ch in line[0:LEVEL_WIDTH]:
                if ch == 'P':
                    exit_line += ch
                    ch = ' '
                else:
                    exit_line += ' '

                if ch in ANIMATED_BLOCKS:
                    glAnimatedEntities[str(col) + ":" + str(row) + ":" + ch] = \
                        AnimatedBlock(ANIMATED_BLOCKS[ch], [col * BLOCK_WIDTH, row * BLOCK_WIDTH])

                if ch == 'X':
                    glBeasts.append(Character("beast.png", [col * BLOCK_WIDTH, row * BLOCK_WIDTH]))

                # Персонаж может быть только один, поэтому данный алгоритм вернёт последнее найденное положение
                if ch == 'I':
                    glPlayer.pos = [col * BLOCK_WIDTH, row * BLOCK_WIDTH]

                static_line += ch if ch in STATIC_BLOCKS else ' '
                col += 1

            static_layer.append(static_line)
            exit_layer.append(exit_line)

            row += 1

    # Return tuple of layer in defined order
    return static_layer, exit_layer


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


glMainCanvas = init_screen(BLOCK_WIDTH * LEVEL_WIDTH, BLOCK_WIDTH * LEVEL_HEIGHT)

STATIC_BLOCKS = {'Z': Block("block.png"),
                 'H': Block("ladder.png"),
                 'O': Block("solid.png"),
                 '-': Block("bar.png"),
                 'P': Block("exit_ladder.png"),
                 }
ANIMATED_BLOCKS = {'+': "treasure.png", }

glPlayer = Character("player.png")

glCurrentLevel = load_level("01.lvl")

glStaticCanvas = pygame.Surface(glMainCanvas.get_size())
show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)

glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    for beast in glBeasts:
        glMainCanvas.blit(beast.image, beast.pos)
    for animBlock in glAnimatedEntities.values():
        glMainCanvas.blit(animBlock.image, animBlock.pos)
    glMainCanvas.blit(glPlayer.image, glPlayer.pos)

    pygame.display.update()
    glClock.tick(FPS)

pygame.quit()
