# LodeRunner clone game
# Проект по освоению программирования на Python'е

# Шаг 1.0
# Загрузка уровня и вывод его текстовыми символами

# Цель: 
# Научиться чтению из текстового файла и создание
# базового модуля вывода, который затем будет
# переписан под графику.

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