# LodeRunner clone game
# This project is for studying python programming

# V 7.6
# Полностью реализованная игра. Осталось немного вычистить код, и можно делать релиз.

# В данном проекте есть один серьёзный недочёт дизайна -- сейчас при загрузке уровня
# все анимированные спрайты создаются и загружаются заново. На каждый новый уровень. Причём. на каждый блок своя копия.
# Это неоптимально. Картинки анимации, например, достаточно загрузить один раз за всю игру
# по одному экземпляру на каждый тип анимированного спрайта.
# Для этого можно ввсти промежуточный класс между Block и всеми наследниками -- что-то типа ImageArray
# Или перед Block, а последний сделать вырожденным случаем.


from os import path, walk
import random
import sys
import json

import pygame
from pygame.locals import *

import block
import character
import configparser

# Объявление глобальных констант и переменных
SETTINGS_FILE = path.join(path.dirname(__file__), "settings.ini")

# Статусы завершения игры
GAME_OVER_COMPLETE = 0  # Уровень пройден
GAME_OVER_EATEN = 1  # Игрока съели
GAME_OVER_STUCK = 2  # Игрок застрял в разрушенном блоке
GAME_OVER_KILLED = 3  # Игрок убит в смертельном блоке
GAME_OVER_USER_END = 100  # Пользователь хочет закрыть программу

# What next after level end (fail or win)
ACTION_QUIT = 0  # Exit program
ACTION_NEXT = 1  # Proceed to next level
ACTION_RESTART = 2  # Restart current level

glClock = pygame.time.Clock()


def load_sound(filename):
    """Загрузка звукового эффекта. Все эффекты лежат в каталоге Sounds"""
    if filename is None:
        return None
    snd = pygame.mixer.Sound(path.join(path.dirname(__file__), "Sounds", filename))
    snd.set_volume(0.5)
    return snd


def get_screen_pos(pos: list, step=0.0, oldpos: list = None, tick=0):
    """Переводит старые и новые координаты в знакоместах в экранные координаты относительно текущего игрового тика"""
    if oldpos is None:
        return pos[1] * BLOCK_WIDTH, pos[0] * BLOCK_WIDTH

    disp = step * tick
    disp_x = (pos[1] - oldpos[1]) * disp
    disp_y = (pos[0] - oldpos[0]) * disp
    return oldpos[1] * BLOCK_WIDTH + disp_x, oldpos[0] * BLOCK_WIDTH + disp_y


def init_screen(width, height):
    """Инициализирует экран, создаёт игровое окно"""
    pygame.init()

    scr = pygame.display.set_mode((width, height))
    pygame.display.set_caption("pyLode Runner")
    return scr


def load_level(filename):
    """Загружает игровой уровень. Создаёт всю необходимую структуру и динамические объекты"""
    global glTreasuresCount
    static_layer = list()  # Layer for static tiles
    exit_layer = list()  # Layer for exit ladder

    glBeasts.clear()
    glAnimatedEntities.clear()

    # Уровень -- текстовый файл с буквами и символами, соответствующими структуре уровня
    with open(filename, 'r') as lvl_stream:
        row = 0

        # Цикл по строкам файла
        for line in lvl_stream:
            static_line = list()
            exit_line = list()

            col = 0

            # Цикл по отдельным символам строки. Добавляем один символ, чтобы не писать в коде лишних проверок
            # на выход за границы массива
            for ch in line[0:LEVEL_WIDTH + 1]:
                if ch in character.EXIT_BLOCKS:
                    exit_line.append(ch)
                    ch = '.'
                else:
                    exit_line.append('.')

                if ch in ANIMATED_BLOCKS:
                    glAnimatedEntities[str(row) + ":" + str(col) + ":" + ch] = \
                        block.AnimatedBlock(ANIMATED_BLOCKS[ch][1], [row, col],
                                            subfolder=ANIMATED_BLOCKS[ch][0],
                                            animation_delay=random.randrange(ANIMATED_BLOCKS[ch][2][0],
                                                                             ANIMATED_BLOCKS[ch][2][1],
                                                                             ANIMATED_BLOCKS[ch][2][2]) \
                                                if isinstance(ANIMATED_BLOCKS[ch][2], (list, tuple)) \
                                                else ANIMATED_BLOCKS[ch][2],
                                            animation_pause=random.randrange(ANIMATED_BLOCKS[ch][3][0],
                                                                             ANIMATED_BLOCKS[ch][3][1],
                                                                             ANIMATED_BLOCKS[ch][3][2]) \
                                                if isinstance(ANIMATED_BLOCKS[ch][3], (list, tuple)) \
                                                else ANIMATED_BLOCKS[ch][3],
                                            hit_sound=load_sound(ANIMATED_BLOCKS[ch][4]))
                    if ch in character.TREASURE_BLOCKS:
                        glTreasuresCount += 1

                if ch in character.BEAST_BLOCKS:
                    glBeasts.append(character.Beast(BEAST_FRAMES[ch], [row, col], subfolder=BEAST_FRAMES[ch]["folder"],
                                                    sounds=(None, None, load_sound(BEAST_FRAMES[ch]["dieSound"])),
                                                    idle_delay=BEAST_FRAMES[ch]["idle_delay"],
                                                    fall_delay=BEAST_FRAMES[ch]["fall_delay"]))

                # Персонаж может быть только один, поэтому данный алгоритм вернёт последнее найденное положение
                if ch == 'I':
                    glPlayer.pos = [row, col]
                    glPlayer.oldpos = [row, col]

                static_line.append(('.', ch)[ch in character.MAPPED_BLOCKS])
                col += 1

            static_layer.append(static_line)
            exit_layer.append(exit_line)

            row += 1

    # Additional hidden line to avoid 'index out of range' errors
    static_layer.append(static_line)
    # Return tuple of layer in defined order
    return static_layer, exit_layer


def show_layer(canvas: pygame.Surface, level: list, sprites: dict) -> None:
    """Процедура для рисования статичной части уровня на экране"""
    y = 0

    for row in level:
        x = 0
        for block in row:
            # Используем метод get. Он не выдаёт ошибок, если индекс отсутствует, а возвращает None, что удобнее
            curBlock = sprites.get(block)

            if curBlock is not None:
                canvas.blit(curBlock.image, curBlock.image.get_rect(topleft=(x * BLOCK_WIDTH, y * BLOCK_WIDTH)))
            x += 1
        y += 1


def collect_treasures(pos):
    """Проверка на подбор сокровища игроком. Если все сокровища собраны, добавляем выход с уровня"""
    global glTreasuresCount
    for ch in character.TREASURE_BLOCKS:
        key = str(pos[0]) + ":" + str(pos[1]) + ":" + ch
        if key in glAnimatedEntities:
            if glAnimatedEntities[key].hit_sound is not None:
                glAnimatedEntities[key].hit_sound.play()
            del glAnimatedEntities[key]
            glTreasuresCount -= 1

            # Все сокровища собраны, готовим выход
            if glTreasuresCount <= 0:
                exitAppears_sound.play()
                row = 0
                for line in glCurrentLevel[1]:
                    col = 0
                    for ch in line:
                        glCurrentLevel[0][row][col] = ch if ch != '.' else glCurrentLevel[0][row][col]
                        col += 1
                    row += 1

                show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)


def die_beast(beast):
    if beast.die_sound is not None:
        beast.die_sound.play()
    beast.pos[0] = beast.oldpos[0] = beast.spawn_pos[0]
    beast.pos[1] = beast.oldpos[1] = beast.spawn_pos[1]


def respawn_beasts(block: block.Block):
    """Проверяем, не зажало ли игрока или монстра зарастающей стеной"""
    if glPlayer.pos[0] == block.pos[0] and glPlayer.pos[1] == block.pos[1]:
        return False
    for beast in glBeasts:
        if beast.pos[0] == block.pos[0] and beast.pos[1] == block.pos[1]:
            die_beast(beast)
    return True


def game_over(reason: int):
    """Действия, которые нужно выполнить при завершении игры (по любой причине)"""
    buttons = [btQuit, ]

    # Если игрок уровень проиграл, то нужно проиграть соответствующий звук
    # Кроме того, на экране заставки нужно добавить кнопку Restart
    if reason != GAME_OVER_COMPLETE:
        if glPlayer.die_sound is not None:
            glPlayer.die_sound[reason].play()
        glMainCanvas.blit(FailTitle.image, FailTitle.image.get_rect(
            center=(LEVEL_WIDTH * BLOCK_WIDTH / 2, LEVEL_HEIGHT * BLOCK_WIDTH / 2)))

        btRestart.rect = btRestart.image.get_rect(
            topleft=(LEVEL_WIDTH * BLOCK_WIDTH / 2 - btRestart.rect.width - BLOCK_WIDTH,
                     LEVEL_HEIGHT * BLOCK_WIDTH / 2 + BLOCK_WIDTH * 2))
        glMainCanvas.blit(btRestart.get_image(), btRestart.rect)

        buttons.append(btRestart)
    else:  # Если переход на следующий уровень, то а) нужный звук и б) кнопка "Next level"
        levelEnd_sound.play()
        glMainCanvas.blit(WinTitle.image, WinTitle.image.get_rect(
            center=(LEVEL_WIDTH * BLOCK_WIDTH / 2, LEVEL_HEIGHT * BLOCK_WIDTH / 2)))
        btNext.rect = btNext.image.get_rect(
            topleft=(LEVEL_WIDTH * BLOCK_WIDTH / 2 - btNext.rect.width - BLOCK_WIDTH,
                     LEVEL_HEIGHT * BLOCK_WIDTH / 2 + BLOCK_WIDTH * 2))
        glMainCanvas.blit(btNext.get_image(), btNext.rect)
        buttons.append(btNext)

    btQuit.rect = btQuit.image.get_rect(topleft=(LEVEL_WIDTH * BLOCK_WIDTH / 2 + BLOCK_WIDTH,
                                                 LEVEL_HEIGHT * BLOCK_WIDTH / 2 + BLOCK_WIDTH * 2))
    glMainCanvas.blit(btQuit.get_image(), btQuit.rect)
    pygame.display.update()

    # Ждём реакции пользователя
    # Это либо клик мыши по соответствующей кнопке, либо нажатие нужной кнопки на клавиатуре
    wait_state = True
    res = ACTION_QUIT
    while wait_state:
        for event in pygame.event.get():
            if event.type == QUIT:
                wait_state = False
                break

            # Для мышки нужно реагировать только на левую кнопку (хранится в event.button)
            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.rect.collidepoint(event.pos):
                        draw_button(button, True)

            if event.type == MOUSEBUTTONUP and event.button == 1:
                for button in buttons:
                    if button.rect.collidepoint(event.pos):
                        res = draw_button(button, False)
                        wait_state = False

            if event.type == KEYDOWN:
                for button in buttons:
                    if event.key in button.key:
                        draw_button(button, True)

            if event.type == KEYUP:
                for button in buttons:
                    if event.key in button.key:
                        res = draw_button(button, False)
                        wait_state = False

        pygame.display.update()
    return res


def draw_button(button, state=None):
    """Вспомогательная функция. Рисует на заставке кнопку в соответствующем состоянии"""
    if state is None:
        state = button.pressed_state

    if state:
        button.pressed_state = True
        glMainCanvas.blit(button.get_image(), button.rect)
        return None
    else:
        button.pressed_state = False
        glMainCanvas.blit(button.get_image(), button.rect)
        return button.event


# =========
# Main body
# =========


# В конфигурации мы храним прогресс игрока -- текущий уровень и текущую музыкальную композицию
# А также все константы и настройки
config = configparser.ConfigParser()

current_level = -1
current_song = -1

# Спрайты статичных блоков структуры уровня
STATIC_BLOCKS_FILES = {'Z': "block.png",
                       'H': "ladder.png",
                       'O': "solid.png",
                       '-': "bar.png",
                       '_': "exit_bar.png",
                       'P': "exit_ladder.png",
                       'U': "block.png",
                       '=': "platform.png",
                       }

# Анимированные спрайты структуры уровня
ANIMATED_BLOCKS = {'+': ("Treasure",
                         ("treasure0.png",
                          "treasure1.png",
                          "treasure2.png",
                          "treasure3.png",
                          "treasure4.png",
                          "treasure5.png",
                          "treasure6.png",
                          "treasure7.png",
                          ),
                         10,  # задержка между кадрами анимации относительно FPS, больше значение - выше задержка
                         # Интервал (минимум, максимум, шаг), из которого выбираются (случайным образом)
                         # паузы между фазами анимации сокровищ. Так отсутствует раздражающая синхронность
                         # в анимации сокровищ
                         (100, 400, 20),
                         "collect.wav",
                         ),
                   '*': ("Animation",
                         ("saw0.png",
                          "saw1.png",
                          "saw2.png",
                          ),
                         (5, 20, 1),  # задержка между кадрами анимации относительно FPS, больше - выше задержка
                         0,  # пауза анимации. Можно указать и просто число
                         "saw.wav",
                         ),
                   '0': ("Animation",
                         ("fullsaw0.png",
                          "fullsaw1.png",
                          "fullsaw2.png",
                          ),
                         (5, 20, 1),  # задержка между кадрами анимации относительно FPS, больше - выше задержка
                         0,  # пауза анимации. Можно указать и просто число
                         "saw.wav",
                         ),
                   '/': ("Animation",  # Rope body
                         ("Rope0.png",
                          "Rope1.png",
                          "Rope0.png",
                          "Rope2.png",
                          ),
                         20,
                         0,
                         None,
                         ),
                   '\\': ("Animation",  # Rope body
                          ("Rope0.png",
                           "Rope2.png",
                           "Rope0.png",
                           "Rope1.png",
                           ),
                          20,
                          0,
                          None,
                          ),
                   'T': ("Animation",  # Rope head (hook plate)
                         ("Rope base0.png",
                          "Rope base1.png",
                          "Rope base0.png",
                          "Rope base2.png",
                          ),
                         20,
                         0,
                         None,
                         ),
                   'J': ("Animation",  # Rope tail (knot)
                         ("Rope tail0.png",
                          "Rope tail1.png",
                          "Rope tail0.png",
                          "Rope tail2.png",
                          ),
                         20,
                         0,
                         None,
                         ),
                   'L': ("Animation",  # Rope tail (knot)
                         ("Rope tail0.png",
                          "Rope tail2.png",
                          "Rope tail0.png",
                          "Rope tail1.png",
                          ),
                         20,
                         0,
                         None,
                         ),
                   '~': ("Animation",  # Lava
                         ("Lava0.png",
                          "Lava1.png",
                          "Lava2.png",
                          "Lava3.png",
                          "Lava4.png",
                          "Lava5.png",
                          "Lava6.png",
                          "Lava7.png",
                          "Lava8.png",
                          "Lava9.png",
                          ),
                         (15, 30, 1),
                         (1, 20, 1),
                         "burned.wav",
                         ),
                   }

# Кадры анимации для спрайта игрока. Относительно каталога images\Player
PLAYER_FRAMES = {"idle_delay": 300,
                 "fall_delay": 100,
                 "folder": "Player",
                 "idle": ("player_idle0.png",
                          "player_idle1.png",
                          "player_idle2.png",
                          "player_idle3.png",
                          ),
                 "fall": ("player_fall0.png",
                          "player_fall1.png",
                          "player_fall2.png",
                          "player_fall3.png",
                          ),
                 "hang": ("player_hang_idle0.png",
                          "player_hang_idle1.png",
                          ),
                 "walk_right": ("player_walk0.png",
                                "player_walk1.png",
                                "player_walk2.png",
                                "player_walk3.png",
                                "player_walk4.png",
                                "player_walk5.png",
                                "player_walk6.png",
                                "player_walk7.png"),
                 "walk_hang_right": ("character_maleAdventurer_hang0.png",
                                     "character_maleAdventurer_hang1.png",
                                     "character_maleAdventurer_hang2.png",
                                     "character_maleAdventurer_hang3.png",
                                     ),
                 "climb_up": ("player_climb0.png",
                              "player_climb1.png",
                              "player_climb2.png",
                              "player_climb3.png",
                              "player_climb4.png",
                              "player_climb5.png",
                              "player_climb6.png",
                              "player_climb7.png",
                              ),
                 "attack_left": ("attack0.png",
                                 "attack1.png",
                                 "attack2.png",
                                 "attack3.png",
                                 "attack3.png",
                                 "attack4.png",
                                 "attack5.png",
                                 "attack6.png",
                                 ),
                 }

# Кадры для анимации монстров. Относительно каталога images\Beast
BEAST_FRAMES = {'X': {"folder": "Beast",
                      "dieSound": "beast die.wav",
                      "idle_delay": 250,
                      "fall_delay": 100,
                      "idle": ("zombie_idle0.png",
                               "zombie_idle1.png",
                               "zombie_idle0.png",
                               "zombie_idle2.png",
                               ),
                      "fall": ("zombie_fall0.png",
                               "zombie_fall1.png",
                               "zombie_fall2.png",
                               "zombie_fall1.png",),
                      "hang": ("zombie_hang_idle0.png",
                               "zombie_hang_idle1.png",
                               "zombie_hang_idle0.png",
                               "zombie_hang_idle2.png",),
                      "walk_right": ("zombie_walk0.png",
                                     "zombie_walk1.png",
                                     "zombie_walk2.png",
                                     "zombie_walk3.png",
                                     "zombie_walk4.png",
                                     "zombie_walk5.png",
                                     "zombie_walk6.png",
                                     "zombie_walk7.png",),
                      "walk_hang_right": ("zombie_hang0.png",
                                          "zombie_hang1.png",
                                          "zombie_hang2.png",
                                          "zombie_hang3.png",
                                          "zombie_hang4.png",
                                          "zombie_hang5.png",
                                          "zombie_hang6.png",
                                          "zombie_hang7.png",
                                          ),
                      "climb_up": ("zombie_climb0.png",
                                   "zombie_climb1.png",
                                   "zombie_climb2.png",
                                   "zombie_climb3.png",
                                   "zombie_climb4.png",
                                   "zombie_climb5.png",
                                   "zombie_climb6.png",
                                   "zombie_climb7.png",)
                      },
                }

# Размеры спрайтов и уровня в целом
BLOCK_WIDTH = 38
LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22

STEP = 24  # Шагов анимации между ключевыми кадрами (в которых игра воспринимает управление)
TEMPO = 12  # Количество ключевых кадров в секунду. Темп игры

# Для корректной работы BEAST_STEP * BEAST_TEMPO должно совпадать с FPS
# Поэтому надо подбирать значения тщательно, чтобы всё делилось нацело
# Если эти значения совпадают со значениями игрока, монстры перемещаются с его скоростью
# Изменяя эти значения можно добиться либо замедления, либо ускорения монстров относительно игрока
BEAST_TEMPO = 8  # У монстров ключевых кадров меньше. Они более медлительны

if path.exists(SETTINGS_FILE):
    config.read(SETTINGS_FILE)
    current_level = int(config.get("Progress", "current level", fallback=current_level + 1)) - 1
    current_song = int(config.get("Progress", "current song", fallback=current_song + 1)) - 1

    STATIC_BLOCKS_FILES = json.loads(
        config.get("Blocks", "STATIC BLOCKS FILES", fallback=json.dumps(STATIC_BLOCKS_FILES)).replace("'", "\""))
    ANIMATED_BLOCKS = json.loads(
        config.get("Blocks", "ANIMATED BLOCKS", fallback=json.dumps(ANIMATED_BLOCKS)).replace("'", "\""))

    PLAYER_FRAMES = json.loads(
        config.get("Characters", "PLAYER FRAMES", fallback=json.dumps(PLAYER_FRAMES)).replace("'", "\""))
    BEAST_FRAMES = json.loads(
        config.get("Characters", "BEAST FRAMES", fallback=json.dumps(BEAST_FRAMES)).replace("'", "\""))

    BLOCK_WIDTH = int(config.get("Geometry", "BLOCK WIDTH", fallback=BLOCK_WIDTH))
    LEVEL_WIDTH = int(config.get("Geometry", "LEVEL WIDTH", fallback=LEVEL_WIDTH))
    LEVEL_HEIGHT = int(config.get("Geometry", "LEVEL HEIGHT", fallback=LEVEL_HEIGHT))

    STEP = int(config.get("Game", "STEP", fallback=STEP))
    TEMPO = int(config.get("Game", "TEMPO", fallback=TEMPO))
    BEAST_TEMPO = int(config.get("Game", "BEAST TEMPO", fallback=BEAST_TEMPO))

    character.SOLID_BLOCKS = json.loads(
        config.get("Structure", "SOLID BLOCKS", fallback=json.dumps(character.SOLID_BLOCKS)).replace("'", "\""))
    character.DESTRUCTABLE_BLOCKS = json.loads(
        config.get("Structure", "DESTRUCTABLE BLOCKS",
                   fallback=json.dumps(character.DESTRUCTABLE_BLOCKS)).replace("'", "\""))
    character.SUPPORT_BLOCKS = json.loads(
        config.get("Structure", "SUPPORT BLOCKS", fallback=json.dumps(character.SUPPORT_BLOCKS)).replace("'", "\""))
    character.CARRY_BLOCKS = json.loads(
        config.get("Structure", "CARRY BLOCKS", fallback=json.dumps(character.CARRY_BLOCKS)).replace("'", "\""))
    character.HANG_BLOCKS = json.loads(
        config.get("Structure", "HANG BLOCKS", fallback=json.dumps(character.HANG_BLOCKS)).replace("'", "\""))
    character.CLIMB_BLOCKS = json.loads(
        config.get("Structure", "CLIMB BLOCKS", fallback=json.dumps(character.CLIMB_BLOCKS)).replace("'", "\""))
    character.VIRTUAL_BLOCKS = json.loads(
        config.get("Structure", "VIRTUAL BLOCKS", fallback=json.dumps(character.VIRTUAL_BLOCKS)).replace("'", "\""))
    character.TREASURE_BLOCKS = json.loads(
        config.get("Structure", "TREASURE BLOCKS", fallback=json.dumps(character.TREASURE_BLOCKS)).replace("'", "\""))
    character.EXIT_BLOCKS = json.loads(
        config.get("Structure", "EXIT BLOCKS", fallback=json.dumps(character.EXIT_BLOCKS)).replace("'", "\""))
    character.BEAST_BLOCKS = json.loads(
        config.get("Structure", "BEAST BLOCKS", fallback=json.dumps(character.BEAST_BLOCKS)).replace("'", "\""))
    character.DEADLY_BLOCKS = json.loads(
        config.get("Structure", "DEADLY BLOCKS", fallback=json.dumps(character.DEADLY_BLOCKS)).replace("'", "\""))
else:
    config.add_section("Progress")
    config.add_section("Game")
    config.add_section("Geometry")
    config.add_section("Characters")
    config.add_section("Blocks")
    config.add_section("Structure")

    config["Progress"]["current level"] = str(current_level)
    config["Progress"]["current song"] = str(current_song)
    config["Game"]["STEP"] = str(STEP)
    config["Game"]["TEMPO"] = str(TEMPO)
    config["Game"]["BEAST TEMPO"] = str(BEAST_TEMPO)
    config["Geometry"]["BLOCK WIDTH"] = str(BLOCK_WIDTH)
    config["Geometry"]["LEVEL WIDTH"] = str(LEVEL_WIDTH)
    config["Geometry"]["LEVEL HEIGHT"] = str(LEVEL_HEIGHT)
    config["Blocks"]["STATIC BLOCKS FILES"] = json.dumps(STATIC_BLOCKS_FILES)
    config["Blocks"]["ANIMATED BLOCKS"] = json.dumps(ANIMATED_BLOCKS)
    config["Characters"]["PLAYER FRAMES"] = json.dumps(PLAYER_FRAMES)
    config["Characters"]["BEAST FRAMES"] = json.dumps(BEAST_FRAMES)
    config["Structure"]["SOLID BLOCKS"] = json.dumps(character.SOLID_BLOCKS)
    config["Structure"]["DESTRUCTABLE BLOCKS"] = json.dumps(character.DESTRUCTABLE_BLOCKS)
    config["Structure"]["SUPPORT BLOCKS"] = json.dumps(character.SUPPORT_BLOCKS)
    config["Structure"]["CARRY BLOCKS"] = json.dumps(character.CARRY_BLOCKS)
    config["Structure"]["HANG BLOCKS"] = json.dumps(character.HANG_BLOCKS)
    config["Structure"]["CLIMB BLOCKS"] = json.dumps(character.CLIMB_BLOCKS)
    config["Structure"]["VIRTUAL BLOCKS"] = json.dumps(character.VIRTUAL_BLOCKS)
    config["Structure"]["TREASURE BLOCKS"] = json.dumps(character.TREASURE_BLOCKS)
    config["Structure"]["EXIT BLOCKS"] = json.dumps(character.EXIT_BLOCKS)
    config["Structure"]["BEAST BLOCKS"] = json.dumps(character.BEAST_BLOCKS)
    config["Structure"]["DEADLY BLOCKS"] = json.dumps(character.DEADLY_BLOCKS)

FPS = TEMPO * STEP
BEAST_STEP = int(FPS / BEAST_TEMPO)
BEAST_ANIMATION_STEP = BLOCK_WIDTH / BEAST_STEP  # Смещение объекта в пикселах за один шаг анимации
PLAYER_ANIMATION_STEP = BLOCK_WIDTH / STEP  # Смещение объекта в пикселах за один шаг анимации

block.BLOCK_WIDTH = BLOCK_WIDTH
character.LEVEL_WIDTH = LEVEL_WIDTH
character.LEVEL_HEIGHT = LEVEL_HEIGHT
character.CRACKED_BLOCK_LIFETIME = int(FPS * 2.2)

glMainCanvas = init_screen(block.BLOCK_WIDTH * LEVEL_WIDTH, block.BLOCK_WIDTH * LEVEL_HEIGHT)

STATIC_BLOCKS = dict()
for ch in STATIC_BLOCKS_FILES:
    STATIC_BLOCKS[ch] = block.Block(STATIC_BLOCKS_FILES[ch])

glPlayer = character.Player(PLAYER_FRAMES, subfolder=PLAYER_FRAMES["folder"],
                            sounds=(load_sound("footsteps.wav"), load_sound("attack.wav"),
                                    {GAME_OVER_EATEN: load_sound("eaten.wav"),
                                     GAME_OVER_KILLED: load_sound("beast die.wav"),
                                     GAME_OVER_STUCK: load_sound("beast die.wav"),
                                     GAME_OVER_USER_END: load_sound("user end.wav"),
                                     }),
                            idle_delay=PLAYER_FRAMES["idle_delay"],
                            fall_delay=PLAYER_FRAMES["fall_delay"])

levelEnd_sound = load_sound("level end.wav")
exitAppears_sound = load_sound("exit.wav")

FailTitle = block.Block("Game over title.jpg", "Titles")
WinTitle = block.Block("Win title.jpg", "Titles")
IntroTitle = block.Block("Intro title.jpg", "Titles")

btRestart = block.Button(("Restart.jpg", "Restart pressed.jpg"), "Buttons", event=ACTION_RESTART,
                         key=(K_RETURN, K_KP_ENTER, K_SPACE))
btQuit = block.Button(("Quit.jpg", "Quit pressed.jpg"), "Buttons", event=ACTION_QUIT, key=(K_ESCAPE,))
btNext = block.Button(("Next.jpg", "Next pressed.jpg"), "Buttons", event=ACTION_NEXT,
                      key=(K_RETURN, K_KP_ENTER, K_SPACE))

game_over_reason = GAME_OVER_COMPLETE
whatNext = ACTION_NEXT

#
# Intro screen
#

glMainCanvas.blit(IntroTitle.image,
                  IntroTitle.image.get_rect(center=(LEVEL_WIDTH * BLOCK_WIDTH / 2, LEVEL_HEIGHT * BLOCK_WIDTH / 2)))
pygame.display.update()

pygame.mixer.music.load(path.join(path.dirname(__file__), "Sounds", "INTRO.mp3"))
pygame.mixer.music.set_volume(0.3)
pygame.mixer.music.play(-1)

# Wait user input to startup our game
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        if event.type == KEYUP or event.type == MOUSEBUTTONUP:
            running = False

pygame.mixer.music.stop()

#
# Enumerate levels
#
(levels_dir, _, levels_list) = next(walk(path.join(path.dirname(__file__), "Levels")), (None, None, []))

#
# And music
#
(music_dir, _, songs_list) = next(walk(path.join(path.dirname(__file__), "Music")), (None, None, []))

#
# Game loop itself
#
# С этого момента начинается специфическая для уровня инициализация, загрузка
# и игровой цикл
#

while whatNext in (ACTION_NEXT, ACTION_RESTART):
    glBeasts = list()
    glAnimatedEntities = dict()
    glTemporaryItems = list()

    exitAppears_sound.stop()
    levelEnd_sound.stop()

    current_song += (whatNext == ACTION_NEXT)
    if current_song >= len(songs_list):
        current_song = 0
    pygame.mixer.music.load(path.join(music_dir, songs_list[current_song]))
    pygame.mixer.music.set_volume(0.1)
    pygame.mixer.music.play(-1)

    # Мы отдельно считаем количество сокровищ, так как они хранятся в общем массиве с анимированными спрайтами.
    # Здесь заложена техническая возможность украсить уровень разными интересными плюшками,
    # как чисто декоративными, так и всякими препятствиями (пилы, шипы, верёвки, капающая кислота, огонь и лава и т.п.)
    glTreasuresCount = 0

    if whatNext == ACTION_NEXT:
        current_level = current_level + 1 if current_level < len(levels_list) - 1 else 0
    whatNext = ACTION_RESTART

    # Сразу нужно сохранить прогресс. Мало ли, выключится свет, слетит игра -- игрок должен вернуться именно на тот
    # уровень, до которого дошёл
    config["Progress"]["current level"] = str(current_level)
    config["Progress"]["current song"] = str(current_song)
    with open(SETTINGS_FILE, "w") as config_file:
        config.write(config_file)

    glCurrentLevel = load_level(path.join(levels_dir, levels_list[current_level]))
    character.glCurrentLevel = glCurrentLevel

    glStaticCanvas = pygame.Surface(glMainCanvas.get_size())
    show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)

    #
    # Pause 1,5 sec for user to look around new level
    # Beasts, treasures and player are blinking at this time
    #
    for i in range(8):
        glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())
        for animBlock in glAnimatedEntities.values():
            glMainCanvas.blit(animBlock.get_image(0), get_screen_pos(animBlock.pos))
        if i % 2 == 0:
            glMainCanvas.blit(glPlayer.get_image(0, STEP),
                              get_screen_pos(glPlayer.pos, PLAYER_ANIMATION_STEP, glPlayer.oldpos, 0))
            for beast in glBeasts:
                glMainCanvas.blit(beast.get_image(0, BEAST_STEP),
                                  get_screen_pos(beast.pos, BEAST_ANIMATION_STEP, beast.oldpos, 0))
        pygame.display.update()
        glClock.tick(8)

    running = True
    player_tick = 0
    beast_tick = 0

    # =================================================================================================
    # Game lifecycle
    # =================================================================================================
    while running:
        # =================================
        # Actions on user interrupt attempt
        # =================================
        for event in pygame.event.get():
            if event.type == QUIT or \
                    (event.type == KEYUP and event.key == K_ESCAPE):
                whatNext = ACTION_QUIT
                game_over_reason = GAME_OVER_USER_END
                running = False

        # =====================
        # Erasing old animation
        # =====================
        glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())

        # =======================================
        # Do player movement and collisions check
        # =======================================
        if player_tick == 0:
            running = glPlayer.move(glBeasts, temporary_items=glTemporaryItems)
            if not running:
                game_over_reason = GAME_OVER_EATEN
            else:
                collect_treasures(glPlayer.oldpos)
            if glPlayer.oldpos[0] == 0 and running:
                game_over_reason = GAME_OVER_COMPLETE
                running = False

        # ================================================
        # Drawing items in their positions
        # First -- non-movable level blocks with animation
        # ================================================
        for animBlock in glAnimatedEntities.values():
            glMainCanvas.blit(animBlock.get_image(player_tick), get_screen_pos(animBlock.pos))

        # ==================================================================
        # Second -- draw temporary items and do collision check if necessary
        # ==================================================================
        for tempBlock in glTemporaryItems:
            glMainCanvas.blit(tempBlock.get_image(player_tick), get_screen_pos(tempBlock.pos))
            if tempBlock.died:
                if tempBlock.underlay is not None:
                    if not respawn_beasts(tempBlock):
                        game_over_reason = GAME_OVER_STUCK
                        running = False
                    glCurrentLevel[0][tempBlock.pos[0]][tempBlock.pos[1]] = tempBlock.underlay
                del glTemporaryItems[glTemporaryItems.index(tempBlock)]

        # ===========================
        # Third -- draw player sprite
        # ===========================
        glMainCanvas.blit(glPlayer.get_image(player_tick, STEP),
                          get_screen_pos(glPlayer.pos, PLAYER_ANIMATION_STEP, glPlayer.oldpos, player_tick))

        # ==================================================================
        # Fourth -- move all beasts and again do collision check with player
        # ==================================================================
        for beast in glBeasts:
            if beast_tick == 0:
                # Метод возвращает ложь, если монстр оказался в позиции игрока
                # В нашей ситуации это означает съедение
                if not beast.move(glPlayer.pos, glBeasts):
                    running = False
                    game_over_reason = GAME_OVER_EATEN
                else:
                    if glCurrentLevel[0][beast.oldpos[0]][beast.oldpos[1]] in character.DEADLY_BLOCKS:
                        key = str(beast.oldpos[0]) + ":" + str(beast.oldpos[1]) + ":" + \
                              glCurrentLevel[0][beast.oldpos[0]][beast.oldpos[1]]
                        if glAnimatedEntities[key].hit_sound is not None:
                            glAnimatedEntities[key].hit_sound.play()
                        die_beast(beast)
            glMainCanvas.blit(beast.get_image(beast_tick, BEAST_STEP),
                              get_screen_pos(beast.pos, BEAST_ANIMATION_STEP, beast.oldpos, beast_tick))

        # ==============================================================
        # And finally -- check characters for standing over deadly block
        # ==============================================================
        if glCurrentLevel[0][glPlayer.oldpos[0]][glPlayer.oldpos[1]] in character.DEADLY_BLOCKS:
            key = str(glPlayer.oldpos[0]) + ":" + str(glPlayer.oldpos[1]) + ":" + \
                  glCurrentLevel[0][glPlayer.oldpos[0]][glPlayer.oldpos[1]]
            if glAnimatedEntities[key].hit_sound is not None:
                glAnimatedEntities[key].hit_sound.play()
            running = False
            game_over_reason = GAME_OVER_KILLED

        player_tick = player_tick + 1 if player_tick < STEP - 1 else 0
        beast_tick = beast_tick + 1 if beast_tick < BEAST_STEP - 1 else 0

        pygame.display.update()
        glClock.tick(FPS)

    pygame.mixer.music.fadeout(500)
    whatNext = game_over(game_over_reason)

config["Progress"]["current level"] = str(current_level)
config["Progress"]["current song"] = str(current_song)
with open(SETTINGS_FILE, "w") as config_file:
    config.write(config_file)

pygame.quit()
