import numpy as np

def getWayPoints(s, e, w, fire):      # Gets waypoints
    x1, y1 = s
    x2, y2 = e
    dx = x2 - x1
    dy = y2 - y1
    alpha = np.arctan(dy/dx)
    dx = np.sin(alpha)*w
    dy = np.cos(alpha)*w
    rdx = np.sin(alpha)*w
    rdy = np.cos(alpha)*w
    if fire:
        rdx = np.sin(alpha)*(w-(w/7))
        rdy = np.cos(alpha)*(w-(w/7))
    ex = dy
    ey = dx
    if x1 > x2:
        ex = -ex
        ey = -ey
    # top left, top right, top top, bottom left, bottom right, bottom bottom
    return (int(x1-rdx),int(y1+rdy)), (int(x1+rdx),int(y1-rdy)), (int(x1-ex),int(y1-ey)),(int(x2-dx),int(y2+dy)), (int(x2+dx),int(y2-dy)), (int(x2+ex),int(y2+ey))

def getWayPoints_simple(s, e, w):      # Gets waypoints
    x1, y1 = s
    x2, y2 = e
    dx = x2 - x1
    dy = y2 - y1
    alpha = np.arctan(dy/dx)
    dx = np.sin(alpha)*w
    dy = np.cos(alpha)*w
    rdx = np.sin(alpha)*w
    rdy = np.cos(alpha)*w
    ex = dy
    ey = dx
    if x1 > x2:
        ex = -ex
        ey = -ey
    # top left, top right, top top, bottom left, bottom right, bottom bottom
    left = (int(x1-rdx),int(y1+rdy)), (int(x2-dx),int(y2+dy))
    right = (int(x1+rdx),int(y1-rdy)), (int(x2+dx),int(y2-dy))
    (x1, y1), (x2, y2) = left
    dx = x2 - x1
    dy = y2 - y1
    alpha = np.arctan(dy/dx)
    dx = np.sin(alpha)*w
    dy = np.cos(alpha)*w
    rdx = np.sin(alpha)*w
    rdy = np.cos(alpha)*w
    ex = dy
    ey = dx
    if x1 > x2:
        ex = -ex
        ey = -ey
    top_left, bottom_left = (int(x1-ex),int(y1-ey)), (int(x2+ex),int(y2+ey))
    (x1, y1), (x2, y2) = right
    dx = x2 - x1
    dy = y2 - y1
    alpha = np.arctan(dy/dx)
    dx = np.sin(alpha)*w
    dy = np.cos(alpha)*w
    rdx = np.sin(alpha)*w
    rdy = np.cos(alpha)*w
    ex = dy
    ey = dx
    if x1 > x2:
        ex = -ex
        ey = -ey
    top_right, bottom_right = (int(x1-ex),int(y1-ey)), (int(x2+ex),int(y2+ey))
    return top_left, bottom_left, top_right, bottom_right