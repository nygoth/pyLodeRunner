# Модуль, реализующий персонажей на основе спрайтов игры.
# Персонаж, это перемещающийся по уровню спрайт. Двигает его либо ИИ, либо пользователь вводом с клавиатуры

# V 1.0
import random

import pygame
from pygame.locals import *
import block

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

MOTION = {K_LEFT: (0, -1),
          K_RIGHT: (0, 1),
          K_UP: (-1, 0),
          K_DOWN: (1, 0)
          }

ANTIMOTION = {K_LEFT: K_RIGHT,
              K_RIGHT: K_LEFT,
              K_UP: K_DOWN,
              K_DOWN: K_UP,
              }

# Обратный словарь к MOTION. Нужен для поиска команды по известному шагу
I_MOTION = dict(zip(MOTION.values(), MOTION.keys()))

SOLID_BLOCKS = ('Z', 'O')  # Непроницаемые блоки
SUPPORT_BLOCKS = ('Z', 'O', 'H', 'P')  # Блоки, на которых можно стоять не падая
CARRY_BLOCKS = ('H', '-', 'P')  # Блоки, можно стоять на их фоне и не падать
HANG_BLOCKS = ('-',)  # Блоки, на которых можно висеть
CLIMB_BLOCKS = ('H', 'P')  # Блоки, по которым можно лезть вверх и вниз
MAPPED_BLOCKS = SOLID_BLOCKS + SUPPORT_BLOCKS + CARRY_BLOCKS  # Блоки, которые хранятся в карте проверки

LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22

glCurrentLevel = list()


class Character(block.Block):
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
                        self.images[STATES[state]].append(block.Block(file, subfolder))

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

    def __in_obstacle__(self, obstacles: list, pos: tuple):
        for obst in obstacles:
            if pos[0] == obst.pos[0] and pos[1] == obst.pos[1]:
                return True
        return False

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
                self.move_direction = K_IDLE
                self.pos[0] += 1
            return True
        return False

    def move(self, disp: tuple, obstacles=None):
        self.oldpos = self.pos.copy()

        self.__set_state__()

        if disp[0] != 0 and disp[1] != 0:
            return False  # Character can not move in two directions simultaneously

        if glCurrentLevel[0][self.pos[0] + disp[0]][self.pos[1] + disp[1]] in SOLID_BLOCKS:
            return False  # Impossible movement, block in the way

        if disp[0] == -1 and glCurrentLevel[0][self.pos[0]][self.pos[1]] not in CLIMB_BLOCKS:
            return False  # Impossible to move up

        if obstacles is not None and self.__in_obstacle__(obstacles, (self.pos[0] + disp[0], self.pos[1] + disp[1])):
            return False

        if check_bounds((self.pos[0] + disp[0], self.pos[1] + disp[1])):
            # Looks like we can move
            self.pos[0] += disp[0]
            self.pos[1] += disp[1]

            return True

        return False

    def get_image(self, tick, step):
        if self.move_direction * self.move_state in self.images:
            if isinstance(self.images[self.move_direction * self.move_state], list):
                frames = len(self.images[self.move_direction * self.move_state])
                current_frame = int(tick / (step / frames))

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
        self.idioticy = 0
        self.range = random.randrange(0,4)

    # Мы получаем координаты других чудищ (на их место встать нельзя) и игрока (к которому мы стремимся)
    def move(self, player_pos: list, beasts=None):
        self.__set_state__()

        if super().fall():
            return

        # Если игрок выше и левее -- смещения отрицательные
        # Если ниже или правее -- положительные
        disp_y = player_pos[0] - self.pos[0]
        disp_x = player_pos[1] - self.pos[1]

        res = False
        disp_x = sign(disp_x)
        disp_y = sign(disp_y)
        k_horiz = K_IDLE
        k_vert = K_IDLE
        if self.idioticy == 0:
            self.range = random.randrange(0, 4)
            if disp_y != 0:
                # if disp_x == 0 or glCurrentLevel[0][self.pos[0] + 1][self.pos[1]] in SUPPORT_BLOCKS + CARRY_BLOCKS:
                k_vert = I_MOTION[(disp_y, 0)]
                res = super().move((disp_y, 0), beasts)
            # Смогли пойти вертикально по направлению к игроку
            if res:
                self.move_direction = k_vert
                return

            if disp_x != 0:
                k_horiz = I_MOTION[(0, disp_x)]
                res = super().move((0, disp_x), beasts)
            # Смогли пойти горизонтально
            if res:
                self.move_direction = k_horiz
                return

        self.idioticy = self.idioticy + 1 if self.idioticy < self.range else 0
        if self.move_direction != K_IDLE:
            if not super().move(MOTION[self.move_direction], beasts):
                self.move_direction = ANTIMOTION[self.move_direction]
                if not super().move(MOTION[self.move_direction]):
                    self.move_direction = K_IDLE


class Player(Character):
    """Персонаж, контролируемый игроком.
        Здесь происходит проверка клавиатурного ввода и передача команд на движение.
    """

    def __init__(self, img, position=None, subfolder=""):
        super(Player, self).__init__(img, position, subfolder)

    def move(self, obstacles=None):
        pressed_keys = pygame.key.get_pressed()

        self.move_direction = K_IDLE

        self.__set_state__()

        if super().fall():
            self.move_direction = K_IDLE
            return

        for key in (K_UP, K_DOWN, K_LEFT, K_RIGHT):
            if pressed_keys[key] and super().move(MOTION[key], obstacles):
                self.move_direction = key
                break


def check_bounds(pos: tuple):
    """Return true, if provided position within screen bounds, else false"""
    if pos[1] < 0 or pos[1] >= LEVEL_WIDTH or \
            pos[0] < 0 or pos[0] >= LEVEL_HEIGHT:
        return False
    return True


def sign(x):
    return -1 if x < 0 else 1 if x > 0 else 0
