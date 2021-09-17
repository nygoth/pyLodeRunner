# LodeRunner clone game
# This project is for studying python programming

# V 4.1
# Game itself

# После реализации базовой анимации делаем небольшую шлифовку -- рисуем недостающие кадры для анимации
# Персонажа и монстров, рисуем анимацию сокровищ, реализуем анимированные спрайты блоков уровня

# Следующий глобальный шаг -- ИИ монстров

import os
import random

import pygame
from pygame.locals import *

BLOCK_WIDTH = 45
LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22

STEP = 16  # Шагов анимации между ключевыми кадрами (в которых игра воспринимает управление)
TEMPO = 12  # Количество ключевых кадров в секунду. Темп игры
FPS = TEMPO * STEP
ANIMATION_STEP = BLOCK_WIDTH / STEP  # Смещение объекта в пикселах за один шаг анимации

TREASURE_DELAY = 10
TREASURE_PAUSE_LIMIT = (100, 400, 20)

K_IDLE = 1
STATE_FALL = 10
STATE_STAND = 1
STATE_HANG = 100

STATES = {"idle": STATE_STAND * K_IDLE,
          "fall": STATE_FALL * K_IDLE,
          "fall_hang": STATE_HANG * K_DOWN,
          "hang": STATE_HANG * K_IDLE,
          "walk_right": STATE_STAND * K_RIGHT,
          "walk_left": STATE_STAND * K_LEFT,
          "climb_up": STATE_STAND * K_UP,
          "climb_down": STATE_STAND * K_DOWN,
          "walk_hang_right": STATE_HANG * K_RIGHT,
          "walk_hang_left": STATE_HANG * K_LEFT,
          }

PLAYER_FRAMES = {"idle": ("character_maleAdventurer_idle.png",),
                 "fall": ("character_maleAdventurer_fall0.png",
                          "character_maleAdventurer_fall1.png"),
                 "hang": ("character_maleAdventurer_hang_idle.png",),
                 "walk_right": ("character_maleAdventurer_walk0.png",
                                "character_maleAdventurer_walk1.png",
                                "character_maleAdventurer_walk2.png",
                                "character_maleAdventurer_walk3.png",
                                "character_maleAdventurer_walk4.png",
                                "character_maleAdventurer_walk5.png",
                                "character_maleAdventurer_walk6.png",
                                "character_maleAdventurer_walk7.png"),
                 "walk_hang_right": ("character_maleAdventurer_hang0.png",
                                     "character_maleAdventurer_hang1.png",
                                     "character_maleAdventurer_hang2.png",
                                     "character_maleAdventurer_hang3.png",
                                     ),
                 "climb_up": ("character_maleAdventurer_climb0.png",
                              "character_maleAdventurer_climb1.png",
                              "character_maleAdventurer_climb2.png",
                              "character_maleAdventurer_climb3.png",
                              )
                 }

BEAST_FRAMES = {"idle": ("character_zombie_idle.png",),
                "fall": ("character_zombie_fall0.png",
                         "character_zombie_fall1.png",),
                "hang": ("character_zombie_hang.png",),
                "walk_right": ("character_zombie_walk0.png",
                               "character_zombie_walk1.png",
                               "character_zombie_walk2.png",
                               "character_zombie_walk3.png",
                               "character_zombie_walk4.png",
                               "character_zombie_walk5.png",
                               "character_zombie_walk6.png",
                               "character_zombie_walk7.png"),
                "climb_up": ("character_zombie_climb0.png",
                             "character_zombie_climb1.png")
                }

glBeasts = list()
glAnimatedEntities = dict()
glClock = pygame.time.Clock()


class Block(pygame.sprite.Sprite):
    """Спрайт уровня. Неподвижный, с разными характеристиками проницаемости"""

    def __init__(self, img, subfolder=""):
        super().__init__()
        self.base_images_folder = os.path.join(os.path.dirname(__file__), "images", subfolder)

        if img is not None:
            self.image = pygame.image.load(os.path.join(self.base_images_folder, img)).convert_alpha()
        else:
            self.image = pygame.Surface((BLOCK_WIDTH, BLOCK_WIDTH))
            self.image.fill((255, 255, 0))

        self.size = self.image.get_size()
        self.rect = self.image.get_rect(center=(self.size[0] / 2, self.size[1] / 2))

    # TODO Реализовать масштабирование
    def copy(self, xflip=False, yflip=False, scale=1):
        copied = Block(None)

        if xflip or yflip:
            copied.image = pygame.transform.flip(self.image, xflip, yflip)
        else:
            copied.image = self.image.copy()

        return copied


class AnimatedBlock(Block):
    """Анимированный спрайт уровня. Неподвижный"""

    def __init__(self, img, position=None, subfolder="", animation_delay=0, animation_pause=0):
        self.pos = [0, 0] if position is None else position
        self.delay = animation_delay
        self.pause = animation_pause
        self.images = list()
        self.single = False
        self.ticks = 0
        self.current_frame = 0
        self.in_action = True

        super(AnimatedBlock, self).__init__(None, subfolder)
        if isinstance(img, (tuple, list)):
            for file in img:
                self.images.append(Block(file, subfolder))
        else:
            self.single = True

    def get_image(self, tick):
        if not self.single:
            wait_for = self.delay if self.in_action else self.pause

            if self.ticks < wait_for:
                self.ticks += 1
            else:
                self.ticks = 0
                self.current_frame = self.current_frame + 1 if self.in_action else self.current_frame
                if self.current_frame >= len(self.images):
                    self.current_frame = 0
                self.in_action = not self.in_action if self.current_frame == 0 else self.in_action

            return self.images[self.current_frame].image
        else:
            return self.image


class Character(Block):
    """Базовый класс игрового персонажа. Анимированный, перемещается

        Здесь реализовано базовое движение и падение под действием гравитации.
        А также -- проверка столкновений
    """

    def __init__(self, img, position=None, subfolder=""):
        self.pos = [0, 0] if position is None else position
        self.oldpos = self.pos
        self.move_direction = K_IDLE
        self.move_state = STATE_STAND
        self.images = dict()

        # Load all images as an animation sets
        super().__init__(None, subfolder)
        if isinstance(img, dict):

            for state in STATES.keys():
                if state in img:
                    self.images[STATES[state]] = list()
                    for file in img[state]:
                        self.images[STATES[state]].append(Block(file, subfolder))

            # Let's duplicate and flip walking animation if absent
            self.__clone_animation__(STATES["walk_left"], STATES["walk_right"], True)

            # Let's duplicate climbing animations if absent
            self.__clone_animation__(STATES["climb_down"], STATES["climb_up"])

            # Несколько переходных форм
            self.__clone_animation__(STATES["walk_hang_right"], STATES["walk_hang_left"], True)
            self.__clone_animation__(STATES["hang"], STATES["walk_hang_left"])
            self.__clone_animation__(STATES["hang"], STATES["walk_hang_right"])
            self.__clone_animation__(STATES["fall"], STATES["fall_hang"])

    def __clone_animation__(self, state1, state2, flip=False):
        if state1 not in self.images and state2 in self.images:
            self.images[state1] = list()
            for pict in self.images[state2]:
                self.images[state1].append(pict.copy(xflip=flip))
        if state1 in self.images and state2 not in self.images:
            self.images[state2] = list()
            for pict in self.images[state1]:
                self.images[state2].append(pict.copy(xflip=flip))

    def __set_state__(self):
        self.move_state = STATE_HANG if glCurrentLevel[0][self.pos[0]][self.pos[1]] in HANG_BLOCKS else STATE_STAND

    def fall(self):
        """ Check for support block under us or staying on block which hangable
            If falling is present -- return true
        """
        self.oldpos = self.pos.copy()
        self.__set_state__()

        if glCurrentLevel[0][self.pos[0] + 1][self.pos[1]] not in SUPPORT_BLOCKS and \
                glCurrentLevel[0][self.pos[0]][self.pos[1]] not in CARRY_BLOCKS:
            # We are falling down, no other movement
            if check_bounds((self.pos[0] + 1, self.pos[1])):
                self.move_state = STATE_FALL
                self.pos[0] += 1
            return True
        return False

    def move(self, disp: tuple):
        self.oldpos = self.pos.copy()

        self.__set_state__()

        if disp[0] != 0 and disp[1] != 0:
            return False  # Character can not move in two directions simultaneously

        if glCurrentLevel[0][self.pos[0] + disp[0]][self.pos[1] + disp[1]] in SOLID_BLOCKS:
            return False  # Impossible movement, block in the way

        if disp[0] == -1 and glCurrentLevel[0][self.pos[0]][self.pos[1]] not in CLIMB_BLOCKS:
            return False  # Impossible to move up

        if check_bounds((self.pos[0] + disp[0], self.pos[1] + disp[1])):
            # Looks like we can move
            self.pos[0] += disp[0]
            self.pos[1] += disp[1]

            return True

        return False

    def get_image(self, tick):
        if self.move_direction * self.move_state in self.images:
            if isinstance(self.images[self.move_direction * self.move_state], list):
                frames = len(self.images[self.move_direction * self.move_state])
                current_frame = int(tick / (STEP / frames))

                return self.images[self.move_direction * self.move_state][current_frame].image
            else:
                return self.images[self.move_direction + self.move_state].image
        else:
            return self.image


class Beast(Character):
    """Персонаж, управляемый компьютером
        Здесь реализовано компьютерное управление персонажем.
        В общем случае, он стремится по кратчайшей траектории подойти к игроку.
    """

    def __init__(self, img, position=None, subfolder=""):
        super(Beast, self).__init__(img, position, subfolder)
        # Запоминаем позицию рождения для возрождения чудовища в исходном месте при его смерти
        self.spawn_pos = self.pos

    def move(self):
        if super().fall():
            return


class Player(Character):
    """Персонаж, контролируемый игроком.
        Здесь происходит проверка клавиатурного ввода и передача команд на движение.
    """

    def __init__(self, img, position=None, subfolder=""):
        super(Player, self).__init__(img, position, subfolder)

    def move(self):
        pressed_keys = pygame.key.get_pressed()
        motion = {K_LEFT: (0, -1),
                  K_RIGHT: (0, 1),
                  K_UP: (-1, 0),
                  K_DOWN: (1, 0)
                  }

        self.move_direction = K_IDLE

        self.__set_state__()

        if super().fall():
            self.move_direction = K_IDLE
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
                        AnimatedBlock(ANIMATED_BLOCKS[ch][1], [row, col], subfolder=ANIMATED_BLOCKS[ch][0],
                                      animation_delay=TREASURE_DELAY,
                                      animation_pause=random.randrange(TREASURE_PAUSE_LIMIT[0],
                                                                       TREASURE_PAUSE_LIMIT[1],
                                                                       TREASURE_PAUSE_LIMIT[2]))
                    if ch == '+':
                        glTreasuresCount += 1

                if ch == 'X':
                    glBeasts.append(Beast(BEAST_FRAMES, [row, col], subfolder="Beast"))

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
                modified = ""
                for ch in line:
                    modified += ch if ch != '.' else glCurrentLevel[0][row][col]
                    col += 1
                glCurrentLevel[0][row] = modified
                row += 1

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
ANIMATED_BLOCKS = {'+': ("Treasure", ("treasure0.png",
                                      "treasure1.png",
                                      "treasure2.png",
                                      "treasure3.png",
                                      "treasure4.png",
                                      "treasure5.png",
                                      "treasure6.png",
                                      "treasure7.png",)), }

SOLID_BLOCKS = ('Z', 'O')  # Непроницаемые блоки
SUPPORT_BLOCKS = ('Z', 'O', 'H', 'P')  # Блоки, на которых можно стоять не падая
CARRY_BLOCKS = ('H', '-', 'P')  # Блоки, можно стоять на их фоне и не падать
HANG_BLOCKS = ('-',)  # Блоки, на которых можно висеть
CLIMB_BLOCKS = ('H', 'P')  # Блоки, по которым можно лезть вверх и вниз
MAPPED_BLOCKS = SOLID_BLOCKS + SUPPORT_BLOCKS + CARRY_BLOCKS  # Блоки, которые хранятся в карте проверки

glPlayer = Player(PLAYER_FRAMES, subfolder="Player")

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
    # First -- non-movable level blocks with animation
    for animBlock in glAnimatedEntities.values():
        glMainCanvas.blit(animBlock.get_image(tick), get_screen_pos(animBlock.pos))

    # Then -- player
    glMainCanvas.blit(glPlayer.get_image(tick), get_screen_pos(glPlayer.pos, glPlayer.oldpos, tick))

    # And finally -- beasts
    for beast in glBeasts:
        if tick == 0:
            beast.move()
        glMainCanvas.blit(beast.get_image(tick), get_screen_pos(beast.pos, beast.oldpos, tick))

    tick = tick + 1 if tick < STEP - 1 else 0

    pygame.display.update()
    glClock.tick(FPS)

pygame.quit()
