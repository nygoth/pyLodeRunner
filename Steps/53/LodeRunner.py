# LodeRunner clone game
# This project is for studying python programming

# V 5.3
# Game itself

# Реализован временный спрайт, анимация и удаление временных спрайтов
# С его помощью создан эффект атаки для игрока

# Теперь реализуем разрушение уровня игроком и восстановление его
# Для этого временные спрайты должны иметь возможность сохранять элемент, который они закрывают
# Пока это будет реализовано только для статичных блоков.

import random

import pygame
from pygame.locals import *

import block
import character

BLOCK_WIDTH = block.BLOCK_WIDTH
LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22
character.LEVEL_WIDTH = LEVEL_WIDTH
character.LEVEL_HEIGHT = LEVEL_HEIGHT

STEP = 16  # Шагов анимации между ключевыми кадрами (в которых игра воспринимает управление)
TEMPO = 12  # Количество ключевых кадров в секунду. Темп игры
PLAYER_ANIMATION_STEP = BLOCK_WIDTH / STEP  # Смещение объекта в пикселах за один шаг анимации
FPS = TEMPO * STEP

# Для корректной работы BEAST_STEP * BEAST_TEMPO должно совпадать с FPS
# Поэтому надо подбирать значения тщательно, чтобы всё делилось нацело
BEAST_TEMPO = 8  # У монстров ключевых кадров меньше. Они более медлительны
BEAST_STEP = int(FPS / BEAST_TEMPO)
BEAST_ANIMATION_STEP = BLOCK_WIDTH / BEAST_STEP  # Смещение объекта в пикселах за один шаг анимации

TREASURE_DELAY = 10
TREASURE_PAUSE_LIMIT = (100, 400, 20)

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

BEAST_FRAMES = {"idle": ("character_zombie_idle.png",),
                "fall": ("character_zombie_fall0.png",
                         "character_zombie_fall1.png",),
                "hang": ("character_zombie_hang_idle.png",),
                "walk_right": ("character_zombie_walk0.png",
                               "character_zombie_walk1.png",
                               "character_zombie_walk2.png",
                               "character_zombie_walk3.png",
                               "character_zombie_walk4.png",
                               "character_zombie_walk5.png",
                               "character_zombie_walk6.png",
                               "character_zombie_walk7.png"),
                "walk_hang_right": ("character_zombie_hang0.png",
                                    "character_zombie_hang1.png",
                                    "character_zombie_hang2.png",
                                    "character_zombie_hang3.png",
                                    "character_zombie_hang4.png",
                                    "character_zombie_hang5.png",
                                    ),
                "climb_up": ("character_zombie_climb0.png",
                             "character_zombie_climb1.png",
                             "character_zombie_climb2.png",
                             "character_zombie_climb3.png",
                             "character_zombie_climb4.png",
                             "character_zombie_climb5.png",
                             "character_zombie_climb6.png",
                             "character_zombie_climb7.png",)
                }

GAME_OVER_COMPLETE = 0
GAME_OVER_EATEN = 1
GAME_OVER_STUCK = 2
GAME_OVER_STRINGS = ("Congratulations!\nLevel complete!",
                     "Fail!\nEaten by zombie.",
                     "Fail!\nStuck in structure.")

# What next after level end (fail or win)
ACTION_QUIT = 0  # Exit program
ACTION_NEXT = 1  # Proceed to next level
ACTION_RESTART = 2  # Restart current level

glClock = pygame.time.Clock()


def get_screen_pos(pos: list, step=0, oldpos=None, tick=0):
    if oldpos is None:
        return pos[1] * BLOCK_WIDTH, pos[0] * BLOCK_WIDTH

    disp = step * tick
    disp_x = (pos[1] - oldpos[1]) * disp
    disp_y = (pos[0] - oldpos[0]) * disp
    return oldpos[1] * BLOCK_WIDTH + disp_x, oldpos[0] * BLOCK_WIDTH + disp_y


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
            static_line = list()
            exit_line = list()

            col = 0

            for ch in line[0:LEVEL_WIDTH + 1]:
                if ch == 'P':
                    exit_line.append(ch)
                    ch = '.'
                else:
                    exit_line.append('.')

                if ch in ANIMATED_BLOCKS:
                    glAnimatedEntities[str(row) + ":" + str(col) + ":" + ch] = \
                        block.AnimatedBlock(ANIMATED_BLOCKS[ch][1], [row, col], subfolder=ANIMATED_BLOCKS[ch][0],
                                            animation_delay=TREASURE_DELAY,
                                            animation_pause=random.randrange(TREASURE_PAUSE_LIMIT[0],
                                                                             TREASURE_PAUSE_LIMIT[1],
                                                                             TREASURE_PAUSE_LIMIT[2]))
                    if ch == '+':
                        glTreasuresCount += 1

                if ch == 'X':
                    glBeasts.append(character.Beast(BEAST_FRAMES, [row, col], subfolder="Beast"))

                # Персонаж может быть только один, поэтому данный алгоритм вернёт последнее найденное положение
                if ch == 'I':
                    glPlayer.pos = [row, col]
                    glPlayer.oldpos = [row, col]

                static_line.append(('.', ch)[ch in character.MAPPED_BLOCKS])
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
                for ch in line:
                    glCurrentLevel[0][row][col] = ch if ch != '.' else glCurrentLevel[0][row][col]
                    col += 1
                row += 1

            show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)


def respawn_beasts(block: block.TemporaryBlock):
    if glPlayer.pos[0] == block.pos[0] and glPlayer.pos[1] == block.pos[1]:
        return False
    for beast in glBeasts:
        if beast.pos[0] == block.pos[0] and beast.pos[1] == block.pos[1]:
            beast.pos[0] = beast.oldpos[0] = beast.spawn_pos[0]
            beast.pos[1] = beast.oldpos[1] = beast.spawn_pos[1]
    return True


def game_over(reason: int):
    buttons = [btQuit, ]

    if reason in (GAME_OVER_EATEN, GAME_OVER_STUCK):
        glMainCanvas.blit(FailTitle.image, FailTitle.image.get_rect(
            center=(LEVEL_WIDTH * BLOCK_WIDTH / 2, LEVEL_HEIGHT * BLOCK_WIDTH / 2)))

        btRestart.rect = btRestart.image.get_rect(
            topleft=(LEVEL_WIDTH * BLOCK_WIDTH / 2 - btRestart.rect.width - BLOCK_WIDTH,
                     LEVEL_HEIGHT * BLOCK_WIDTH / 2 + BLOCK_WIDTH * 2))
        glMainCanvas.blit(btRestart.get_image(), btRestart.rect)

        buttons.append(btRestart)
    else:
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
    wait_state = True
    ret = ACTION_QUIT
    while wait_state:
        for event in pygame.event.get():
            if event.type == QUIT:
                wait_state = False
                break

            if event.type == MOUSEBUTTONDOWN and event.button == 1:
                for button in buttons:
                    if button.rect.collidepoint(event.pos):
                        button.pressed_state = True
                        glMainCanvas.blit(button.get_image(), button.rect)

            if event.type == MOUSEBUTTONUP and event.button == 1:
                for button in buttons:
                    if button.rect.collidepoint(event.pos):
                        button.pressed_state = False
                        glMainCanvas.blit(button.get_image(), button.rect)
                        ret = button.event
                        wait_state = False

        pygame.display.update()
    return ret


# =========
# Main body
# =========


glMainCanvas = init_screen(block.BLOCK_WIDTH * LEVEL_WIDTH, block.BLOCK_WIDTH * LEVEL_HEIGHT)

STATIC_BLOCKS = {'Z': block.Block("block.png"),
                 'H': block.Block("ladder.png"),
                 'O': block.Block("solid.png"),
                 '-': block.Block("bar.png"),
                 'P': block.Block("exit_ladder.png"),
                 }
ANIMATED_BLOCKS = {'+': ("Treasure", ("treasure0.png",
                                      "treasure1.png",
                                      "treasure2.png",
                                      "treasure3.png",
                                      "treasure4.png",
                                      "treasure5.png",
                                      "treasure6.png",
                                      "treasure7.png",)), }

glPlayer = character.Player(PLAYER_FRAMES, subfolder="Player")

FailTitle = block.Block("Game over title.jpg", "Titles")
WinTitle = block.Block("Win title.jpg", "Titles")

btRestart = block.Button("Restart.jpg", "Restart pressed.jpg", "Buttons", event=ACTION_RESTART)
btQuit = block.Button("Quit.jpg", "Quit pressed.jpg", "Buttons", event=ACTION_QUIT)
btNext = block.Button("Next level.jpg", "Next level pressed.jpg", "Buttons", event=ACTION_NEXT)

game_over_reason = GAME_OVER_COMPLETE
whatNext = ACTION_RESTART

#
# С этого момента начинается специфическая для уровня инициализация, загрузка
# и игровой цикл
#

while whatNext in (ACTION_NEXT, ACTION_RESTART):
    glBeasts = list()
    glAnimatedEntities = dict()
    glTemporaryItems = list()

    glTreasuresCount = 0
    glCurrentLevel = load_level("01.lvl")
    character.glCurrentLevel = glCurrentLevel

    glStaticCanvas = pygame.Surface(glMainCanvas.get_size())
    show_layer(glStaticCanvas, glCurrentLevel[0], STATIC_BLOCKS)

    glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())

    running = True
    player_tick = 0
    beast_tick = 0

    while running:
        for event in pygame.event.get():
            if event.type == QUIT:
                whatNext = ACTION_QUIT
                game_over_reason = GAME_OVER_STUCK
                running = False

        # Erasing old creatures
        glMainCanvas.blit(glStaticCanvas, glStaticCanvas.get_rect())

        if player_tick == 0:
            collect_treasure()
            running = glPlayer.move(glBeasts, temporary_items=glTemporaryItems)
            if not running:
                game_over_reason = GAME_OVER_EATEN
            if glPlayer.oldpos[0] == 0 and running:
                game_over_reason = GAME_OVER_COMPLETE
                running = False

        # Drawing them in new positions
        # First -- non-movable level blocks with animation
        for animBlock in glAnimatedEntities.values():
            glMainCanvas.blit(animBlock.get_image(player_tick), get_screen_pos(animBlock.pos))

        # Then draw temporary items
        for tempBlock in glTemporaryItems:
            glMainCanvas.blit(tempBlock.get_image(player_tick), get_screen_pos(tempBlock.pos))
            if tempBlock.died:
                if tempBlock.underlay is not None:
                    if not respawn_beasts(tempBlock):
                        game_over_reason = GAME_OVER_STUCK
                        running = False
                    glCurrentLevel[0][tempBlock.pos[0]][tempBlock.pos[1]] = tempBlock.underlay
                del glTemporaryItems[glTemporaryItems.index(tempBlock)]

        # Then -- player
        glMainCanvas.blit(glPlayer.get_image(player_tick, STEP),
                          get_screen_pos(glPlayer.pos, PLAYER_ANIMATION_STEP, glPlayer.oldpos, player_tick))

        # And finally -- beasts
        for beast in glBeasts:
            if beast_tick == 0:
                # Метод возвращает ложь, если монстр оказался в позиции игрока
                # В нашей ситуации это означает съедение
                if not beast.move(glPlayer.pos, glBeasts):
                    running = False
                    game_over_reason = GAME_OVER_EATEN

            glMainCanvas.blit(beast.get_image(beast_tick, BEAST_STEP),
                              get_screen_pos(beast.pos, BEAST_ANIMATION_STEP, beast.oldpos, beast_tick))

        player_tick = player_tick + 1 if player_tick < STEP - 1 else 0
        beast_tick = beast_tick + 1 if beast_tick < BEAST_STEP - 1 else 0

        pygame.display.update()
        glClock.tick(FPS)

    whatNext = game_over(game_over_reason)

pygame.quit()
