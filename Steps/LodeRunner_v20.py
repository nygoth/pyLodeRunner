# LodeRunner clone game
# This project is for studying python programming

# V 2.0
# Load level file and show it with sprites in window

# Goal is to learn how to use pygame
# to show static graphics
import sys

import pygame
from pygame.locals import *

class Block(pygame.sprite.Sprite):
    def __init__(self, img):
        super().__init__()
        self.image = pygame.image.load("images\\" + img)
        self.size = self.image.get_size()
        self.rect = self.image.get_rect(center=(self.size[0] / 2, self.size[1] / 2))

class Runner(Block):
    def __init__(self, img):
        super().__init__(img)


def init_screen(width, height):
    pygame.init()

    canvas = pygame.display.set_mode((width,height))
    pygame.display.set_caption("Lode Runner")
    return canvas

def load_level(filename):
    game_level=list()

    with open(filename, 'r') as lvl_stream:
        for line in lvl_stream:
            row = [ch for ch in line if (ch != "\n" and ch !="\r")]
            game_level.append(row)
    return game_level

def show_level(canvas, level, sprites):
    y=0

    for row in level:
        x = 0
        for block in row:
            curBlock = sprites.get(block)
            if curBlock != None:
                canvas.blit(curBlock.image, curBlock.image.get_rect(topleft=(x*45,y*45)))
            x += 1
        y += 1
    pygame.display.update()


level_blocks = {'Z':Block("brick.png"),
                'H':Block("ladder.png"),
                'O':Block("brick_solid.png"),
                '-':Block("bar.png"),
                'P':Block("exit_ladder.png"),
                '+':Block("treasure.png"),
                'X':Runner("beast.png"),
                'I':Runner("player.png")
                }

currentLevel = load_level("01.lvl")
show_level(init_screen(45*42, 45*22), currentLevel, level_blocks)

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()