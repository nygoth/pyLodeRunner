""" Модуль, реализующий персонажей на основе спрайтов игры.
  Персонаж, это перемещающийся по уровню спрайт. Двигает его либо ИИ, либо пользователь вводом с клавиатуры.
"""

# V 2.1
import random

import pygame
from pygame.locals import *
import block
import CC
import level
from glb import *

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


class Character(block.Block):
    """Базовый класс игрового персонажа. Анимированный, перемещается

        Здесь реализовано базовое движение и падение под действием гравитации.
        А также -- проверка столкновений
    """

    def __init__(self, img,
                 position: list = None,
                 subfolder="",
                 sounds: tuple = None,
                 idle_delay=200,
                 fall_delay=100,
                 step=0,
                 animation_step=0):
        self.pos = [0, 0] if position is None else position
        self.oldpos = self.pos
        self.move_direction = K_IDLE
        self.move_state = STATE_STAND
        self.images = dict()
        self.delay = dict()
        self.delay[STATE_STAND] = idle_delay  # Idle and fall states are slower than moving states.
        self.delay[STATE_HANG] = idle_delay  # So they use different counters
        self.delay[STATE_FALL] = fall_delay
        self.current_ticks = 0
        self.step = step
        self.animation_step = animation_step

        (self.step_sound, self.attack_sound, self.die_sound) = ((None, None, None), sounds)[sounds is not None]

        # Load all images as an animation sets
        super().__init__(None, position, subfolder)
        if isinstance(img, dict):

            for state in STATES.keys():
                if state in img:
                    self.images[STATES[state]] = [block.Block(file, position, subfolder) for file in img[state]]

            # Let's duplicate and flip walking animation if absent
            self.__clone_animation__(STATES["walk_left"], STATES["walk_right"], True)

            # Let's duplicate climbing animations if absent
            self.__clone_animation__(STATES["climb_down"], STATES["climb_up"], reverse=True)

            # Несколько переходных форм
            self.__clone_animation__(STATES["walk_hang_right"], STATES["walk_hang_left"], True)
            self.__clone_animation__(STATES["hang"], STATES["walk_hang_left"])
            self.__clone_animation__(STATES["hang"], STATES["walk_hang_right"])
            self.__clone_animation__(STATES["fall"], STATES["fall_hang"])

            attack_list = ("attack_left", "attack_right")
            for state in attack_list:
                if state in img:
                    self.images[state] = block.TemporaryBlock((img[state], None), subfolder=subfolder,
                                                              animation_delay=6)

            if attack_list[0] not in self.images and \
                    attack_list[1] not in self.images:
                self.images[attack_list[0]] = block.TemporaryBlock((None, None), animation_delay=6)

            if attack_list[1] not in self.images:
                self.images[attack_list[1]] = self.images[attack_list[0]].copy(xflip=True)

    def __clone_animation__(self, state1, state2, flip=False, reverse=False):
        f, z = state1, state2
        for i in range(2):
            if f not in self.images and z in self.images:
                if isinstance(self.images[z], list):
                    self.images[f] = [pict.copy(xflip=flip) for pict in reversed(self.images[z])] if reverse \
                        else [pict.copy(xflip=flip) for pict in self.images[z]]
                break
            f, z = state2, state1

    def __set_state__(self):
        self.move_state = (STATE_STAND, STATE_HANG)[level.glLevel[self.pos] in CC.HANG_BLOCKS]

    @staticmethod
    def __in_obstacle__(obstacles: list, pos: list):
        if obstacles is not None:
            obst: Character
            for obst in obstacles:
                if pos == obst.pos:
                    return True
        return False

    def fall(self, obstacles: list = None):
        """ Check for support block under us or staying on block which hangable
            If falling is present -- return true
        """
        self.oldpos = self.pos.copy()
        self.__set_state__()

        tmp_pos = [self.pos[0] + 1, self.pos[1]]
        if check_bounds(tmp_pos):
            if level.glLevel[tmp_pos] not in CC.SUPPORT_BLOCKS and \
                    level.glLevel[self.pos] not in CC.CARRY_BLOCKS and \
                    not self.__in_obstacle__(obstacles, tmp_pos):
                # We are falling down, no other movement
                self.move_state = STATE_FALL
                self.move_direction = K_IDLE
                self.pos[0] += 1
                return True
        return False

    def move(self, disp: tuple, obstacles: list = None):
        self.oldpos = self.pos.copy()

        self.__set_state__()

        if disp[0] != 0 and disp[1] != 0:
            return False  # Character can not move in two directions simultaneously

        tmp_pos = [self.pos[0] + disp[0], self.pos[1] + disp[1]]

        if level.glLevel[tmp_pos] in CC.SOLID_BLOCKS:
            return False  # Impossible movement, block in the way

        if disp[0] == -1 and level.glLevel[self.pos] not in CC.CLIMB_BLOCKS:
            return False  # Impossible to move up

        if obstacles is not None and self.__in_obstacle__(obstacles, tmp_pos):
            return False

        if check_bounds(tmp_pos):
            # Looks like we can move
            # Character movement itself
            self.step_sound is None or self.step_sound.play()
            self.pos = tmp_pos.copy()
            return True

        return False

    def get_image(self, tick):
        if self.move_direction * self.move_state in self.images:
            if isinstance(self.images[self.move_direction * self.move_state], list):
                frames = len(self.images[self.move_direction * self.move_state])
                if self.move_direction == K_IDLE:
                    delay = self.delay[self.move_state]
                    self.current_ticks = 0 if self.current_ticks >= delay - 1 else self.current_ticks + 1
                    current_frame = int(self.current_ticks / (delay / frames))
                else:
                    self.current_ticks = 0
                    current_frame = int(tick / (self.step / frames))

                return self.images[self.move_direction * self.move_state][current_frame].image
            else:
                return self.images[self.move_direction + self.move_state].image
        else:
            return self.image

    def show(self, canvas: pygame.Surface, tick):
        canvas.blit(self.get_image(tick), self.get_screen_pos(self.animation_step, tick))


class Beast(Character):
    """Персонаж, управляемый компьютером
        Здесь реализовано компьютерное управление персонажем.
        В общем случае, он стремится по кратчайшей траектории подойти к игроку.
    """

    def __init__(self, img,
                 position=None,
                 subfolder="",
                 sounds: tuple = None,
                 idle_delay=200,
                 fall_delay=100,
                 step=0,
                 animation_step=0):
        super(Beast, self).__init__(img, position, subfolder, sounds, idle_delay, fall_delay, step, animation_step)
        # Запоминаем позицию рождения для возрождения чудовища в исходном месте при его смерти
        self.spawn_pos = self.pos.copy()
        self.idioticy = 0
        self.range = random.randrange(0, 4)

    # Мы получаем координаты других чудищ (на их место встать нельзя) и игрока (к которому мы стремимся)
    def move(self, player_pos: list, beasts: list = None):
        self.__set_state__()

        if super().fall():
            return True

        # Если игрок выше и левее -- смещения отрицательные
        # Если ниже или правее -- положительные
        disp_y = player_pos[0] - self.pos[0]
        disp_x = player_pos[1] - self.pos[1]

        if disp_x == 0 and disp_y == 0:
            return False

        disp_x = sign(disp_x)
        disp_y = sign(disp_y)
        k_horiz = K_IDLE
        k_vert = K_IDLE
        if self.idioticy == 0:
            self.range = random.randrange(0, 4)
            if disp_y != 0:
                k_vert = I_MOTION[(disp_y, 0)]
            if super().move((disp_y, 0), beasts):
                # Смогли пойти вертикально по направлению к игроку
                self.move_direction = k_vert
                return True

            if disp_x != 0:
                k_horiz = I_MOTION[(0, disp_x)]
            if super().move((0, disp_x), beasts):
                # Смогли пойти горизонтально
                self.move_direction = k_horiz
                return True

        self.idioticy = self.idioticy + 1 if self.idioticy < self.range else 0
        if self.move_direction != K_IDLE:
            if not super().move(MOTION[self.move_direction], beasts):
                self.move_direction = ANTIMOTION[self.move_direction]
                if not super().move(MOTION[self.move_direction]):
                    self.move_direction = K_IDLE
        return True

    def die(self):
        if self.die_sound is not None:
            self.die_sound.play()
        self.pos[0] = self.oldpos[0] = self.spawn_pos[0]
        self.pos[1] = self.oldpos[1] = self.spawn_pos[1]


class Player(Character):
    """Персонаж, контролируемый игроком.
        Здесь происходит проверка клавиатурного ввода и передача команд на движение.
    """

    def __init__(self, img,
                 position=None,
                 subfolder="",
                 sounds: tuple = None,
                 idle_delay=200,
                 fall_delay=100,
                 step=0,
                 animation_step=0):
        super(Player, self).__init__(img, position, subfolder, sounds, idle_delay, fall_delay, step, animation_step)
        # TODO Все временные блоки, ассоциированные с разрушаемыми, должны читаться и создаваться
        # TODO где-то вне. А при атаке игрока должен вставляться именно тот блок, который соответствует
        # TODO разрушаемому.
        cracked = CC.BLOCKS["temporary"][CC.BLOCKS["static"]["Z"][1]]
        self.cracked_block = block.TemporaryBlock(cracked,
                                                  subfolder="Animation", animation_delay=cracked[2] / 100,
                                                  animation_pause=cracked[2])

    def move(self, obstacles: list = None, temporary_items: list = None):
        pressed_keys = pygame.key.get_pressed()

        self.move_direction = K_IDLE

        self.__set_state__()

        if super().fall(obstacles):
            self.move_direction = K_IDLE
            return True

        if self.__in_obstacle__(obstacles, self.pos):
            return False

        attack = {K_q: ("attack_left", -1),
                  K_w: ("attack_right", +1)}
        for key in attack:
            if pressed_keys[key]:
                if 0 <= self.pos[1] + attack[key][1] < CC.LEVEL_WIDTH and \
                        level.glLevel[(self.pos[0], self.pos[1] + attack[key][1])] == '.' and \
                        level.glLevel[(self.pos[0] + 1, self.pos[1] + attack[key][1])] in CC.DESTRUCTABLE_BLOCKS:
                    self.attack_sound is None or self.attack_sound.play()
                    fire = self.images[attack[key][0]].copy()
                    crack = self.cracked_block.copy()
                    fire.pos = [self.pos[0], self.pos[1] + attack[key][1]]
                    crack.pos = [self.pos[0] + 1, self.pos[1] + attack[key][1]]
                    crack.underlay = level.glLevel[crack.pos]

                    level.glLevel[crack.pos] = '.'

                    temporary_items.append(fire)
                    temporary_items.append(crack)

        for key in (K_UP, K_DOWN, K_LEFT, K_RIGHT):
            if pressed_keys[key]:
                if super().move(MOTION[key], obstacles):
                    self.move_direction = key
                    break
        return True
