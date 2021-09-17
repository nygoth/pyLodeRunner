# LodeRunner clone game
# This project is for studying python programming

# V 3.0
# Game itself

# Итак, уровень загружен, разнесён на различные структуры и отображается.
# Займёмся базовой игровой механикой -- перемещением игрока по уровню и сбором сокровищ
# Пока никаких монстров
# Однако, в классе Character уже должно быть реализовано действие гравитации и контроль
# пространства. Т.е. персонажи не должны падать ниже пола и должны виснуть на перекладине

import os

import pygame
from pygame.locals import *

BLOCK_WIDTH = 45
LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22

FPS = 10

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
    """Базовый класс игрового персонажа. Анимированный, перемещается

        Здесь реализовано базовое движение и падение под действием гравитации.
        А также -- проверка столкновений
    """
    pos = list()
    oldpos = list()

    def __init__(self, img, position=None):
        self.pos = [0, 0] if position is None else position
        self.oldpos = self.pos
        super().__init__(img)

    def fall(self):
        """ Check for support block under us or staying on block which hangable
            If falling is present -- return true
        """
        if glCurrentLevel[0][self.pos[0] + 1][self.pos[1]] not in SUPPORT_BLOCKS and \
                glCurrentLevel[0][self.pos[0]][self.pos[1]] not in HANG_BLOCKS:
            # We are falling down, no other movement
            if check_bounds((self.pos[0] + 1, self.pos[1])):
                self.oldpos = self.pos
                self.pos[0] += 1
            return True
        return False

    def move(self, disp: tuple):
        if disp[0] != 0 and disp[1] != 0:
            return  # Character can not move in two directions simultaneously

        if glCurrentLevel[0][self.pos[0] + disp[0]][self.pos[1] + disp[1]] in SOLID_BLOCKS:
            return  # Impossible movement, block in the way

        if check_bounds((self.pos[0] + disp[0], self.pos[1] + disp[1])):
            # Looks like we can move
            self.oldpos = self.pos
            self.pos[0] += disp[0]
            self.pos[1] += disp[1]


class Beast(Character):
    """Персонаж, управляемый компьютером
        Здесь реализовано компьютерное управление персонажем.
        В общем случае, он стремится по кратчайшей траектории подойти к игроку.
    """

    def __init__(self, img, position=None):
        super(Beast, self).__init__(img, position)

    def move(self):
        if super().fall():
            return


class Player(Character):
    """Персонаж, контролируемый игроком.
        Здесь происходит проверка клавиатурного ввода и передача команд на движение.
    """

    def __init__(self, img, position=None):
        super(Player, self).__init__(img, position)

    def move(self):
        pressed_keys = pygame.key.get_pressed()
        motion = {K_LEFT: (0, -1),
                  K_RIGHT: (0, 1),
                  K_UP: (-1, 0),
                  K_DOWN: (1, 0)
                  }

        if super().fall():
            return

        for key in (K_LEFT, K_RIGHT, K_UP, K_DOWN):
            super().move(motion[key]) if pressed_keys[key] else None


def get_screen_pos(pos: list):
    return pos[1] * BLOCK_WIDTH, pos[0] * BLOCK_WIDTH


def check_bounds(pos: tuple):
    """Return true, if provided position within screen bounds, else false"""
    if pos[1] < 0 or pos[1] >= LEVEL_WIDTH or \
            pos[0] < 0 or pos[0] >= LEVEL_HEIGHT:
        return False
    return True


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

            for ch in line[0:LEVEL_WIDTH+1]:
                if ch == 'P':
                    exit_line += ch
                    ch = '_'
                else:
                    exit_line += '_'

                if ch in ANIMATED_BLOCKS:
                    glAnimatedEntities[str(row) + ":" + str(col) + ":" + ch] = \
                        AnimatedBlock(ANIMATED_BLOCKS[ch], [row, col])

                if ch == 'X':
                    glBeasts.append(Beast("beast.png", [row, col]))

                # Персонаж может быть только один, поэтому данный алгоритм вернёт последнее найденное положение
                if ch == 'I':
                    glPlayer.pos = [row, col]

                static_line += ('_', ch)[ch in STATIC_BLOCKS or \
                                         ch in SOLID_BLOCKS or \
                                         ch in SUPPORT_BLOCKS or \
                                         ch in HANG_BLOCKS]
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

            if curBlock is not None:
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
SOLID_BLOCKS = ('Z', 'O')  # Непроницаемые блоки
SUPPORT_BLOCKS = ('Z', 'O', 'H', 'P')  # Блоки, на которых можно стоять не падая
HANG_BLOCKS = ('H', '-')  # Блоки, на которых можно висеть (т.е. можно стоять на их фоне и не падать)

glPlayer = Player("player.png")

glCurrentLevel = load_level("01.lvl")

glStaticCanvas = pygame.Surface(glMainCanvas.get_size())
show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)

glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())

running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # Erasing old creatures
    glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())

    glPlayer.move()

    # Drawing new in new positions
    for beast in glBeasts:
        beast.move()
        glMainCanvas.blit(beast.image, get_screen_pos(beast.pos))
    for animBlock in glAnimatedEntities.values():
        glMainCanvas.blit(animBlock.image, get_screen_pos(animBlock.pos))
    glMainCanvas.blit(glPlayer.image, get_screen_pos(glPlayer.pos))

    pygame.display.update()
    glClock.tick(FPS)

pygame.quit()
