"""Global functions for all modules"""

from os import path
import pygame
from pygame.locals import *
import random


def load_sound(filename):
    """Загрузка звукового эффекта. Все эффекты лежат в каталоге Sounds"""
    if filename is None:
        return None
    snd = pygame.mixer.Sound(path.join(path.dirname(__file__), "Sounds", filename))
    snd.set_volume(0.5)
    return snd


def to_number(val):
    """Return random number from provided range or value itself"""
    return random.randrange(int(val[0]), int(val[1]), int(val[2])) if isinstance(val, (list, tuple)) else val

