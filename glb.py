"""Global functions for all modules"""

from os import path
import pygame
from pygame.locals import *
import random
import CC


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


def check_bounds(pos: list):
    """Return true, if provided position within screen bounds, else false"""
    return 0 <= pos[1] < CC.LEVEL_WIDTH and 0 <= pos[0] < CC.LEVEL_HEIGHT


def sign(x):
    return -1 if x < 0 else 1 if x > 0 else 0


def get_subset_by_type(db:dict, request_type):
    """Возвращает список блоков только заданного типа. db -- CC.BLOCKS"""
    res = dict()
    for leaf_key in db:
        if request_type in db[leaf_key]["type"]:
            res.update({leaf_key: db[leaf_key]})

    return res

