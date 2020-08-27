from basic_movement_mk3 import *

def basic():
    while True:
        if enemy_accessible():
            stop()
            target = enemy_pos()
            turn_to(target[1])
            fire()
            draw(target[1])
        else:
            path = path_plan_mk2(True)
            print('path', path)
            target = path[0]
            print('target', target)
            turn_to(target)
            go_to(path)
            draw(target)

def loop_fix():
    basic()

loop_fix()