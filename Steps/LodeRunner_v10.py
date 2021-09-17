# LodeRunner clone game
# This project is for studying python programming

# V 1.0
# Load level file and show it with text symbols

# Goal is to learn how to read from text file and
# to write basic output module which then will be
# replaced by sprite graphics

def load_level(filename):
    game_level=list()

    with open(filename, 'r') as lvl_stream:
        for line in lvl_stream:
            row = [ch for ch in line if (ch != "\n" and ch !="\r")]
            game_level.append(row)
    return game_level

def show_level(level):
    y=0

    for row in level:
        x = 0
        for block in row:
            print("\033[" + str(y) + ";" + str(x) + "H" + block)
            x += 1
        y += 1


currentLevel = load_level("01.lvl")
show_level(currentLevel)