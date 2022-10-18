""" Классы блоков.
 Это базовый класс для всех спрайтов игры.
 Плюс, класс анимированных, но статичных спрайтов.
 И класс временных анимированных спрайтов. С их помощью подсвечиваются различные события уровня.

 V 2.1

 2.1 Реализован класс Button

 2.0 Реализован класс TemporaryBlock
"""

from os import path
import pygame
from game_structure import BLOCK_WIDTH


class Block(pygame.sprite.Sprite):
    """Спрайт уровня. Неподвижный, с разными характеристиками проницаемости"""

    def __init__(self, img, position: list = None, subfolder=""):
        super().__init__()
        self.pos = [0, 0] if position is None else position
        self.oldpos = None
        self.base_images_folder = path.join(path.dirname(__file__), "images", subfolder)

        if img is not None:
            if isinstance(img, str):
                self.image = pygame.image.load(path.join(self.base_images_folder, img)).convert_alpha()
            if isinstance(img, Block):
                self.image = img.image
        else:
            self.image = pygame.Surface((BLOCK_WIDTH, BLOCK_WIDTH))
            self.image.fill((255, 255, 0))

        self.size = self.image.get_size()
        self.rect = self.image.get_rect(center=(self.size[0] / 2, self.size[1] / 2))

    # TODO Реализовать масштабирование
    def copy(self, xflip=False, yflip=False, scale=1):
        """Копирование текущего экземпляра в новый объект с возможностью отобразить зеркально."""
        copied = Block(None)

        if xflip or yflip:
            copied.image = pygame.transform.flip(self.image, xflip, yflip)
        else:
            copied.image = self.image.copy()

        return copied

    def get_screen_pos(self, step=0.0, tick=0):
        """Переводит старую и новую позицию в знакоместах в экранные координаты относительно текущего игрового тика"""
        if self.oldpos is None:
            return self.pos[1] * BLOCK_WIDTH, self.pos[0] * BLOCK_WIDTH

        disp = step * tick
        disp_x = (self.pos[1] - self.oldpos[1]) * disp
        disp_y = (self.pos[0] - self.oldpos[0]) * disp
        return self.oldpos[1] * BLOCK_WIDTH + disp_x, self.oldpos[0] * BLOCK_WIDTH + disp_y

    def show(self, canvas: pygame.Surface, pos: tuple):
        """Рисование спрайта в заданных координатах сетки на заданной канве"""
        canvas.blit(self.image, self.image.get_rect(topleft=(pos[0] * BLOCK_WIDTH, pos[1] * BLOCK_WIDTH)))


class Button(Block):
    """ Элемент интерфейса -- кнопка. Имеет два состояния: нажата и не нажата."""

    def __init__(self, img: tuple, subfolder="", pos: tuple = None, event: int = 0, key=0):
        super().__init__(img[0], subfolder=subfolder)

        self.images = [self.image, None]
        self.pressed_state = False
        self.event = event
        self.key = key
        if img[1] is not None:
            if isinstance(img[1], str):
                self.images[1] = pygame.image.load(path.join(self.base_images_folder, img[1])).convert_alpha()
            if isinstance(img[1], Block):
                self.images[1] = img[1].image

        if pos is not None:
            self.rect = self.image.get_rect(topleft=pos)

    def copy(self, xflip=False, yflip=False, scale=1):
        copied = Button((None, None))

        if xflip or yflip:
            copied.images = [pygame.transform.flip(self.images[0], xflip, yflip),
                             pygame.transform.flip(self.images[1], xflip, yflip)]
        else:
            copied.images = self.images.copy()

        copied.pressed_state = self.pressed_state

        return copied

    def get_image(self):
        return self.images[self.pressed_state]

    def show(self, canvas: pygame.Surface, state=None):
        """Рисует кнопку в соответствующем состоянии"""
        if state is None:
            state = self.pressed_state

        self.pressed_state = state
        canvas.blit(self.get_image(), self.rect)
        return (self.event, None)[state]


class AnimatedBlock(Block):
    """Анимированный спрайт уровня. Неподвижный"""

    def __init__(self, img, position=None, subfolder="", animation_delay=0, animation_pause=0, hit_sound=None):
        self.delay = animation_delay
        self.pause = animation_pause
        self.images = list()
        self.single = True
        self.ticks = 0
        self.current_frame = 0
        self.in_action = True
        self.hit_sound = hit_sound

        super(AnimatedBlock, self).__init__(None, position, subfolder)
        if isinstance(img, (tuple, list)):
            for file in img:
                self.images.append(Block(file, position, subfolder))
            self.single = False

    def get_image(self, tick):
        if not self.single:
            wait_for = (self.pause, self.delay)[self.in_action]

            if self.ticks < wait_for:
                self.ticks += 1
            else:
                self.ticks = 0
                self.current_frame = self.current_frame + 1 if self.in_action else self.current_frame
                if self.current_frame >= len(self.images) or not self.in_action:
                    self.current_frame = 0

                if self.current_frame == 0:
                    self.in_action = not self.in_action

            return self.images[self.current_frame].image
        else:
            return self.image

    def show(self, canvas: pygame.Surface, tick):
        canvas.blit(self.get_image(tick), self.get_screen_pos(tick=tick))

    def copy(self, xflip=False, yflip=False, scale=1):
        copied = AnimatedBlock(None, self.pos, animation_delay=self.delay, animation_pause=self.pause)
        return self.__copy_body__(copied, xflip, yflip, scale)

    def __copy_body__(self, dst, xflip=False, yflip=False, scale=1):
        dst.single = self.single
        dst.pos = self.pos
        dst.ticks = self.ticks
        dst.current_frame = self.current_frame
        dst.in_action = self.in_action

        if self.single:
            if xflip or yflip:
                dst.image = pygame.transform.flip(self.image, xflip, yflip)
            else:
                dst.image = self.image.copy()
        else:
            for pict in self.images:
                dst.images.append(pict.copy(xflip, yflip, scale))
            # for pict in self.images[z].images_end:
            #     copied.images_end.append(pict.copy(xflip,yflip,scale))

        return dst


class TemporaryBlock(AnimatedBlock):
    """ Неподвижный анимированный блок уровня. Временный. Никак не влияет на персонажей.
        Нужен только для анимации различных событий на уровне -- разрушение, декорации и прочее.

        Блок существует, пока проигрывается стартовая анимация. Если задан animation_delay,
        финальный кадр стартовой анимации замораживается на это время.
        Если нет -- сразу начинается проигрываться анимация финала, если задана
        После завершения этой анимации блок исчезает.
    """

    def __init__(self, img: tuple, position=None, subfolder="", animation_delay=0, animation_pause=0,
                 sound=None):
        self.on_start = True
        self.died = False
        self.underlay = None
        self.sound = sound
        self.images_end = None
        (img_start, img_end, *rest) = img

        super().__init__(img_start, position, subfolder, animation_delay, animation_pause)
        if isinstance(img_end, (tuple, list)):
            self.images_end = list()
            for file in img_end:
                self.images_end.append(Block(file, position, subfolder))

    def get_image(self, tick):
        if self.single:
            self.ticks += 1
            if self.ticks >= self.delay:
                self.ticks = self.delay
                self.died = True

            return self.image

        if not self.died:
            action = self.in_action
            super().get_image(tick)

            # Поведение по завершению анимации отличается.
            # Как только заканчивается стартовая анимация, мы показываем ПОСЛЕДНИЙ её кадр, а не первый.
            if action and not self.in_action:
                if self.on_start:
                    self.on_start = False
                    self.current_frame = len(self.images) - 1
                    if self.images_end is None:
                        self.died = True
                else:  # Объект отыграл финальную анимацию и должен быть уничтожен
                    if self.current_frame == 0:
                        temp_img = self.images
                        self.images = self.images_end
                        self.images_end = temp_img
                        self.died = True
                        return self.images_end[len(self.images_end) - 1].image

            # Это условия начала воспроизведения новой анимации после паузы. Так они выполняются после
            # отработки get_image родителя
            if not self.on_start and self.in_action and \
                    self.current_frame == 0 and self.ticks == 0 and \
                    not self.died:
                # Чтобы работал старый код, просто подставим анимацию финала вместо стартовой
                temp_img = self.images
                self.images = self.images_end
                self.images_end = temp_img

        return self.images[self.current_frame].image

    def copy(self, xflip=False, yflip=False, scale=1):
        copied = TemporaryBlock((None, None), self.pos, animation_delay=self.delay, animation_pause=self.pause)
        self.__copy_body__(copied, xflip, yflip, scale)
        if self.images_end is not None:
            copied.images_end = list()
            for pict in self.images_end:
                copied.images_end.append(pict.copy(xflip, yflip, scale))
        copied.on_start = self.on_start
        copied.died = self.died
        copied.underlay = self.underlay

        return copied
