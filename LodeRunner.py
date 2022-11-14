""" LodeRunner clone game
 This project is for studying python programming

 V 7.9

 Рефактор кода.
 Реализация отдельного класса для уровня, перенос в него всех проблем, связанных с загрузкой, анимацией и
 прочими вещами, характерными для уровней. Там же сделан жизненный цикл уровня -- один тик. Тиками управляет
 цикл в главном модуле.


 В данном проекте есть один серьёзный недочёт дизайна -- сейчас при загрузке уровня
 все анимированные спрайты создаются и загружаются заново. На каждый новый уровень. Причём, на каждый блок своя копия.
 Это не оптимально. Картинки анимации, например, достаточно загрузить один раз за всю игру
 по одному экземпляру на каждый тип анимированного спрайта.
 Для этого можно ввести промежуточный класс между Block и всеми наследниками -- что-то типа ImageArray
 Или перед Block, а последний сделать вырожденным случаем.

 Замечание на релиз 8.0. Для улучшения вовлечённости, нужно добавить подсчёт очков за уровень и, возможно, ввести
 опционально количество жизней. Очки считать очень просто -- обратное от времени, прошедшего между подборами сокровищ.
 Смысл в том, что чем быстрее собираются сокровища (и достигается выход), тем больше очков за уровень получаешь.
 Можно вести таблицу рекордов в сети.

 Плюс -- новый формат уровней. Помимо символов блоков нужно сделать такую же по размеру таблицу,
 которая будет задавать какие-то атрибуты блоков. Как минимум, группировку нескольких блоков в одну группу анимации.
 Чтобы верёвки, например, колебались каждая со своей скоростью.
"""

from os import walk
import sys
import ctypes
import configparser

import CC
from glb import *

import block
import character
import level


# What next after level end (fail or win)
ACTION_QUIT = 0  # Exit program
ACTION_NEXT = 1  # Proceed to next level
ACTION_RESTART = 2  # Restart current level

glClock = pygame.time.Clock()


def init_screen(width, height):
    """Инициализирует экран, создаёт игровое окно"""
    pygame.init()

    scr = pygame.display.set_mode((width, height))
    pygame.display.set_caption("pyLode Runner")
    return scr


def game_over(reason: int):
    """Действия, которые нужно выполнить при завершении игры (по любой причине)"""
    buttons = [btQuit, ]
    scr_halfwidth, scr_halfheight = (_ * CC.BLOCK_WIDTH / 2 for _ in (CC.LEVEL_WIDTH, CC.LEVEL_HEIGHT))

    # Если игрок уровень проиграл, то нужно воспроизвести соответствующий звук
    # Кроме того, на экране заставки нужно добавить кнопку Restart
    if reason != CC.GAME_OVER_COMPLETE:
        glLevel.player.die_sound is None or glLevel.player.die_sound[reason].play()
        glMainCanvas.blit(FailTitle.image, FailTitle.image.get_rect(center=(scr_halfwidth, scr_halfheight)))

        btRestart.rect = btRestart.image.get_rect(
            topleft=(scr_halfwidth - btRestart.rect.width - CC.BLOCK_WIDTH, scr_halfheight + CC.BLOCK_WIDTH * 2))
        btRestart.show(glMainCanvas)
        buttons.append(btRestart)

    else:  # Если переход на следующий уровень, то а) нужный звук и б) кнопка "Next level"
        glLevel.level_end_sound.play()
        glMainCanvas.blit(WinTitle.image, WinTitle.image.get_rect(center=(scr_halfwidth, scr_halfheight)))
        btNext.rect = btNext.image.get_rect(
            topleft=(scr_halfwidth - btNext.rect.width - CC.BLOCK_WIDTH, scr_halfheight + CC.BLOCK_WIDTH * 2))
        btNext.show(glMainCanvas)
        buttons.append(btNext)

    btQuit.rect = btQuit.image.get_rect(topleft=(scr_halfwidth + CC.BLOCK_WIDTH, scr_halfheight + CC.BLOCK_WIDTH * 2))
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

current_level, current_song = CC.init_config(game_state, config)

# =======================
# Starting initialization
# =======================

# Override default lifetime value in structure setting to avoid speed-related issues
CC.BLOCKS["temporary"]["cracked"][2] = int(CC.FPS * 2.2)

# This makes game screen insensitive to Windows 10 scale setting in screen preferences
ctypes.windll.user32.SetProcessDPIAware()
glMainCanvas = init_screen(CC.BLOCK_WIDTH * CC.LEVEL_WIDTH, CC.BLOCK_WIDTH * CC.LEVEL_HEIGHT)

glLevel = level.Level(glMainCanvas)

FailTitle = block.Block("Game over title.jpg", subfolder="Titles")
WinTitle = block.Block("Win title.jpg", subfolder="Titles")
IntroTitle = block.Block("Intro title.jpg", subfolder="Titles")

btRestart = block.Button(("Restart.jpg", "Restart pressed.jpg"), "Buttons", event=ACTION_RESTART,
                         key=(K_RETURN, K_KP_ENTER, K_SPACE))
btQuit = block.Button(("Quit.jpg", "Quit pressed.jpg"), "Buttons", event=ACTION_QUIT, key=(K_ESCAPE,))
btNext = block.Button(("Next.jpg", "Next pressed.jpg"), "Buttons", event=ACTION_NEXT,
                      key=(K_RETURN, K_KP_ENTER, K_SPACE))

what_next = ACTION_NEXT

# ============
# Intro screen
# ============

glMainCanvas.blit(IntroTitle.image, IntroTitle.image.get_rect(center=(CC.LEVEL_WIDTH * CC.BLOCK_WIDTH / 2,
                                                                      CC.LEVEL_HEIGHT * CC.BLOCK_WIDTH / 2)))
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

# ================
# Enumerate levels
# ================
(levels_dir, _, levels_list) = next(walk(path.join(path.dirname(__file__), "Levels")), (None, None, []))

# =========
# And music
# =========
(music_dir, _, songs_list) = next(walk(path.join(path.dirname(__file__), "Music")), (None, None, []))

# ========================================
# Game loop itself
#
# С этого момента начинается специфическая
# для уровня инициализация, загрузка и
# игровой цикл
# ========================================
while what_next in (ACTION_NEXT, ACTION_RESTART):
    glLevel.stop_all_sounds()

    current_song = (0, current_song + (what_next == ACTION_NEXT))[current_song < len(songs_list)-1]
    glLevel.play_background_music(path.join(music_dir, songs_list[current_song]))

    if what_next == ACTION_NEXT:
        current_level = (0, current_level + 1)[current_level < len(levels_list) - 1]
    what_next = ACTION_RESTART

    # Сразу нужно сохранить прогресс. Мало ли, выключится свет, слетит игра -- игрок должен вернуться именно на тот
    # уровень, до которого дошёл
    game_state["Progress"]["current level"], game_state["Progress"]["current song"] = \
        str(current_level), str(current_song)
    with open(CC.GAME_STATE_FILE, "w") as config_file:
        game_state.write(config_file)

    glLevel.load(path.join(levels_dir, levels_list[current_level]))

    # ======================================================
    # Pause 1,5 sec for user to look around new level
    # Beasts, treasures and player are blinking at this time
    # ======================================================
    for i in range(8):
        glLevel.show_static()
        glLevel.show_animated(0)
        if i % 2 == 0:
            glLevel.show_player(0)
            glLevel.show_beasts(0)
        pygame.display.update()
        glClock.tick(8)

    game_over_reason = CC.GAME_OVER_NOT_OVER
    player_tick = beast_tick = 0

    # =================================================================================================
    # Game lifecycle
    # =================================================================================================
    while game_over_reason == CC.GAME_OVER_NOT_OVER:
        # =================================
        # Actions on user interrupt attempt
        # =================================
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                what_next = ACTION_QUIT
                game_over_reason = CC.GAME_OVER_USER_END

        # ====================================================
        # Do all level actions, assigned to one single tick.
        # Player and beasts ticks management performed at main
        # module lifecycle.
        # ====================================================
        result = glLevel.live(player_tick, beast_tick)
        game_over_reason = (result, game_over_reason)[result == CC.GAME_OVER_NOT_OVER]

        player_tick = (0, player_tick + 1)[player_tick < CC.STEP - 1]
        beast_tick = (0, beast_tick + 1)[beast_tick < CC.BEAST_STEP - 1]

        pygame.display.update()
        glClock.tick(CC.FPS)

    pygame.mixer.music.fadeout(500)
    what_next = game_over(game_over_reason)

game_state["Progress"]["current level"], game_state["Progress"]["current song"] = \
    str(current_level), str(current_song)
with open(CC.GAME_STATE_FILE, "w") as config_file:
    game_state.write(config_file)

pygame.quit()
