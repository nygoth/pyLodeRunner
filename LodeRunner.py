# LodeRunner clone game
# This project is for studying python programming
# V 7.7
# Рефактор кода.
# Кроме того, настройки разнесены по разным файлам. Собственно настройки -- то, что считывается вначале игры и больше
# не меняется, и состояние игры, которое меняется от уровня к уровню.
# Кроме того, некоторый код перенесён в соответствующие классы как метод. Был глобальной процедурой.
#
# План на 7.8 -- Реализация отдельного класса для уровня, перенос в него всех
# # проблем, связанных с загрузкой, анимацией и прочими вещами, характерными для уровней.
# Плюс -- новый формат уровней. Помимо символов блоков нужно сделать такую же по размеру таблицу,
# которая будет задавать какие-то атрибуты блоков. Как минимум, группировку нескольких блоков в одну группу анимации.
# Чтобы верёвки, например, колебались каждая со своей скоростью.

# В данном проекте есть один серьёзный недочёт дизайна -- сейчас при загрузке уровня
# все анимированные спрайты создаются и загружаются заново. На каждый новый уровень. Причём, на каждый блок своя копия.
# Это неоптимально. Картинки анимации, например, достаточно загрузить один раз за всю игру
# по одному экземпляру на каждый тип анимированного спрайта.
# Для этого можно ввести промежуточный класс между Block и всеми наследниками -- что-то типа ImageArray
# Или перед Block, а последний сделать вырожденным случаем.

# Замечание на релиз 8.0. Для улучшения вовлечённости, нужно добавить подсчёт очков за уровень и, возможно, ввести
# опционально количество жизней. Очки считать очень просто -- обратное от времени, прошедшего между подборами сокровищ.
# Смысл в том, что чем быстрее собираются сокровища (и достигается выход), тем больше очков за уровень получаешь.
# Можно вести таблицу рекордов в сети.

from os import walk
import random
import sys
import ctypes

import configparser
import pygame
from pygame.locals import *

import block
from block import BLOCK_WIDTH
import character

from game_structure import *

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
                                            animation_delay=random.randrange(int(ANIMATED_BLOCKS[ch][2][0]),
                                                                             int(ANIMATED_BLOCKS[ch][2][1]),
                                                                             int(ANIMATED_BLOCKS[ch][2][2]))
                                                if isinstance(ANIMATED_BLOCKS[ch][2], (list, tuple))
                                                else ANIMATED_BLOCKS[ch][2],
                                            animation_pause=random.randrange(int(ANIMATED_BLOCKS[ch][3][0]),
                                                                             int(ANIMATED_BLOCKS[ch][3][1]),
                                                                             int(ANIMATED_BLOCKS[ch][3][2]))
                                                if isinstance(ANIMATED_BLOCKS[ch][3], (list, tuple))
                                                else ANIMATED_BLOCKS[ch][3],
                                            hit_sound=load_sound(ANIMATED_BLOCKS[ch][4]))
                    if ch in character.TREASURE_BLOCKS:
                        glTreasuresCount += 1

                if ch in character.BEAST_BLOCKS:
                    glBeasts.append(character.Beast(BEAST_UNITS[ch], [row, col], subfolder=BEAST_UNITS[ch]["folder"],
                                                    sounds=(None, None, load_sound(BEAST_UNITS[ch]["dieSound"])),
                                                    idle_delay=BEAST_UNITS[ch]["idle_delay"],
                                                    fall_delay=BEAST_UNITS[ch]["fall_delay"]))

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
        for blk in row:
            # Используем метод get. Он не выдаёт ошибок, если индекс отсутствует, а возвращает None, что удобнее
            cur_block = sprites.get(blk)

            if cur_block is not None:
                canvas.blit(cur_block.image, cur_block.image.get_rect(topleft=(x * BLOCK_WIDTH, y * BLOCK_WIDTH)))
            x += 1
        y += 1


def collect_treasures(pos):
    """Проверка на подбор сокровища игроком. Если все сокровища собраны, добавляем выход с уровня"""
    global glTreasuresCount
    for chb in character.TREASURE_BLOCKS:
        key = str(pos[0]) + ":" + str(pos[1]) + ":" + chb
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
                    for chx in line:
                        glCurrentLevel[0][row][col] = chx if chx != '.' else glCurrentLevel[0][row][col]
                        col += 1
                    row += 1

                show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)


def block_killing_action(block: block):
    """Проверяем, не зажало ли игрока или монстра зарастающей стеной"""
    if glPlayer.pos[0] == block.pos[0] and glPlayer.pos[1] == block.pos[1]:
        return False
    for beast in glBeasts:
        if beast.pos[0] == block.pos[0] and beast.pos[1] == block.pos[1]:
            beast.die()
    return True


def game_over(reason: int):
    """Действия, которые нужно выполнить при завершении игры (по любой причине)"""
    buttons = [btQuit, ]
    screen_halfwidth = LEVEL_WIDTH * BLOCK_WIDTH / 2
    screen_halfheight = LEVEL_HEIGHT * BLOCK_WIDTH / 2

    # Если игрок уровень проиграл, то нужно воспроизвести соответствующий звук
    # Кроме того, на экране заставки нужно добавить кнопку Restart
    if reason != GAME_OVER_COMPLETE:
        if glPlayer.die_sound is not None:
            glPlayer.die_sound[reason].play()
        glMainCanvas.blit(FailTitle.image, FailTitle.image.get_rect(
            center=(screen_halfwidth, screen_halfheight)))

        btRestart.rect = btRestart.image.get_rect(
            topleft=(screen_halfwidth - btRestart.rect.width - BLOCK_WIDTH,
                     screen_halfheight + BLOCK_WIDTH * 2))
        btRestart.show(glMainCanvas)
        buttons.append(btRestart)

    else:  # Если переход на следующий уровень, то а) нужный звук и б) кнопка "Next level"
        levelEnd_sound.play()
        glMainCanvas.blit(WinTitle.image, WinTitle.image.get_rect(
            center=(screen_halfwidth, screen_halfheight)))
        btNext.rect = btNext.image.get_rect(
            topleft=(screen_halfwidth - btNext.rect.width - BLOCK_WIDTH,
                     screen_halfheight + BLOCK_WIDTH * 2))
        btNext.show(glMainCanvas)
        buttons.append(btNext)

    btQuit.rect = btQuit.image.get_rect(topleft=(screen_halfwidth + BLOCK_WIDTH,
                                                 screen_halfheight + BLOCK_WIDTH * 2))
    btQuit.show(glMainCanvas)
    pygame.display.update()

    # Ждём реакции пользователя
    # Это либо клик мыши по соответствующей кнопке, либо нажатие нужной кнопки на клавиатуре
    wait_state = True
    res = ACTION_QUIT
    while wait_state:
        for exit_event in pygame.event.get():
            if exit_event.type == QUIT:
                wait_state = False
                break

            # Для мышки нужно реагировать только на левую кнопку (хранится в exit_event.button)
            if exit_event.type in (MOUSEBUTTONDOWN, MOUSEBUTTONUP) and exit_event.button == 1:
                for button in buttons:
                    if button.rect.collidepoint(exit_event.pos):
                        res = button.show(glMainCanvas, exit_event.type == MOUSEBUTTONDOWN)
                        wait_state = (exit_event.type == MOUSEBUTTONDOWN)

            if exit_event.type in (KEYDOWN, KEYUP):
                for button in buttons:
                    if exit_event.key in button.key:
                        res = button.show(glMainCanvas, exit_event.type == KEYDOWN)
                        wait_state = (exit_event.type == KEYDOWN)

        pygame.display.update()
    return res


# =========
# Main body
# =========


# В файле состояния мы храним прогресс игрока -- текущий уровень и текущую музыкальную композицию
# Все константы и настройки мы храним в конфигурации игры
config = configparser.ConfigParser()
game_state = configparser.ConfigParser()

current_level, current_song = init_config(game_state, config)

FPS = TEMPO * STEP
BEAST_STEP = int(FPS / BEAST_TEMPO)
BEAST_ANIMATION_STEP = BLOCK_WIDTH / BEAST_STEP  # Смещение объекта в пикселах за один шаг анимации
PLAYER_ANIMATION_STEP = BLOCK_WIDTH / STEP  # Смещение объекта в пикселах за один шаг анимации

character.LEVEL_WIDTH = LEVEL_WIDTH
character.LEVEL_HEIGHT = LEVEL_HEIGHT
character.CRACKED_BLOCK_LIFETIME = int(FPS * 2.2)

# This makes game screen insensitive to Windows 10 scale setting in screen preferences
ctypes.windll.user32.SetProcessDPIAware()
glMainCanvas = init_screen(BLOCK_WIDTH * LEVEL_WIDTH, BLOCK_WIDTH * LEVEL_HEIGHT)

STATIC_BLOCKS = dict()
for ch in STATIC_BLOCKS_FILES:
    STATIC_BLOCKS[ch] = block.Block(STATIC_BLOCKS_FILES[ch])

glPlayer = character.Player(PLAYER_UNIT["animation"], subfolder=PLAYER_UNIT["folder"],
                            sounds=(load_sound(PLAYER_UNIT["sounds"]["steps"]),
                                    load_sound(PLAYER_UNIT["sounds"]["attack"]),
                                    {GAME_OVER_EATEN: load_sound(PLAYER_UNIT["sounds"]["eaten"]),
                                     GAME_OVER_KILLED: load_sound(PLAYER_UNIT["sounds"]["killed"]),
                                     GAME_OVER_STUCK: load_sound(PLAYER_UNIT["sounds"]["stuck"]),
                                     GAME_OVER_USER_END: load_sound(PLAYER_UNIT["sounds"]["leave"]),
                                     }),
                            idle_delay=PLAYER_UNIT["idle_delay"],
                            fall_delay=PLAYER_UNIT["fall_delay"])

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

# Wait user input to start up our game
running = True
while running:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        running = not (event.type in (KEYUP, MOUSEBUTTONUP))

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
        current_level = (0, current_level + 1)[current_level < len(levels_list) - 1]
    whatNext = ACTION_RESTART

    # Сразу нужно сохранить прогресс. Мало ли, выключится свет, слетит игра -- игрок должен вернуться именно на тот
    # уровень, до которого дошёл
    game_state["Progress"]["current level"], game_state["Progress"]["current song"] = \
        str(current_level), str(current_song)
    with open(GAME_STATE_FILE, "w") as config_file:
        game_state.write(config_file)

    glCurrentLevel = load_level(path.join(levels_dir, levels_list[current_level]))
    character.glCurrentLevel = glCurrentLevel

    glStaticCanvas = pygame.Surface(glMainCanvas.get_size())
    show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)

    #
    # Pause 1,5 sec for user to look around new level
    # Beasts, treasures and player are blinking at this time
    #
    # TODO Перенести всю графику в класс Block. Туда же get_screen_pos и прочее. Чтобы этот кусок кода, по сути
    # TODO был просто вызовом show для соответствующего объекта
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
    player_tick = beast_tick = 0

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
                    # TODO Check, whether we can move block_killing_action to TemporaryBlock class
                    if not block_killing_action(tempBlock):
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
                              str(glCurrentLevel[0][beast.oldpos[0]][beast.oldpos[1]])
                        if glAnimatedEntities[key].hit_sound is not None:
                            glAnimatedEntities[key].hit_sound.play()
                        beast.die()
            glMainCanvas.blit(beast.get_image(beast_tick, BEAST_STEP),
                              get_screen_pos(beast.pos, BEAST_ANIMATION_STEP, beast.oldpos, beast_tick))

        # ==============================================================
        # And finally -- check characters for standing over deadly block
        # ==============================================================
        if glCurrentLevel[0][glPlayer.oldpos[0]][glPlayer.oldpos[1]] in character.DEADLY_BLOCKS:
            key = str(glPlayer.oldpos[0]) + ":" + str(glPlayer.oldpos[1]) + ":" + \
                  str(glCurrentLevel[0][glPlayer.oldpos[0]][glPlayer.oldpos[1]])
            if glAnimatedEntities[key].hit_sound is not None:
                glAnimatedEntities[key].hit_sound.play()
            running = False
            game_over_reason = GAME_OVER_KILLED

        player_tick = (0, player_tick + 1)[player_tick < STEP - 1]
        beast_tick = (0, beast_tick + 1)[beast_tick < BEAST_STEP - 1]

        pygame.display.update()
        glClock.tick(FPS)

    pygame.mixer.music.fadeout(500)
    whatNext = game_over(game_over_reason)

game_state["Progress"]["current level"], game_state["Progress"]["current song"] = \
    str(current_level), str(current_song)
with open(GAME_STATE_FILE, "w") as config_file:
    game_state.write(config_file)

pygame.quit()
