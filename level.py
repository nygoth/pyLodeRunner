"""Level class for managing level data and do all other needful things for levels"""

import pygame
import CC
from glb import *
import block
import character


class Level:
    def __init__(self,
                 canvas=None,
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

        self.player = None
        """Player character"""

        self.animated_entities = dict()
        """List of animated things on map"""

        self.sprites = dict()
        """List of all static blocks. Just ordinary sprites"""

        self.temporary_items = list()
        """List of short-lived items for game events animation"""

        self.level_end_sound = self.exit_appears_sound = None
        self.level_end_sound_filename = done_sound
        self.exit_appears_sound_filename = exit_appears_sound

        self.canvas: pygame.Surface = None
        self.static_image: pygame.Surface = None
        self.set_canvas(canvas)
        canvas is None or self.init(done_sound, exit_appears_sound)

    def set_canvas(self, canvas: pygame.Surface):
        """Set the drawing canvas for level. It can be called internally in constructor or separately,
            if drawing surface changed."""
        self.canvas: pygame.Surface = canvas
        self.static_image: pygame.Surface = pygame.Surface(self.canvas.get_size()) if canvas is not None else None

    def init(self, done_sound=None, exit_appears_sound=None):
        """Initialize object. This must be called after pygame init and screen canvas creation.
            So, this is called from construcrtor internally, if canvas provided, or must be called
            separately and explicitly after "set_canvas" call."""
        solid = CC.BLOCKS["static"]
        self.sprites = {ch: block.Block(solid[ch]["img"], subfolder=solid[ch]["folder"]) for ch in solid}
        self.level_end_sound = load_sound((self.level_end_sound_filename, done_sound)[done_sound is not None])
        self.exit_appears_sound = \
            load_sound((self.exit_appears_sound_filename, exit_appears_sound)[exit_appears_sound is not None])
        self.player = character.Player(CC.PLAYER_UNIT["animation"], self,
                                       subfolder=CC.PLAYER_UNIT["folder"],
                                       sounds=(load_sound(CC.PLAYER_UNIT["sounds"]["steps"]),
                                               load_sound(CC.PLAYER_UNIT["sounds"]["attack"]),
                                               {CC.GAME_OVER_EATEN: load_sound(CC.PLAYER_UNIT["sounds"]["eaten"]),
                                                CC.GAME_OVER_KILLED: load_sound(CC.PLAYER_UNIT["sounds"]["killed"]),
                                                CC.GAME_OVER_STUCK: load_sound(CC.PLAYER_UNIT["sounds"]["stuck"]),
                                                CC.GAME_OVER_USER_END: load_sound(CC.PLAYER_UNIT["sounds"]["leave"]),
                                                }),
                                       idle_delay=CC.PLAYER_UNIT["idle_delay"],
                                       fall_delay=CC.PLAYER_UNIT["fall_delay"],
                                       step=CC.STEP,
                                       animation_step=CC.PLAYER_ANIMATION_STEP)

    def load(self, filename):
        """Загружает игровой уровень. Создаёт всю необходимую структуру и динамические объекты.
            Уровень -- текстовый файл с буквами и символами, соответствующими структуре уровня.
            Если канва уже задана (не None), сразу рисует статичную картинку."""
        self.level.clear()
        self.exit.clear()
        self.beasts.clear()
        self.animated_entities.clear()
        self.temporary_items.clear()
        self.treasures_count = 0

        with open(filename, 'r') as lvl_stream:
            animated = CC.BLOCKS["animated"]
            # Цикл по строкам файла
            for row, line in enumerate(lvl_stream):
                static_line = list()
                exit_line = list()

                # Цикл по отдельным символам строки. Добавляем один символ, чтобы не писать в коде лишних проверок
                # на выход за границы массива
                for col, ch in enumerate(line[0:CC.LEVEL_WIDTH + 1]):
                    exit_line.append(('.', ch)[ch in CC.EXIT_BLOCKS])
                    static_line.append(('.', ch)[ch in CC.MAPPED_BLOCKS and ch not in CC.EXIT_BLOCKS])

                    if ch in animated:
                        self.animated_entities[str([row, col]) + ":" + ch] = \
                            block.AnimatedBlock(animated[ch]["animation"]["idle"], [row, col],
                                                subfolder=animated[ch]["folder"],
                                                animation_delay=to_number(animated[ch]["animation"]["speed"]),
                                                animation_pause=to_number(animated[ch]["animation"]["delay"]),
                                                hit_sound=load_sound(animated[ch]["sounds"]["over"])
                                                                if animated[ch]["sounds"] is not None else None)
                        self.treasures_count += (ch in CC.TREASURE_BLOCKS)

                    if ch in CC.BEAST_BLOCKS:
                        monster = CC.BEAST_UNITS[ch]
                        self.beasts.append(character.Beast(monster["animation"], self, [row, col],
                                                           subfolder=monster["folder"],
                                                           sounds=(None, None, load_sound(monster["sounds"]["death"])),
                                                           idle_delay=monster["idle_delay"],
                                                           fall_delay=monster["fall_delay"],
                                                           step=CC.BEAST_STEP,
                                                           animation_step=CC.BEAST_ANIMATION_STEP))

                    # Персонаж может быть только один, поэтому данный алгоритм вернёт последнее найденное положение
                    if ch == 'I':
                        self.player.pos, self.player.oldpos = [[row, col]] * 2

                self.level.append(static_line)
                self.exit.append(exit_line)

        # Additional hidden line to avoid 'index out of range' errors
        self.level.append(static_line)

        self.prepare_static()
        # Return true if success
        return True

    def prepare_static(self, canvas: pygame.Surface = None) -> None:
        """Процедура подготовки статичной части уровня для отрисовки.
            Рисует статичные блоки на заранее подготовленной канве."""
        canvas = (self.static_image, canvas)[canvas is not None]
        if canvas is None:
            return

        # Clean game screen
        canvas.fill((0, 0, 0))
        for y, row in enumerate(self.level):
            for x, blk in enumerate(row):
                # Используем метод get. Он не выдаёт ошибок, если индекс отсутствует, а возвращает None, что удобнее
                cur_block: block.Block = self.sprites.get(blk)
                cur_block is None or cur_block.show(canvas, [y, x])

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

    def show_player(self, tick=0, canvas: pygame.Surface = None):
        """Рисует монстров уровня"""
        canvas = (self.canvas, canvas)[canvas is not None]
        if canvas is None:
            return
        self.player.show(canvas, tick)

    def live(self, player_tick=0, beast_tick=0) -> int:
        """Жизненный цикл уровня. Монстры бегут к игроку, кушают его и умирают, если попадут в ловушку.
            Монстры отрисовываются."""

        live_result = CC.GAME_OVER_NOT_OVER
        # =====================
        # Erasing old animation
        # =====================
        self.show_static()

        # =======================================
        # Do player movement and collisions check
        # =======================================
        if not player_tick:
            if not self.player.move(self.beasts, self.temporary_items):
                live_result = CC.GAME_OVER_EATEN
            else:
                self.collect_treasures()
            # Row position at 0 is win position
            live_result = (live_result, CC.GAME_OVER_COMPLETE)[not self.player.oldpos[0]]

        # ===============================================
        # Check for player death at deadly block
        # ===============================================
        if self[self.player.oldpos] in CC.DEADLY_BLOCKS:
            key = str(self.player.oldpos) + ":" + str(self[self.player.oldpos])
            self.animated_entities[key].hit_sound is None or self.animated_entities[key].hit_sound.play()
            live_result = CC.GAME_OVER_KILLED

        # ================================================
        # Drawing items in their positions
        # First -- non-movable level blocks with animation
        # ================================================
        self.show_animated(player_tick)

        # ==================================================================
        # Second -- draw temporary items and do collision check if necessary
        # ==================================================================
        for tempBlock in self.temporary_items:
            tempBlock.show(self.canvas, player_tick)
            if tempBlock.died:
                if tempBlock.underlay is not None:
                    if not tempBlock.is_killing(self.player.pos, self.beasts):
                        live_result = CC.GAME_OVER_STUCK
                    self[tempBlock.pos] = tempBlock.underlay
                del self.temporary_items[self.temporary_items.index(tempBlock)]

        # ===========================
        # Third -- draw player sprite
        # ===========================
        self.show_player(player_tick)

        # ========================================================
        # Fourth -- move all beasts and check for eating player or
        #           for death at deadly block. Draw them as well.
        # ========================================================
        for beast in self.beasts:
            if not beast_tick:
                # Метод возвращает ложь, если монстр оказался в позиции игрока
                # В нашей ситуации это означает съедение
                if not beast.move(self.player.pos, self.beasts):
                    live_result = CC.GAME_OVER_EATEN
                else:
                    if self[beast.oldpos] in CC.DEADLY_BLOCKS:
                        key = str(beast.oldpos) + ":" + str(self[beast.oldpos])
                        self.animated_entities[key].hit_sound is None or self.animated_entities[key].hit_sound.play()
                        beast.die()
            beast.show(self.canvas, beast_tick)

        return live_result

    def collect_treasures(self):
        """Проверка на подбор сокровища игроком. Если все сокровища собраны, добавляем выход с уровня"""
        for chb in CC.TREASURE_BLOCKS:
            key = str(self.player.oldpos) + ":" + chb
            if key in self.animated_entities:
                self.animated_entities[key].hit_sound is None or self.animated_entities[key].hit_sound.play()
                del self.animated_entities[key]
                self.treasures_count -= 1

                # Все сокровища собраны, готовим выход
                if self.treasures_count <= 0:
                    self.exit_appears_sound.play()
                    #  Эта строка объединяет два массива. Там где в массиве exit не стоит точка, используется
                    # символ этого массива, иначе -- исходного. Своеобразное наложение по маске.
                    self.level = [[elem[elem[1] != '.'] for elem in zip(level_row[0], level_row[1])]
                                  for level_row in zip(self.level, self.exit)]
                    self.prepare_static()
                    self.show_static()

        # Возвращаем значение, чтобы в главном цикле можно было написать более лаконичный код
        return CC.GAME_OVER_NOT_OVER

    @staticmethod
    def play_background_music(filename):
        """Load and start playing level background music"""
        pygame.mixer.music.load(filename)
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1)

    def stop_all_sounds(self):
        """Stop playing all level related sounds. Used in level change procedure."""
        self.exit_appears_sound.stop()
        self.level_end_sound.stop()

    def __getitem__(self, item):
        return (None, self.level[item[0]][item[1]])[isinstance(item, (list, tuple))]

    def __setitem__(self, key, value):
        if isinstance(key, (list, tuple)):
            self.level[key[0]][key[1]] = value
