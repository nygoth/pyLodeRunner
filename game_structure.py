# Описание игровой структуры
# Какие блоки что значат, анимация и прочее

from os import path
import character
import json

from block import BLOCK_WIDTH

# Define global game settings like blocks info, animation etc
GAME_CONFIG_FILE = path.join(path.dirname(__file__), "structure.ini")

# Define game state file. This is storage for values, that changes during game, like current level, music track etc
GAME_STATE_FILE = path.join(path.dirname(__file__), "state.ini")

# Размеры спрайтов и уровня в целом
LEVEL_WIDTH = 42
LEVEL_HEIGHT = 22

STEP = 24  # Шагов анимации между ключевыми кадрами (в которых игра воспринимает управление)
TEMPO = 12  # Количество ключевых кадров в секунду. Темп игры

# Для корректной работы BEAST_STEP * BEAST_TEMPO должно совпадать с FPS
# Поэтому надо подбирать значения тщательно, чтобы всё делилось нацело
# Если эти значения совпадают со значениями игрока, монстры перемещаются с его скоростью
# Изменяя эти значения можно добиться либо замедления, либо ускорения монстров относительно игрока
BEAST_TEMPO = 8  # У монстров ключевых кадров меньше. Они более медлительны

# Спрайты статичных блоков структуры уровня
STATIC_BLOCKS_FILES = {'Z': "block.png",
                       'H': "ladder.png",
                       'O': "concrete_solid.png",
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

CRACKED_BLOCK_IMAGES = (("cracked_block0.png",
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
                         ))
CRACKED_BLOCK_LIFETIME = 400

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

SOLID_BLOCKS = ('Z', 'O', '=')  # Непроницаемые блоки
DESTRUCTABLE_BLOCKS = ('Z',)  # Разрушаемые блоки
SUPPORT_BLOCKS = ('Z', 'O', 'H', 'P', 'T', '=')  # Блоки, на которых можно стоять не падая
CARRY_BLOCKS = ('H', '-', '_', 'P', 'T', '/', '\\', 'J', 'L')  # Блоки, можно стоять на их фоне и не падать
HANG_BLOCKS = ('-', '_',)  # Блоки, на которых можно висеть
CLIMB_BLOCKS = ('H', 'P', 'T', '/', '\\', 'J', 'L')  # Блоки, по которым можно лезть вверх и вниз
VIRTUAL_BLOCKS = ('U',)  # Блоки, которые мираж
TREASURE_BLOCKS = ('+',)  # Блоки-сокровища
EXIT_BLOCKS = ('P', '_',)  # Блоки, появляющиеся, когда все сокровища собраны
BEAST_BLOCKS = ('X',)  # Символы, помечающие монстров
DEADLY_BLOCKS = ('*', '~', '0',)  # Смертельные блоки. Игрок и монстры умирают, находясь на них

# Блоки, хранящиеся в карте проверки
MAPPED_BLOCKS = SOLID_BLOCKS + SUPPORT_BLOCKS + CARRY_BLOCKS + VIRTUAL_BLOCKS + DEADLY_BLOCKS


def init_config(game_state, config, defaults: tuple = (-1, -1)):
    global STATIC_BLOCKS_FILES, ANIMATED_BLOCKS, PLAYER_UNIT, BLOCK_WIDTH
    global BEAST_UNITS, LEVEL_HEIGHT, LEVEL_WIDTH, STEP, TEMPO, BEAST_TEMPO

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
        STATIC_BLOCKS_FILES = json.loads(
            config.get("Blocks", "STATIC BLOCKS FILES", fallback=json.dumps(STATIC_BLOCKS_FILES)).replace("'", "\""))
        ANIMATED_BLOCKS = json.loads(
            config.get("Blocks", "ANIMATED BLOCKS", fallback=json.dumps(ANIMATED_BLOCKS)).replace("'", "\""))

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
            config.get("Structure", "TREASURE BLOCKS", fallback=json.dumps(character.TREASURE_BLOCKS)).replace("'",
                                                                                                               "\""))
        character.EXIT_BLOCKS = json.loads(
            config.get("Structure", "EXIT BLOCKS", fallback=json.dumps(character.EXIT_BLOCKS)).replace("'", "\""))
        character.BEAST_BLOCKS = json.loads(
            config.get("Structure", "BEAST BLOCKS", fallback=json.dumps(character.BEAST_BLOCKS)).replace("'", "\""))
        character.DEADLY_BLOCKS = json.loads(
            config.get("Structure", "DEADLY BLOCKS", fallback=json.dumps(character.DEADLY_BLOCKS)).replace("'", "\""))
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
        config["Blocks"]["STATIC BLOCKS FILES"] = json.dumps(STATIC_BLOCKS_FILES)
        config["Blocks"]["ANIMATED BLOCKS"] = json.dumps(ANIMATED_BLOCKS)
        config["Characters"]["PLAYER UNIT"] = json.dumps(PLAYER_UNIT)
        config["Characters"]["BEAST UNITS"] = json.dumps(BEAST_UNITS)
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

        with open(GAME_CONFIG_FILE, "w") as config_file:
            config.write(config_file)

    return current_level, current_song
