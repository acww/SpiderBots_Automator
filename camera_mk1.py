from picamera.array import PiRGBArray
from picamera import PiCamera
from BattleSpider import *
import numpy as np
import maze_mk2 as maze
import cv2

IMG_WIDTH = 640
IMG_HEIGHT = 480

camera = PiCamera()
camera.resolution = (IMG_WIDTH, IMG_HEIGHT)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(IMG_WIDTH, IMG_HEIGHT))

Preview = True

while Preview:
    rawCapture.truncate(0)
    camera.capture(rawCapture, format="bgr", use_video_port=True)
    img2 = rawCapture.array
    cv2.imshow('Preview', img2)
    key = cv2.waitKey(1)
    if key == ord('s'):
        Preview = False
cv2.destroyAllWindows()

class Setup:
    def get_shape(self, img2):
        img = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Converting image to a binary image
        # (black and white only image).
        _, threshold = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY)
        # Detecting shapes in image by selecting region
        # with same colors or intensity.
        contours,_ = cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        # Searching through every region selected to
        # find the required polygon.
        cnt = contours[1]
        area = cv2.contourArea(cnt)
        # Shortlisting the regions based on there area.
        if area < 400:
            smoothing = 0.07
        elif area < 1001:
            smoothing = 0.06
        elif area < 2001:
            smoothing = 0.06
        elif area < 10001:
            smoothing = 0.055
        else:
            smoothing = 0.05
        approx = cv2.approxPolyDP(cnt,
                                  smoothing * cv2.arcLength(cnt, True), True)
        sides = len(approx)
        return (area-50), (area+50), sides, smoothing, cnt

    def get_shape_values(self):
        rawCapture.truncate(0)
        camera.capture(rawCapture, format="bgr", use_video_port=False)
        img = rawCapture.array
        (x,y,w,h) = cv2.selectROI('Select roi', img)
        cropped = img[y: y + h, x: x + w]
        cv2.destroyAllWindows()
        min_size, max_size, sides, smoothing, cnt = self.get_shape(cropped)
        print(min_size, max_size, sides, smoothing)
        return (self.get_shape(cropped))

setup = Setup()

class Shape:

    pre_tx, pre_ty = 0, 0
    pre = "null"
    def __init__(self, b1):     # Class wich mainly handles turning to face a set coordinate
        self.b1 = b1
        self.min_size, self.max_size, self.sides, self.smoothing, self.cnt2 = setup.get_shape_values()

    def cost(self, tx, ty, px, py):     # Gets the distance between two points
        dy = (ty-py)*(ty-py)
        dx = (tx-px)*(tx-px)
        price = np.sqrt(dx+dy)
        return price

    def get_front(self, cnt):       # Finds the front of the robot
        M = cv2.moments(cnt)
        cx = int(M["m10"] / M["m00"])
        cy = int(M["m01"] / M["m00"])
        cx = round(cx)
        cy = round(cy)
        l = tuple(cnt[cnt[:,:,0].argmin()][0])
        r = tuple(cnt[cnt[:,:,0].argmax()][0])
        t = tuple(cnt[cnt[:,:,1].argmin()][0])
        b = tuple(cnt[cnt[:,:,1].argmax()][0])
        extr = [l, r, t, b]
        pre_dist = 0
        for p in extr:
            x, y = p
            dist = self.cost(cx, cy, x, y)
            if dist > pre_dist:
                front = x, y
                pre_dist = dist
        x, y = front
        return front, (cx, cy)

    def getFrontAndCenter(self):
        rawCapture.truncate(0)
        camera.capture(rawCapture, format="bgr", use_video_port=True)
        img2 = rawCapture.array
        img = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Converting image to a binary image
        # (black and white only image).
        _,threshold = cv2.threshold(img, 60, 255, cv2.THRESH_BINARY)

        # Detecting shapes in image by selecting region
        # with same colors or intensity.
        contours,_=cv2.findContours(threshold, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        # Searching through every region selected to
        # find the required polygon.
        number = 0
        pre_ret = 100
        for cnt in contours:
            area = cv2.contourArea(cnt)
            # Shortlisting the regions based on there area.
            if area < self.max_size and area > self.min_size:
                approx = cv2.approxPolyDP(cnt, self.smoothing * cv2.arcLength(cnt, True), True)
                if len(approx) == self.sides:
                    number = number + 1
                    ret = cv2.matchShapes(cnt,self.cnt2,1,0.0)
                    if ret < pre_ret:
                        robot = cnt
                        pre_ret = ret
                        front, center = self.get_front(robot)
        if number == 0:
            for cnt in contours:
                ret = cv2.matchShapes(cnt,self.cnt2,1,0.0)
                if ret < pre_ret:
                    shape = cnt
                    pre_ret = ret
                    front, center = self.get_front(shape)
        return front, center

    def find(self):
        front, center = self.getFrontAndCenter()
        return front, center

    def turn(self, target, center, front, tick):                              # Turns left and right
        (tx, ty), (cx, cy), (fx, fy) = target, center, front
        pos = np.sign((tx - cx) * (fy - cy) - (ty - cy) * (fx - cx))
        if pos == 1:
            if self.pre != "l":
                self.b1.stopTurn()
                sleep(0.2)
            self.b1.left()
            self.pre = "l"
        else:
            if self.pre != "r":
                self.b1.stopTurn()
                sleep(0.2)
            self.b1.right()
            self.pre = "r"
        if tick:
            sleep(0.1)
            self.b1.stopTurn()
        print(self.pre)

    def check_inline(self, center, front, target, accuracy, fire):
        fire = True
        (flx, fly), (frx, fry), ft, (blx, bly), (brx, bry), bb = maze.getWayPoints(center, front, accuracy, fire)
        (tx, ty) = target
        robotx, roboty = center
        print(tx, flx, fly, bly, ty, blx)
        left = np.sign((tx - flx) * (fly - bly) - (ty - bly) * (flx - blx))
        right = np.sign((tx - frx) * (fry - bry) - (ty - bry) * (frx - brx))
        if abs(tx-robotx) < 30 and abs(ty-roboty) < 30:
            return True
        if left != right:
            return True
        else:
            return False

    def allign(self, target, fire):                             # Main bit of robot of code
        front, center = self.find()
        if fire:                                                # Changes accuracy depending on whether its fireing
            accuracy = 30
        else:
            accuracy = 20
        inline = self.check_inline(center, front, target, accuracy, fire)
        tick = False
        if inline:                                              # If we are inline (or out but within accuracy)
            self.b1.stopTurn()                                  # then we return the offset and stop turning
            if fire:
                sleep(0.5)
            return
        self.turn(target, center, front, tick)                  # Turn appropriatly
        self.allign(target, fire)                               # Call ourselves again

    def count_non_zero(self, img):      # Counts the non black in an image
        return np.count_nonzero(img)

    def accessible(self, rx, ry, tx, ty, wp, rw):        # Checks to see if the robot can access a specified point
        image = pass_image()
        loaw = []
        base = self.count_non_zero(image)
        for x in wp:
            test = cv2.line(image.copy(), (rx,ry), x, (255,255,255), 15)
            path = self.count_non_zero(test)
            if base == path:
                loaw.append(x)
        costs = []
        aw = []
        for x in loaw:                            # The code that organises the waypoints closest to furthest
            mx, my = x
            price = self.cost(mx, my, tx, ty)
            costs.append(price)
            costs.sort()
            price_pos = costs.index(price)
            aw.insert(price_pos, x)
        return aw

    def access_to(self, robot, target, rw):
        image = pass_image()
        base = self.count_non_zero(image)
        access = False
        test = cv2.line(image.copy(), robot, target, (255,255,255), 15)
        path = self.count_non_zero(test)
        if base == path:
            access = True
            return True
        return access

class Walls:
    def cost(self, tx, ty, px, py):     # Gets the distance between two points
        dy = (ty-py)*(ty-py)
        dx = (tx-px)*(tx-px)
        price = np.sqrt(dx+dy)
        return price

    def midpoint(self, p1, p2):
        (x1, y1), (x2, y2) = p1, p2
        return (int((x1+x2)/2), int((y1+y2)/2))

    def get_ends(self, cnt):
        extr = cnt
        pre_price = 10000
        l = tuple(cnt[0])
        x, y = l
        for (cx, cy) in extr:
            price = self.cost(x, y, cx, cy)
            if (x, y) != (cx, cy):
                if price < pre_price:
                    pre_price = price
                    p = cx, cy
        point1 = self.midpoint(l, p)
        one = True
        for coor in extr:
            coor = tuple(coor)
            print(coor)
            print(l)
            print(p)
            if coor != l and coor != p:
                if one:
                    one = False
                    p1 = coor
                else:
                    p2 = coor
        point2 = self.midpoint(p1, p2)
        return point1, point2

    def get_image(self, cnt, wall_image):
        print(cnt)

        pts = np.array(cnt, np.int32)
        cv2.polylines(wall_image,[pts],True,(0,0,0))
        cv2.fillPoly(wall_image,[pts],(0,0,0))
        return pts, wall_image

    # Reading image
    def get_walls(self, image):
        rawCapture.truncate(0)
        camera.capture(rawCapture, format="bgr", use_video_port=False)
        img2 = rawCapture.array
        img = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)
        if image is tuple:
            image = img
        cv2.imshow("", img)

        walls = []

        # Converting image to a binary image
        # (black and white only image).
        _,threshold = cv2.threshold(img, 50, 255,
                                    cv2.THRESH_BINARY)

        cv2.imshow(" ", threshold)
        cv2.waitKey(60)

        # Detecting shapes in image by selecting region
        # with same colors or intensity.
        contours,_=cv2.findContours(threshold, cv2.RETR_TREE,
                                    cv2.CHAIN_APPROX_SIMPLE)
        CNT = 0
        # Searching through every region selected to
        # find the required polygon.
        arbitary_polygon = []
        walls = []
        for cnt in contours :
            area = cv2.contourArea(cnt)
            # Shortlisting the regions based on there area.
            if area < 100000 and area > 1000:
                rect = cv2.minAreaRect(cnt)
                box = cv2.boxPoints(rect)
                cnt = np.int0(box)
                CNT, wall_image = self.get_image(cnt, image)
                front, back = self.get_ends(cnt)
                walls.append((front, back))
                img2 = cv2.line(img2, front, back, (0,0,255), 5)
                arbitary_polygon.append(CNT)
        return img2, arbitary_polygon, wall_image, walls

    def find_walls(self, image):
        Preview = True
        img2, cnt, wall_image, walls = self.get_walls(image)
        sleep(0.5)
        img2, cnt, wall_image, walls = self.get_walls(image)
        while Preview:
            cv2.imshow('Preview of wall image', wall_image)
            cv2.imshow('preveiw of lined image', img2)
            key = cv2.waitKey(1)
            if key == ord('r'):
                img2, cnt, wall_image, walls = self.get_walls(image)
            if key == ord('s'):
                Preview = False
        cv2.destroyAllWindows()
        return wall_image, walls


walls_finder = Walls()

wall_image = np.zeros((IMG_HEIGHT,IMG_WIDTH,3), np.uint8)

width = IMG_WIDTH

wall_image[:,0:width//2] = (255,255,255)
wall_image[:,width//2:width] = (225,255,255)

wall_image, list_of_walls = walls_finder.find_walls(wall_image)

def pass_image():
    global wall_image
    return wall_image.copy()

rawCapture.truncate(0)
camera.capture(rawCapture, format="bgr", use_video_port=True)
lines = rawCapture.array

def draw_line(pt1, pt2):
    global lines
    lines = cv2.line(lines,pt1,pt2,(255,0,0),5)
    cv2.imshow('lines', lines)
    cv2.waitKey(1)

def circle(pos, colour):
    global lines
    lines = cv2.circle(lines, pos, 10, colour, -1)

def pass_canvass():
    rawCapture.truncate(0)
    camera.capture(rawCapture, format="bgr", use_video_port=False)
    img = rawCapture.array
    return img