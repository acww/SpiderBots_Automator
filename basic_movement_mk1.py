import numpy as np
from camera_mk4 import *        # Because the pi's camera can only be initialised once
                                # its easier to have everthing that requires an image in one file.
import maze_mk3 as maze         # Mainly handles way point finding.
from BattleSpider import *      # Handles spider bot control.
import cv2

walls = Walls()
b1 = BattleSpider(14)       # Sets up the SpiderBot on pin 14
robot = Shape(b1)
enemy = Shape(10)

ROBOT_SIZE = 100        # An approximate width of the robot

def get_targets(c):     # Function to get the six waypoints around a wall
    s, e = c
    wayPoints = maze.getWayPoints_simple(s, e, (ROBOT_SIZE-(ROBOT_SIZE/4)))
    return wayPoints

def cost(pA, pB):          # Gets the distance between two coordinates
    (tx, ty) = pA
    (px, py) = pB
    dy = (ty-py)*(ty-py)
    dx = (tx-px)*(tx-px)
    dis = np.sqrt(dx+dy)
    return dis

wall_image, list_of_walls = walls.find_walls((0, 0))

wp = []         # List of unorderd waypoints
for x in list_of_walls:
    a, b = x
    waypoint = get_targets(x)
    circle((waypoint[0]), (0,255,0))
    circle((waypoint[1]), (0,0,255))
    circle((waypoint[2]), (255,0,0))
    circle((waypoint[3]), (255,255,0))
    wp += waypoint

def get_accessible_waypoints(pos):
    global wp, ROBOT_SIZE
    if (isinstance(pos, tuple)):
        rx, ry = pos
    else:
        front, (rx, ry) = robot.find()                                 # rx, ry robots center of mass and tx, ty enemy's center of mass
    en_front, (enx, eny) = enemy.find()
    center = (int(rx), int(ry))
    loaw = robot.accessible(rx, ry, enx, eny, wp, ROBOT_SIZE)
    return loaw

for x in wp:
    print(x)
    access_points = get_accessible_waypoints(x)
    for point in access_points:
        draw_line(x, point)

def find_closest_to_enemy(loaw):
    front, (tx, ty) = enemy.find()
    wp = []
    costs = []
    for x in loaw:                            # The code that organises the waypoints closest to furthest
        mx, my = x
        price = cost((mx, my), (tx, ty))
        costs.append(price)
        costs.sort()
        price_pos = costs.index(price)
        wp.insert(price_pos, x)
    return (wp[0])

def enemy_pos():
    return (enemy.find())

pre_target = (0, 0)
def turn_to(target):
    global pre_target
    if target != pre_target:
        stop()
    robot.allign(target, True)
    pre_target = target

def fire():
    b1.fire()

def stop():
    b1.stop()

def go_to(target):
    front, (rx, ry) = robot.find()
    check = target[1]
    target = target[0]
    print(target)
    while accessible(target) and not accessible(check) and not enemy_accessible():
        b1.fwd()
        turn_to(target)
        front, (rx, ry) = robot.find()
    b1.stop()

def accessible(place):
    global wp, ROBOT_SIZE
    front, me = robot.find()                                 # rx, ry robots center of mass and tx, ty enemy's center of mass
    access = robot.access_to(me, place, ROBOT_SIZE)
    return access

def enemy_accessible():
    global wp, ROBOT_SIZE
    front, me = robot.find()                                 # rx, ry robots center of mass and tx, ty enemy's center of mass
    front, place = enemy.find()
    access = robot.access_to(me, place, ROBOT_SIZE)
    return access

def access_granted(place):
    global wp, ROBOT_SIZE
    (rx, ry) = place
    front, (enx, eny) = enemy.find()
    loaw = robot.accessible(rx, ry, enx, eny, [(enx, eny)], ROBOT_SIZE)
    if (enx, eny) in loaw:
        return True
    return False

path = []
def path_plan_mk2(path):
    if path is True:
        print('starting path plan')
        path = []
        front, pos = robot.find()
    else:
        pos = path[-1]
    draw_path(pos)
    for x in get_accessible_waypoints(pos):
        if access_granted(x):
            path.append(x)
            front, enemy_pos = enemy.find()
            path.append(enemy_pos)
            newpath = path
            return newpath
        else:
            if x not in path:
                path.append(x)
                print('going to')
                path = path_plan_mk2(path)
                return path


def path_plan(path, access=False):
    if len(path) == 0:
        front, (rx, ry) = robot.find()
        path = [(rx, ry)]
    print('path', path)
    if not access:
        for node in get_accessible_waypoints(path[-1]):
            if node not in path:
                path.append(node)
                newpath = path
                if access_granted((newpath[-1])):
                    front, center = enemy.find()
                    newpath.append(center)
                    print('done path', newpath)
                    return newpath, True
                newpath = path_plan(path)
    newpath = path
    return newpath

def find_path():
    path = path_plan([])
    print('orig path', path)
    if True in path:
        print(path[0])
        return path[0]
    return path

def draw_path(pos):
    img = pass_image()
    ro_front, ro_center = robot.find()
    en_front, en_center = enemy.find()
    img = cv2.circle(img, ro_center, 20, (0,0,255), -1)
    img = cv2.circle(img, en_center, 20, (255,0,0), -1)
    accessible_points = get_accessible_waypoints(pos)
    for x in accessible_points:
        img = cv2.circle(img, x, 10, (255,255,0), -1)
    img = cv2.circle(img, pos, 10, (0,255,0), -1)
    cv2.imshow("path", img)
    cv2.waitKey(1)

def draw(target):
    img = pass_canvass()
    img2 = pass_image()
    ro_front, ro_center = robot.find()
    en_front, en_center = enemy.find()
    img = cv2.circle(img, ro_center, 20, (0,0,255), -1)
    img = cv2.circle(img, en_center, 10, (0,0,255), -1)
    img = cv2.circle(img, target, 10, (0,255,0), -1)
    cv2.imshow("  ", img)
    key = cv2.waitKey(1)
    img2 = cv2.circle(img2, ro_center, 10, (0,0,255), -1)
    img2 = cv2.circle(img2, en_center, 10, (0,0,255), -1)
    img2 = cv2.circle(img2, target, 10, (0,255,0), -1)
    cv2.imshow(" ", img2)
    cv2.waitKey(1)