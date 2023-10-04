""" Описание игровой структуры
 Какие блоки что значат, анимация и прочее
"""

from os import path
import json
from glb import *


def __fill_level_structure_constants():
    global PLAYER_UNIT, BEAST_UNITS, SOLID_BLOCKS, DESTRUCTABLE_BLOCKS, SUPPORT_BLOCKS, CARRY_BLOCKS, HANG_BLOCKS
    global CLIMB_BLOCKS, VIRTUAL_BLOCKS, TREASURE_BLOCKS, EXIT_BLOCKS, BEAST_BLOCKS, DEADLY_BLOCKS, MAPPED_BLOCKS
    global BLOCKS

    PLAYER_UNIT = BLOCKS["characters"]["I"]
    BEAST_UNITS = get_subset_by_type(BLOCKS["characters"], "beast")
    SOLID_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                           "solid"))  # ('Z', 'O', '=')
    DESTRUCTABLE_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                                  "destructable"))  # ('Z',)
    SUPPORT_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                             "support"))  # ('Z', 'O', 'H', 'P', 'T', '=')
    CARRY_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                           "carry"))  # ('H', '-', '_', 'P', 'T', '/', '\\', 'J', 'L')
    HANG_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                          "hang"))  # ('-', '_',)
    CLIMB_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                           "climb"))  # ('H', 'P', 'T', '/', '\\', 'J', 'L')
    VIRTUAL_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                             "virtual"))  # ('U',)
    TREASURE_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                              "treasure"))  # ('+',)
    EXIT_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                          "exit"))  # ('P', '_',)
    BEAST_BLOCKS = list(get_subset_by_type(BLOCKS["characters"], "beast"))  # ('X',)
    DEADLY_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                            "deadly"))  # ('*', '~', '0',)
    MAPPED_BLOCKS = list(get_subset_by_type({**BLOCKS["static"], **BLOCKS["animated"], **BLOCKS["characters"]},
                                            "mapped"))


# Статусы завершения игры
GAME_OVER_NOT_OVER = 0  # Игра продолжается
GAME_OVER_COMPLETE = 1  # Уровень пройден
GAME_OVER_EATEN = 2  # Игрока съели
GAME_OVER_STUCK = 3  # Игрок застрял в разрушенном блоке
GAME_OVER_KILLED = 4  # Игрок убит в смертельном блоке
GAME_OVER_USER_END = 100  # Пользователь хочет закрыть программу

GAME_CONFIG_FILE = path.join(path.dirname(__file__), "structure.ini")
"""Define global game settings like blocks info, animation etc"""

GAME_STATE_FILE = path.join(path.dirname(__file__), "state.ini")
"""Define game state file. This is storage for values, that changes during game, like current level, music track etc"""

BLOCK_WIDTH = 38
"""Размер спрайтов"""

LEVEL_WIDTH = 42
"""Ширина уровня"""

LEVEL_HEIGHT = 22
"""Высота уровня"""

STEP = 24
"""Шагов анимации между ключевыми кадрами (в которых игра воспринимает управление).
Больше значение -- медленнее играю"""

TEMPO = 12
"""Количество ключевых кадров в секунду. Темп игры. Больше значение, быстрее игра реагирует на управление."""

BEAST_TEMPO = 8
"""Количество ключевых кадров для монстров. Их меньше. Они более медлительны.

    Для корректной работы BEAST_STEP * BEAST_TEMPO должно совпадать с FPS.
Поэтому надо подбирать значения тщательно, чтобы всё делилось нацело.
Если эти значения совпадают со значениями игрока, монстры перемещаются с его скоростью.
Изменяя эти значения можно добиться либо замедления, либо ускорения монстров относительно игрока.
"""

FPS = TEMPO * STEP
BEAST_STEP = int(FPS / BEAST_TEMPO)
BEAST_ANIMATION_STEP = BLOCK_WIDTH / BEAST_STEP  # Смещение объекта в пикселах за один шаг анимации
PLAYER_ANIMATION_STEP = BLOCK_WIDTH / STEP  # Смещение объекта в пикселах за один шаг анимации

# Спрайты блоков структуры уровня.
# Есть у следующие типы блоков:
#   static     -- статичные неанимированные блоки с разными свойствами;
#   animated   -- статичные анимированные блоки;
#   temporary  -- временные анимированные спрайты. Используются для анимации различных событий.
#   characters -- спрайты персонажей. Игрока и монстров.
# Статичные блоки описываются типами, картинкой и опциональной ссылкой на временный блок, который используется
# (рисуется поверх), если с этим элементом что-то делают. Например, игрок может разрушать какие-то блоки.
# Причём, можно запрограммировать для разных разрушаемых блоков разные временные блоки с анимацией
# разрушения/восстановления.
BLOCKS = {"static": {'Z': {"type": ("solid", "support", "destructable", "mapped"),
                           "folder": "Static",
                           "img": "block.png",
                           "overlay": "cracked"
                           },
                     'H': {"type": ("support", "carry", "climb", "mapped"),
                           "folder": "Static",
                           "img": "ladder.png"
                           },
                     'O': {"type": ("solid", "support", "mapped"),
                           "folder": "Static",
                           "img": "concrete_solid.png"
                           },
                     '-': {"type": ("hang", "carry", "mapped"),
                           "folder": "Static",
                           "img": "bar.png"
                           },
                     '_': {"type": ("carry", "hang", "exit", "mapped"),
                           "folder": "Static",
                           "img": "exit_bar.png"
                           },
                     'P': {"type": ("support", "climb", "carry", "exit", "mapped"),
                           "folder": "Static",
                           "img": "exit_ladder.png"
                           },
                     'U': {"type": ("virtual", "mapped"),
                           "folder": "Static",
                           "img": "block.png"
                           },
                     '=': {"type": ("solid", "support", "mapped"),
                           "folder": "Static",
                           "img": "platform.png"
                           },
                     },

          # Анимированные неподвижные блоки уровня.
          # Тип: treasure -- собираемые блоки
          #          иное     -- просто анимированный блок
          # [animation][idle] Список кадров
          # [animation][speed] Задержка между кадрами анимации относительно FPS, больше значение - выше задержка.
          #       Анимация воспроизводится от первого кадра к последнему и либо останавливается на указанное время.
          # [animation][delay] Пауза перед началом следующего цикла анимации
          #       Задержку и паузу можно указать простым числом, а можно интервалом (минимум, максимум, шаг),
          #       из которого выбираются (случайным образом) паузы между фазами анимации блока.
          #       Так отсутствует раздражающая синхронность в анимации однотипных блоков.
          # [sounds][over] Звук, который проигрывается, когда игрок или чудище попадают на этот блок (именно в клеточку
          #       с этим блоком, а не стоят сверху).
          "animated": {'+': {"type": ("treasure", ),    # Collectible item
                             "folder": "Treasure",
                             "animation": {"idle": ("treasure0.png",
                                                    "treasure1.png",
                                                    "treasure2.png",
                                                    "treasure3.png",
                                                    "treasure4.png",
                                                    "treasure5.png",
                                                    "treasure6.png",
                                                    "treasure7.png",
                                                   ),
                                           "speed": 10,
                                           "delay": (100, 400, 20),
                                          },
                             "sounds": {"over": "collect.wav"},
                             },
                       '*': {"type": ("deadly", "mapped"),   # Floor-mounted saw, half circle
                             "folder": "Animation",
                             "animation": {"idle": ("saw0.png",
                                                    "saw1.png",
                                                    "saw2.png",
                                                   ),
                                           "speed": (5, 20, 1),
                                           "delay": 0,
                                          },
                             "sounds": {"over": "saw.wav"},
                            },
                       '0': {"type": ("deadly", "mapped"),   # Standalone saw, full circle
                             "folder": "Animation",
                             "animation": {"idle": ("fullsaw0.png",
                                                    "fullsaw1.png",
                                                    "fullsaw2.png",
                                                   ),
                                           "speed": (5, 20, 1),
                                           "delay": 0,
                                          },
                             "sounds": {"over": "saw.wav"},
                            },
                       '/': {"type": ("carry", "climb", "mapped"),  # Rope body right slope
                             "folder": "Animation",
                             "animation": {"idle": ("Rope0.png",
                                                    "Rope1.png",
                                                    "Rope0.png",
                                                    "Rope2.png",
                                                   ),
                                           "speed": 20,
                                           "delay": 0,
                                          },
                             "sounds": None,
                            },
                       '\\': {"type": ("carry", "climb", "mapped"),  # Rope body left slope
                              "folder": "Animation",
                              "animation": {"idle": ("Rope0.png",
                                                     "Rope2.png",
                                                     "Rope0.png",
                                                     "Rope1.png",
                                                    ),
                                            "speed": 20,
                                            "delay": 0,
                                           },
                              "sounds": None,
                             },
                       'T': {"type": ("support", "carry", "climb", "mapped"),  # Rope head (hook plate)
                             "folder": "Animation",
                             "animation": {"idle": ("Rope base0.png",
                                                    "Rope base1.png",
                                                    "Rope base0.png",
                                                    "Rope base2.png",
                                                   ),
                                           "speed": 20,
                                           "delay": 0,
                                          },
                             "sounds": None,
                            },
                       'J': {"type": ("carry", "climb", "mapped"),  # Rope tail (knot) left turned
                             "folder": "Animation",
                             "animation": {"idle": ("Rope tail0.png",
                                                    "Rope tail1.png",
                                                    "Rope tail0.png",
                                                    "Rope tail2.png",
                                                   ),
                                           "speed": 20,
                                           "delay": 0,
                                          },
                             "sounds": None,
                            },
                       'L': {"type": ("carry", "climb", "mapped"),  # Rope tail (knot) right turned
                             "folder": "Animation",
                             "animation": {"idle": ("Rope tail0.png",
                                                    "Rope tail2.png",
                                                    "Rope tail0.png",
                                                    "Rope tail1.png",
                                                   ),
                                           "speed": 20,
                                           "delay": 0,
                                           },
                             "sounds": None,
                             },
                       '~': {"type": ("deadly", "mapped"),  # Lava
                             "folder": "Animation",
                             "animation": {"idle": ("Lava0.png",
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
                                           "speed": (15, 30, 1),
                                           "delay": (1, 20, 1),
                                           },
                             "sounds": {"over": "burned.wav"},
                             },
                       },
          # Временные блоки уровня.
          # Возникают на какое-то время вместо какого-то постоянного блока. Меняют его вид и свойство.
          # Обычно, анимированны. Именованы, имена используются как ссылки на них.
          # [animation][appear] Анимация появления
          # [animation][disappear] Анимация исчезания
          # [lifetime] Время жизни
          "temporary": {"cracked": {"type": ("deadly", ),
                                    "folder": "Animation",
                                    "lifetime": 400,
                                    "animation": {"appear": ("cracked_block0.png",
                                                             "cracked_block1.png",
                                                             "cracked_block2.png",
                                                             "cracked_block3.png",
                                                             "cracked_block4.png",
                                                             "cracked_block5.png",
                                                             "cracked_block6.png",
                                                            ),
                                                  "disappear": ("cracked_block6.png",
                                                                "cracked_block5.png",
                                                                "cracked_block4.png",
                                                                "cracked_block3.png",
                                                                "cracked_block2.png",
                                                                "cracked_block1.png",
                                                                "cracked_block0.png",
                                                                ),
                                                  },
                                    },
                        },

          # Спрайт игрока. Относительно каталога images\Player
          # [idle_delay] Задержка анимации в состоянии ожидания
          # [fall_delay] Задержка анимации в состоянии падения
          "characters": {"I": {"type": ("player",),
                               "folder": "Player",
                               "idle_delay": 300,
                               "fall_delay": 100,
                               "sounds": {"steps": "footsteps.wav",
                                          "attack": "attack.wav",
                                          "eaten": "eaten.wav",
                                          "killed": "beast die.wav",
                                          "stuck": "beast die.wav",
                                          "leave": "user end.wav"
                                          },
                               "animation": {"idle": ("player_idle0.png",
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
                                                             )
                                             }
                               },

                         # Кадры для анимации монстров. Относительно каталога images\Beast
                         'X': {"type": ("beast", "npc"),
                               "folder": "Beast",
                               "idle_delay": 250,
                               "fall_delay": 100,
                               "sounds": {"death": "beast die.wav"},
                               "animation": {"idle": ("zombie_idle0.png",
                                                      "zombie_idle1.png",
                                                      "zombie_idle0.png",
                                                      "zombie_idle2.png",),
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
                                                                 "zombie_hang7.png",),
                                             "climb_up": ("zombie_climb0.png",
                                                          "zombie_climb1.png",
                                                          "zombie_climb2.png",
                                                          "zombie_climb3.png",
                                                          "zombie_climb4.png",
                                                          "zombie_climb5.png",
                                                          "zombie_climb6.png",
                                                          "zombie_climb7.png",),
                                             },
                               },
                         },
          }

PLAYER_UNIT = dict()
BEAST_UNITS = dict()

SOLID_BLOCKS = list()
"""Непроницаемые блоки"""
DESTRUCTABLE_BLOCKS = list()
"""Разрушаемые блоки"""
SUPPORT_BLOCKS = list()
"""Блоки, на которых можно стоять не падая"""
CARRY_BLOCKS = list()
"""Блоки, на фоне которых можно стоять и не падать"""
HANG_BLOCKS = list()
"""Блоки, на которых можно висеть"""
CLIMB_BLOCKS = list()
"""Блоки, по которым можно лезть вверх и вниз"""
VIRTUAL_BLOCKS = list()
"""Блоки, которые мираж"""
TREASURE_BLOCKS = list()
"""Блоки-сокровища"""
EXIT_BLOCKS = list()
"""Блоки, появляющиеся, когда все сокровища собраны"""
BEAST_BLOCKS = list()
"""Символы, помечающие монстров"""
DEADLY_BLOCKS = list()
"""Смертельные блоки. Игрок и монстры умирают, находясь на них"""
MAPPED_BLOCKS = list()
"""Блоки, хранящиеся в карте проверки"""

__fill_level_structure_constants()


def init_config(game_state, config, defaults: tuple = (-1, -1)):
    """Загрузка или установка конфигурации по умолчанию и создание файлов конфигурации"""
    global BLOCKS, BLOCK_WIDTH, FPS, BEAST_STEP, PLAYER_ANIMATION_STEP
    global LEVEL_HEIGHT, LEVEL_WIDTH, STEP, TEMPO, BEAST_TEMPO, BEAST_ANIMATION_STEP

    (current_level, current_song) = defaults

    if path.exists(GAME_STATE_FILE):
        game_state.read(GAME_STATE_FILE)
        current_level = int(game_state.get("Progress", "current level", fallback=defaults[0] + 1)) - 1
        current_song = int(game_state.get("Progress", "current song", fallback=defaults[1] + 1)) - 1
    else:
        game_state.add_section("Progress")
        game_state["Progress"]["current level"] = str(defaults[0])
        game_state["Progress"]["current song"] = str(defaults[1])

    if path.exists(GAME_CONFIG_FILE):
        config.read(GAME_CONFIG_FILE)
        BLOCKS = json.loads(
            config.get("Entities", "BLOCKS", fallback=json.dumps(BLOCKS)).replace("'", "\""))

        BLOCK_WIDTH = int(config.get("Geometry", "BLOCK WIDTH", fallback=BLOCK_WIDTH))
        LEVEL_WIDTH = int(config.get("Geometry", "LEVEL WIDTH", fallback=LEVEL_WIDTH))
        LEVEL_HEIGHT = int(config.get("Geometry", "LEVEL HEIGHT", fallback=LEVEL_HEIGHT))

        STEP = int(config.get("Game", "STEP", fallback=STEP))
        TEMPO = int(config.get("Game", "TEMPO", fallback=TEMPO))
        BEAST_TEMPO = int(config.get("Game", "BEAST TEMPO", fallback=BEAST_TEMPO))

        __fill_level_structure_constants()

        FPS = TEMPO * STEP
        BEAST_STEP = int(FPS / BEAST_TEMPO)
        BEAST_ANIMATION_STEP = BLOCK_WIDTH / BEAST_STEP  # Смещение объекта в пикселах за один шаг анимации
        PLAYER_ANIMATION_STEP = BLOCK_WIDTH / STEP  # Смещение объекта в пикселах за один шаг анимации
    else:
        config.add_section("Game")
        config.add_section("Geometry")
        config.add_section("Entities")

        config["Game"]["STEP"] = str(STEP)
        config["Game"]["TEMPO"] = str(TEMPO)
        config["Game"]["BEAST TEMPO"] = str(BEAST_TEMPO)
        config["Geometry"]["BLOCK WIDTH"] = str(BLOCK_WIDTH)
        config["Geometry"]["LEVEL WIDTH"] = str(LEVEL_WIDTH)
        config["Geometry"]["LEVEL HEIGHT"] = str(LEVEL_HEIGHT)
        config["Entities"]["BLOCKS"] = json.dumps(BLOCKS, indent='\t')

        with open(GAME_CONFIG_FILE, "w") as config_file:
            config.write(config_file)

    return current_level, current_song


