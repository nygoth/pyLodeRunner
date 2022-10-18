""" Описание игровой структуры
 Какие блоки что значат, анимация и прочее
"""

from os import path
import json

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
"""Шагов анимации между ключевыми кадрами (в которых игра воспринимает управление)"""

TEMPO = 12
"""Количество ключевых кадров в секунду. Темп игры"""

BEAST_TEMPO = 8
"""Количество ключевых кадров для монстров. Их меньше. Они более медлительны.

    Для корректной работы BEAST_STEP * BEAST_TEMPO должно совпадать с FPS.
Поэтому надо подбирать значения тщательно, чтобы всё делилось нацело.
Если эти значения совпадают со значениями игрока, монстры перемещаются с его скоростью.
Изменяя эти значения можно добиться либо замедления, либо ускорения монстров относительно игрока.
"""
# Спрайты блоков структуры уровня
# Статичные блоки описываются картинкой и опциональной ссылкой на временный блок, который используется,
# если с этим элементом что-то делают. Например, игрок может разрушать какие-то блоки. Причём, можно запрограммировать
# для разных разрушаемых блоков разные временные блоки с анимацией разрушения/восстановления
BLOCKS = {"static": {'Z': ("block.png", "cracked"),
                     'H': ("ladder.png",),
                     'O': ("concrete_solid.png",),
                     '-': ("bar.png",),
                     '_': ("exit_bar.png",),
                     'P': ("exit_ladder.png",),
                     'U': ("block.png",),
                     '=': ("platform.png",),
                     },

          # Анимированные неподвижные блоки уровня.
          # [0] Тип: Treasure -- собираемые блоки
          #          Animation -- просто анимированный блок
          # [1] Список кадров
          # [2] Задержка между кадрами анимации относительно FPS, больше значение - выше задержка.
          #       Анимация воспроизводится от первого кадра к последнему и либо останавливается на указанное время.
          # [3] Пауза перед началом следующего цикла анимации
          #       Задержку и паузу можно указать простым числом, а можно интервалом (минимум, максимум, шаг),
          #       из которого выбираются (случайным образом) паузы между фазами анимации блока.
          #       Так отсутствует раздражающая синхронность в анимации однотипных блоков.
          # [4] Звук, который проигрывается, когда игрок или чудище попадают на этот блок (именно в клеточку
          #       с этим блоком, а не стоят сверху).
          "animated": {'+': ("Treasure",    # Collectible item
                             ("treasure0.png",
                              "treasure1.png",
                              "treasure2.png",
                              "treasure3.png",
                              "treasure4.png",
                              "treasure5.png",
                              "treasure6.png",
                              "treasure7.png",
                              ),
                             10,
                             (100, 400, 20),
                             "collect.wav",
                             ),
                       '*': ("Animation",   # Floor-mounted saw, half circle
                             ("saw0.png",
                              "saw1.png",
                              "saw2.png",
                              ),
                             (5, 20, 1),
                             0,
                             "saw.wav",
                             ),
                       '0': ("Animation",   # Standalone saw, full circle
                             ("fullsaw0.png",
                              "fullsaw1.png",
                              "fullsaw2.png",
                              ),
                             (5, 20, 1),
                             0,
                             "saw.wav",
                             ),
                       '/': ("Animation",  # Rope body right slope
                             ("Rope0.png",
                              "Rope1.png",
                              "Rope0.png",
                              "Rope2.png",
                              ),
                             20,
                             0,
                             None,
                             ),
                       '\\': ("Animation",  # Rope body left slope
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
                       'J': ("Animation",  # Rope tail (knot) left turned
                             ("Rope tail0.png",
                              "Rope tail1.png",
                              "Rope tail0.png",
                              "Rope tail2.png",
                              ),
                             20,
                             0,
                             None,
                             ),
                       'L': ("Animation",  # Rope tail (knot) right turned
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
                       },
          # Временные блоки уровня.
          # Возникают на какое-то время вместо какого-то постоянного блока. Меняют его вид и свойство.
          # Обычно, анимированны. Именованы, имена используются как ссылки на них.
          # [0] Анимация появления
          # [1] Анимация исчезания
          # [2] Время жизни
          "temporary": {"cracked": [("cracked_block0.png",
                                     "cracked_block1.png",
                                     "cracked_block2.png",
                                     "cracked_block3.png",
                                     "cracked_block4.png",
                                     "cracked_block5.png",
                                     "cracked_block6.png",
                                     ),
                                    ("cracked_block6.png",
                                     "cracked_block5.png",
                                     "cracked_block4.png",
                                     "cracked_block3.png",
                                     "cracked_block2.png",
                                     "cracked_block1.png",
                                     "cracked_block0.png",
                                     ),
                                    400,
                                    ],
                        }
          }

# Кадры анимации для спрайта игрока. Относительно каталога images\Player
PLAYER_UNIT = {"idle_delay": 300,
               "fall_delay": 100,
               "folder": "Player",
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
               }

# Кадры для анимации монстров. Относительно каталога images\Beast
BEAST_UNITS = {'X': {"folder": "Beast",
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

SOLID_BLOCKS = ('Z', 'O', '=')
"""Непроницаемые блоки"""
DESTRUCTABLE_BLOCKS = ('Z',)
"""Разрушаемые блоки"""
SUPPORT_BLOCKS = ('Z', 'O', 'H', 'P', 'T', '=')
"""Блоки, на которых можно стоять не падая"""
CARRY_BLOCKS = ('H', '-', '_', 'P', 'T', '/', '\\', 'J', 'L')
"""Блоки, на фоне которых можно стоять и не падать"""
HANG_BLOCKS = ('-', '_',)
"""Блоки, на которых можно висеть"""
CLIMB_BLOCKS = ('H', 'P', 'T', '/', '\\', 'J', 'L')
"""Блоки, по которым можно лезть вверх и вниз"""
VIRTUAL_BLOCKS = ('U',)
"""Блоки, которые мираж"""
TREASURE_BLOCKS = ('+',)
"""Блоки-сокровища"""
EXIT_BLOCKS = ('P', '_',)
"""Блоки, появляющиеся, когда все сокровища собраны"""
BEAST_BLOCKS = ('X',)
"""Символы, помечающие монстров"""
DEADLY_BLOCKS = ('*', '~', '0',)
"""Смертельные блоки. Игрок и монстры умирают, находясь на них"""

MAPPED_BLOCKS = SOLID_BLOCKS + SUPPORT_BLOCKS + CARRY_BLOCKS + VIRTUAL_BLOCKS + DEADLY_BLOCKS
"""Блоки, хранящиеся в карте проверки"""


def init_config(game_state, config, defaults: tuple = (-1, -1)):
    """Загрузка или установка конфигурации по умолчанию и создание файлов конфигурации"""
    global BLOCKS, PLAYER_UNIT, BLOCK_WIDTH
    global BEAST_UNITS, LEVEL_HEIGHT, LEVEL_WIDTH, STEP, TEMPO, BEAST_TEMPO
    global SOLID_BLOCKS, DESTRUCTABLE_BLOCKS, SUPPORT_BLOCKS, CARRY_BLOCKS, HANG_BLOCKS, CLIMB_BLOCKS
    global VIRTUAL_BLOCKS, TREASURE_BLOCKS, EXIT_BLOCKS, BEAST_BLOCKS, DEADLY_BLOCKS, MAPPED_BLOCKS

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
            config.get("Blocks", "BLOCKS", fallback=json.dumps(BLOCKS)).replace("'", "\""))

        PLAYER_UNIT = json.loads(
            config.get("Characters", "PLAYER UNIT", fallback=json.dumps(PLAYER_UNIT)).replace("'", "\""))
        BEAST_UNITS = json.loads(
            config.get("Characters", "BEAST UNITS", fallback=json.dumps(BEAST_UNITS)).replace("'", "\""))

        BLOCK_WIDTH = int(config.get("Geometry", "BLOCK WIDTH", fallback=BLOCK_WIDTH))
        LEVEL_WIDTH = int(config.get("Geometry", "LEVEL WIDTH", fallback=LEVEL_WIDTH))
        LEVEL_HEIGHT = int(config.get("Geometry", "LEVEL HEIGHT", fallback=LEVEL_HEIGHT))

        STEP = int(config.get("Game", "STEP", fallback=STEP))
        TEMPO = int(config.get("Game", "TEMPO", fallback=TEMPO))
        BEAST_TEMPO = int(config.get("Game", "BEAST TEMPO", fallback=BEAST_TEMPO))

        SOLID_BLOCKS = json.loads(
            config.get("Structure", "SOLID BLOCKS", fallback=json.dumps(SOLID_BLOCKS)).replace("'", "\""))
        DESTRUCTABLE_BLOCKS = json.loads(
            config.get("Structure", "DESTRUCTABLE BLOCKS", fallback=json.dumps(DESTRUCTABLE_BLOCKS)).replace("'", "\""))
        SUPPORT_BLOCKS = json.loads(
            config.get("Structure", "SUPPORT BLOCKS", fallback=json.dumps(SUPPORT_BLOCKS)).replace("'", "\""))
        CARRY_BLOCKS = json.loads(
            config.get("Structure", "CARRY BLOCKS", fallback=json.dumps(CARRY_BLOCKS)).replace("'", "\""))
        HANG_BLOCKS = json.loads(
            config.get("Structure", "HANG BLOCKS", fallback=json.dumps(HANG_BLOCKS)).replace("'", "\""))
        CLIMB_BLOCKS = json.loads(
            config.get("Structure", "CLIMB BLOCKS", fallback=json.dumps(CLIMB_BLOCKS)).replace("'", "\""))
        VIRTUAL_BLOCKS = json.loads(
            config.get("Structure", "VIRTUAL BLOCKS", fallback=json.dumps(VIRTUAL_BLOCKS)).replace("'", "\""))
        TREASURE_BLOCKS = json.loads(
            config.get("Structure", "TREASURE BLOCKS", fallback=json.dumps(TREASURE_BLOCKS)).replace("'", "\""))
        EXIT_BLOCKS = json.loads(
            config.get("Structure", "EXIT BLOCKS", fallback=json.dumps(EXIT_BLOCKS)).replace("'", "\""))
        BEAST_BLOCKS = json.loads(
            config.get("Structure", "BEAST BLOCKS", fallback=json.dumps(BEAST_BLOCKS)).replace("'", "\""))
        DEADLY_BLOCKS = json.loads(
            config.get("Structure", "DEADLY BLOCKS", fallback=json.dumps(DEADLY_BLOCKS)).replace("'", "\""))

        MAPPED_BLOCKS = SOLID_BLOCKS + SUPPORT_BLOCKS + CARRY_BLOCKS + VIRTUAL_BLOCKS + DEADLY_BLOCKS
    else:
        config.add_section("Game")
        config.add_section("Geometry")
        config.add_section("Characters")
        config.add_section("Blocks")
        config.add_section("Structure")

        config["Game"]["STEP"] = str(STEP)
        config["Game"]["TEMPO"] = str(TEMPO)
        config["Game"]["BEAST TEMPO"] = str(BEAST_TEMPO)
        config["Geometry"]["BLOCK WIDTH"] = str(BLOCK_WIDTH)
        config["Geometry"]["LEVEL WIDTH"] = str(LEVEL_WIDTH)
        config["Geometry"]["LEVEL HEIGHT"] = str(LEVEL_HEIGHT)
        config["Blocks"]["BLOCKS"] = json.dumps(BLOCKS)
        config["Characters"]["PLAYER UNIT"] = json.dumps(PLAYER_UNIT)
        config["Characters"]["BEAST UNITS"] = json.dumps(BEAST_UNITS)
        config["Structure"]["SOLID BLOCKS"] = json.dumps(SOLID_BLOCKS)
        config["Structure"]["DESTRUCTABLE BLOCKS"] = json.dumps(DESTRUCTABLE_BLOCKS)
        config["Structure"]["SUPPORT BLOCKS"] = json.dumps(SUPPORT_BLOCKS)
        config["Structure"]["CARRY BLOCKS"] = json.dumps(CARRY_BLOCKS)
        config["Structure"]["HANG BLOCKS"] = json.dumps(HANG_BLOCKS)
        config["Structure"]["CLIMB BLOCKS"] = json.dumps(CLIMB_BLOCKS)
        config["Structure"]["VIRTUAL BLOCKS"] = json.dumps(VIRTUAL_BLOCKS)
        config["Structure"]["TREASURE BLOCKS"] = json.dumps(TREASURE_BLOCKS)
        config["Structure"]["EXIT BLOCKS"] = json.dumps(EXIT_BLOCKS)
        config["Structure"]["BEAST BLOCKS"] = json.dumps(BEAST_BLOCKS)
        config["Structure"]["DEADLY BLOCKS"] = json.dumps(DEADLY_BLOCKS)

        with open(GAME_CONFIG_FILE, "w") as config_file:
            config.write(config_file)

    return current_level, current_song
