# Классы блоков. Это базовый класс для всех спрайтов игры. Плюс, класс анимированных, но статичных спрайтов

# V 1.0

import os
import pygame

BLOCK_WIDTH = 45


class Block(pygame.sprite.Sprite):
    """Спрайт уровня. Неподвижный, с разными характеристиками проницаемости"""

    def __init__(self, img, subfolder=""):
        super().__init__()
        self.base_images_folder = os.path.join(os.path.dirname(__file__), "images", subfolder)

        if img is not None:
            self.image = pygame.image.load(os.path.join(self.base_images_folder, img)).convert_alpha()
        else:
            self.image = pygame.Surface((BLOCK_WIDTH, BLOCK_WIDTH))
            self.image.fill((255, 255, 0))

        self.size = self.image.get_size()
        self.rect = self.image.get_rect(center=(self.size[0] / 2, self.size[1] / 2))

    # TODO Реализовать масштабирование
    def copy(self, xflip=False, yflip=False, scale=1):
        copied = Block(None)

        if xflip or yflip:
            copied.image = pygame.transform.flip(self.image, xflip, yflip)
        else:
            copied.image = self.image.copy()

        return copied


class AnimatedBlock(Block):
    """Анимированный спрайт уровня. Неподвижный"""

    def __init__(self, img, position=None, subfolder="", animation_delay=0, animation_pause=0):
        self.pos = [0, 0] if position is None else position
        self.delay = animation_delay
        self.pause = animation_pause
        self.images = list()
        self.single = False
        self.ticks = 0
        self.current_frame = 0
        self.in_action = True

        super(AnimatedBlock, self).__init__(None, subfolder)
        if isinstance(img, (tuple, list)):
            for file in img:
                self.images.append(Block(file, subfolder))
        else:
            self.single = True

    def get_image(self, tick):
        if not self.single:
            wait_for = self.delay if self.in_action else self.pause

            if self.ticks < wait_for:
                self.ticks += 1
            else:
                self.ticks = 0
                self.current_frame = self.current_frame + 1 if self.in_action else self.current_frame
                if self.current_frame >= len(self.images):
                    self.current_frame = 0
                self.in_action = not self.in_action if self.current_frame == 0 else self.in_action

            return self.images[self.current_frame].image
        else:
            return self.image
