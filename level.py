"""Level class for managin level data and do all other needful things for levels"""

import pygame
from pygame.locals import *
import CC
from glb import *
import block
import character


class Level:
    def __init__(self,
                 canvas=None,
                 filename=None,
                 player=None,
                 done_sound="level end.wav",
                 exit_appears_sound="exit.wav"):
        self.treasures_count = 0
        """Treasures in level"""

        self.level = list()
        """Layer for static tiles"""

        self.exit = list()
        """Layer for exit ladder"""

        self.beasts = list()
        """List of beasts in level"""

        self.animated_entities = dict()
        """List of animated things on map"""

        self.sprites = dict()
        """List of all static blocks. Just ordinary sprites"""

        self.level_end_sound = self.exit_appears_sound = None
        self.level_end_sound_filename = done_sound
        self.exit_appears_sound_filename = exit_appears_sound

        self.canvas: pygame.Surface = None
        self.static_image: pygame.Surface = None
        self.set_canvas(canvas)

        (player is None or filename is None) or self.load(filename, player)

    def set_canvas(self, canvas: pygame.Surface):
        self.canvas: pygame.Surface = canvas
        self.static_image: pygame.Surface = pygame.Surface(self.canvas.get_size()) if canvas is not None else None

    def init(self,
             done_sound=None,
             exit_appears_sound=None):
        solid = CC.BLOCKS["static"]
        for ch in solid:
            self.sprites[ch] = block.Block(solid[ch][0])
        self.level_end_sound = load_sound((self.level_end_sound_filename, done_sound)[done_sound is not None])
        self.exit_appears_sound = \
            load_sound((self.exit_appears_sound_filename, exit_appears_sound)[exit_appears_sound is not None])

    def load(self, filename, player):
        """Загружает игровой уровень. Создаёт всю необходимую структуру и динамические объекты.
            Уровень -- текстовый файл с буквами и символами, соответствующими структуре уровня.
            Если канва уже задана (не None), сразу рисует статичную картинку."""
        self.level.clear()
        self.exit.clear()
        self.beasts.clear()
        self.animated_entities.clear()
        self.treasures_count = 0

        with open(filename, 'r') as lvl_stream:
            row = 0

            animated = CC.BLOCKS["animated"]
            # Цикл по строкам файла
            for line in lvl_stream:
                static_line = list()
                exit_line = list()

                col = 0

                # Цикл по отдельным символам строки. Добавляем один символ, чтобы не писать в коде лишних проверок
                # на выход за границы массива
                for ch in line[0:CC.LEVEL_WIDTH + 1]:
                    exit_line.append(('.', ch)[ch in CC.EXIT_BLOCKS])

                    if ch in animated:
                        self.animated_entities[str(row) + ":" + str(col) + ":" + ch] = \
                            block.AnimatedBlock(animated[ch][1], [row, col],
                                                subfolder=animated[ch][0],
                                                animation_delay=to_number(animated[ch][2]),
                                                animation_pause=to_number(animated[ch][3]),
                                                hit_sound=load_sound(animated[ch][4]))
                        self.treasures_count += (ch in CC.TREASURE_BLOCKS)

                    if ch in CC.BEAST_BLOCKS:
                        monster = CC.BEAST_UNITS[ch]
                        self.beasts.append(character.Beast(monster, [row, col], subfolder=monster["folder"],
                                                           sounds=(None, None, load_sound(monster["dieSound"])),
                                                           idle_delay=monster["idle_delay"],
                                                           fall_delay=monster["fall_delay"],
                                                           step=CC.BEAST_STEP,
                                                           animation_step=CC.BEAST_ANIMATION_STEP))

                    # Персонаж может быть только один, поэтому данный алгоритм вернёт последнее найденное положение
                    if ch == 'I':
                        player.pos = [row, col]
                        player.oldpos = [row, col]

                    static_line.append(('.', ch)[ch in CC.MAPPED_BLOCKS and ch not in CC.EXIT_BLOCKS])
                    col += 1

                self.level.append(static_line)
                self.exit.append(exit_line)

                row += 1

        # Additional hidden line to avoid 'index out of range' errors
        self.level.append(static_line)

        self.prepare_static()
        # Return true if success
        return True

    # TODO Стоит переделать этот код, чтобы хранить уровень, как список спрайтов, которым уже заданы нужные координаты.
    # TODO Тогда отрисовка будет простым перебором спрайтов. Но это после выноса кода уровня в отдельный класс.
    def prepare_static(self, canvas: pygame.Surface = None) -> None:
        """Процедура подготовки статичной части уровня для отрисовки.
            Рисует статичные блоки на заранее подготовленной канве."""
        canvas = (self.static_image, canvas)[canvas is not None]
        if canvas is None:
            return
        for row, y in zip(self.level, range(CC.LEVEL_HEIGHT + 1)):
            for blk, x in zip(row, range(CC.LEVEL_WIDTH + 1)):
                # Используем метод get. Он не выдаёт ошибок, если индекс отсутствует, а возвращает None, что удобнее
                cur_block: block.Block = self.sprites.get(blk)
                if cur_block is not None:
                    cur_block.show(canvas, (x, y))

    def show_static(self, canvas: pygame.Surface = None):
        """Переносит заранее нарисованную статичную часть уровня на заданную канву."""
        canvas = (self.canvas, canvas)[canvas is not None]
        if canvas is None:
            return
        canvas.blit(self.static_image, self.static_image.get_rect())

    def show_animated(self, tick=0, canvas: pygame.Surface = None):
        """Отрисовка анимированных блоков уровня"""
        canvas = (self.canvas, canvas)[canvas is not None]
        if canvas is None:
            return
        for anim in self.animated_entities.values():
            anim.show(canvas, tick)

    def show_beasts(self, tick=0, canvas: pygame.Surface = None):
        """Рисует монстров уровня"""
        canvas = (self.canvas, canvas)[canvas is not None]
        if canvas is None:
            return
        for beast in self.beasts:
            beast.show(canvas, tick)

    def show(self, canvas: pygame.Surface = None, tick=0):
        """Рисует всю графику, ассоциированную с уровнем"""
        self.show_static(canvas)
        self.show_animated(canvas, tick)
        self.show_beasts(canvas, tick)

    def live(self, player, tick=0) -> bool:
        """Жизненный цикл уровня. Монстры бегут к игроку, кушают его и умирают, если попадут в ловушку.
            Монстры отрисовываются."""
        for beast in self.beasts:
            if tick == 0:
                # Метод возвращает ложь, если монстр оказался в позиции игрока
                # В нашей ситуации это означает съедение
                if not beast.move(player.pos, self.beasts):
                    return False
                else:
                    if self[beast.oldpos] in CC.DEADLY_BLOCKS:
                        key = str(beast.oldpos[0]) + ":" + str(beast.oldpos[1]) + ":" + str(self[beast.oldpos])
                        self.animated_entities[key].hit_sound is None or self.animated_entities[key].hit_sound.play()
                        beast.die()
            beast.show(self.canvas, tick)
        return True

    def collect_treasures(self, pos):
        """Проверка на подбор сокровища игроком. Если все сокровища собраны, добавляем выход с уровня"""
        for chb in CC.TREASURE_BLOCKS:
            key = str(pos[0]) + ":" + str(pos[1]) + ":" + chb
            if key in self.animated_entities:
                self.animated_entities[key].hit_sound is None or self.animated_entities[key].hit_sound.play()
                del self.animated_entities[key]
                self.treasures_count -= 1

                # Все сокровища собраны, готовим выход
                if self.treasures_count <= 0:
                    self.exit_appears_sound.play()
                    self.level = [[elem[elem[1] != '.'] for elem in zip(level_row[0], level_row[1])]
                                  for level_row in zip(self.level, self.exit)]
                    self.show_static()

    def __getitem__(self, item):
        return (None, self.level[item[0]][item[1]])[isinstance(item, (list, tuple))]

    def __setitem__(self, key, value):
        if isinstance(key, (list, tuple)):
            self.level[key[0]][key[1]] = value


glLevel = Level()
