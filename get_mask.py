import numpy as np
import os
import SimpleITK as sitk
import cv2 as cv
from matplotlib import pyplot as plt

def mask(slice):
    # slice *= 10
    threshold, binary = cv.threshold(slice, 0, 255, cv.THRESH_BINARY+cv.THRESH_OTSU)
    binary = binary.astype(np.ubyte)
    contours, hierarchy = cv.findContours(binary, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)
    area = []
    for i in range(len(contours)):
        area.append(cv.contourArea(contours[i]))
    max_idx = np.argmax(area)
    max_area = cv.contourArea(contours[max_idx])
    for i in range(len(contours)):
        if i != max_idx:
            cv.fillPoly(binary, [contours[i]], 0)
    '''
    cv.fillPoly(binary, [contours[max_idx]], 0)
    
    cv.imwrite("./fgMask.png", binary)
    input("1:")
    '''
    return binary