# LodeRunner clone game
# This project is for studying python programming

# V 3.2
# Game itself

# На предыдущем шаге решена задача плавного перемещения и корректной обработки клавиш
# Приступаем к сбору сокровищ

import os

import pygame
from pygame.locals import *

BLOCK_WIDTH = 45
LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22

STEP = 8  # Шагов анимации между ключевыми кадрами (в которых игра воспринимает управление)
TEMPO = 15  # Количество ключевых кадров в секунду. Темп игры
FPS = TEMPO * STEP
ANIMATION_STEP = BLOCK_WIDTH / STEP  # Смещение объекта в пикселах за один шаг анимации

K_FALL = -1

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
        self.move_direction = 0
        super().__init__(img)

    def fall(self):
        """ Check for support block under us or staying on block which hangable
            If falling is present -- return true
        """
        self.oldpos = self.pos.copy()

        if glCurrentLevel[0][self.pos[0] + 1][self.pos[1]] not in SUPPORT_BLOCKS and \
                glCurrentLevel[0][self.pos[0]][self.pos[1]] not in HANG_BLOCKS:
            # We are falling down, no other movement
            if check_bounds((self.pos[0] + 1, self.pos[1])):
                self.pos[0] += 1
            return True
        return False

    def move(self, disp: tuple):
        self.oldpos = self.pos.copy()

        if disp[0] != 0 and disp[1] != 0:
            return False  # Character can not move in two directions simultaneously

        if glCurrentLevel[0][self.pos[0] + disp[0]][self.pos[1] + disp[1]] in SOLID_BLOCKS:
            return False  # Impossible movement, block in the way

        if disp[0] == -1 and glCurrentLevel[0][self.pos[0]][self.pos[1]] not in CLIMB_BLOCKS:
            return False   # Impossible to move up

        if check_bounds((self.pos[0] + disp[0], self.pos[1] + disp[1])):
            # Looks like we can move
            self.pos[0] += disp[0]
            self.pos[1] += disp[1]

            return True

        return False


class Beast(Character):
    """Персонаж, управляемый компьютером
        Здесь реализовано компьютерное управление персонажем.
        В общем случае, он стремится по кратчайшей траектории подойти к игроку.
    """
    spawn_pos = list()  # Запоминаем позицию рождения для возрождения чудовища в исходном месте при его смерти

    def __init__(self, img, position=None):
        super(Beast, self).__init__(img, position)
        self.spawn_pos = self.pos

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

        self.move_direction = 0

        if super().fall():
            self.move_direction = K_FALL
            return

        for key in (K_UP, K_DOWN, K_LEFT, K_RIGHT):
            if pressed_keys[key] and super().move(motion[key]):
                self.move_direction = key
                break


def get_screen_pos(pos: list, oldpos=None, tick=0):
    if oldpos is None:
        return pos[1] * BLOCK_WIDTH, pos[0] * BLOCK_WIDTH

    disp = ANIMATION_STEP * tick
    disp_x = (pos[1] - oldpos[1]) * disp
    disp_y = (pos[0] - oldpos[0]) * disp
    return oldpos[1] * BLOCK_WIDTH + disp_x, oldpos[0] * BLOCK_WIDTH + disp_y


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
    global glTreasuresCount
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

            for ch in line[0:LEVEL_WIDTH + 1]:
                if ch == 'P':
                    exit_line += ch
                    ch = '.'
                else:
                    exit_line += '.'

                if ch in ANIMATED_BLOCKS:
                    glAnimatedEntities[str(row) + ":" + str(col) + ":" + ch] = \
                        AnimatedBlock(ANIMATED_BLOCKS[ch], [row, col])
                    if ch == '+':
                        glTreasuresCount += 1

                if ch == 'X':
                    glBeasts.append(Beast("beast.png", [row, col]))

                # Персонаж может быть только один, поэтому данный алгоритм вернёт последнее найденное положение
                if ch == 'I':
                    glPlayer.pos = [row, col]
                    glPlayer.oldpos = [row, col]

                static_line += ('.', ch)[ch in MAPPED_BLOCKS]
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

def collect_treasure():
    global glTreasuresCount
    key = str(glPlayer.pos[0]) + ":" + str(glPlayer.pos[1]) + ":+"
    if key in glAnimatedEntities:
        del glAnimatedEntities[key]
        glTreasuresCount -= 1

        # Все сокровища собраны, готовим выход
        if glTreasuresCount == 0:
            row = 0
            for line in glCurrentLevel[1]:
                col = 0
                modifyed = ""
                for ch in line:
                    modifyed += ch if ch != '.' else glCurrentLevel[0][row][col]
                    col += 1
                glCurrentLevel[0][row] = modifyed
                row +=1

            show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)


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
HANG_BLOCKS = ('H', '-', 'P')  # Блоки, на которых можно висеть (т.е. можно стоять на их фоне и не падать)
CLIMB_BLOCKS = ('H', 'P')  # Блоки, по которым можно лезть вверх и вниз
MAPPED_BLOCKS = SOLID_BLOCKS + SUPPORT_BLOCKS + HANG_BLOCKS  # Блоки, которые хранятся в карте проверки

glPlayer = Player("player.png")
glTreasuresCount = 0
glCurrentLevel = load_level("01.lvl")

glStaticCanvas = pygame.Surface(glMainCanvas.get_size())
show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)

glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())

running = True
tick = 0

while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            running = False

    # Erasing old creatures
    glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())

    if tick == 0:
        collect_treasure()
        glPlayer.move()

    # Drawing them in new positions
    # First -- non-moveable level blocks with animation
    for animBlock in glAnimatedEntities.values():
        glMainCanvas.blit(animBlock.image, get_screen_pos(animBlock.pos))

    # Then -- player
    glMainCanvas.blit(glPlayer.image, get_screen_pos(glPlayer.pos, glPlayer.oldpos, tick))

    # And finally -- beasts
    for beast in glBeasts:
        if tick == 0:
            beast.move()
        glMainCanvas.blit(beast.image, get_screen_pos(beast.pos, beast.oldpos, tick))

    tick = tick + 1 if tick < STEP else 0

    pygame.display.update()
    glClock.tick(FPS)

pygame.quit()
