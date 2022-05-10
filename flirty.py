#!/usr/bin/env python3

import os
import sys
import math
import datetime
import random
import re

from PIL import Image, ImageFilter, ImageOps
import pytesseract
import imageio as iio
import numpy as np

def average_color(colors):
    if len(colors) == 0: return ()
    avg = [None] * len(colors[0])

    for color in colors:
        for p in range(0, len(avg)):
            avg[p] += color[p]

    for p in range(0, len(avg)):
        avg[p] /= len(colors)

    return tuple(avg)


def quantize_color(src, row, comp):
    # First, find the closest match on the scale
    close_x = 0
    close_dist = 1000000
    #print("Provided color is " + str(comp))

    for x in range(0, src.width):
        check_col = src.getpixel((x, row))
        check_dist = math.dist(check_col, comp)

        if check_dist < close_dist:
            close_dist = check_dist
            close_x = x

    close_color = src.getpixel((row, close_x))
    #print("  Closest match is at " + str(close_x) + " (color " + str(close_color) + ", dist " + str(close_dist) + ")")
   
    # If this is the exact color, bail out early
    if close_dist == 0:
        #print("  Match is dead on, bailing")
        return close_x + 0.0

    # Otherwise, figure out how close it is to its neighbors
    left_x = (close_x - 1) if close_x > 0 else (close_x)
    left_color = src.getpixel((left_x, row))
    left_dist = math.dist(left_color, comp)
    #print("  Leftward distance is " + str(left_dist))

    right_x = (close_x + 1) if close_x < src.width else (close_x)
    right_color = src.getpixel((right_x, row))
    right_dist = math.dist(right_color, comp)
    #print("  Rightward distance is " + str(right_dist))

    neighbor_dist = (left_dist) if left_dist < right_dist else (right_dist)

    # Calculate ratio between quantized pixel and next closest pixel
    neighbor_ratio = (close_dist / neighbor_dist) * 0.5
    #print("  Match is about " + str(neighbor_ratio) + " off from the closest")
    close_x += (-neighbor_ratio) if left_dist < right_dist else (neighbor_ratio)
    #print("  Adjusted match is " + str(close_x))

    # And bail
    return close_x
   

def test_quantizer(src, row, iterations):
    for i in range(0, iterations):
        randloc = (random.randrange(0, src.width), random.randrange(0, src.height))
        rand_col = src.getpixel(randloc)
        print("Found " + str(rand_col) + " at " + str(randloc))
        quantize_color(src, row, rand_col)


def generate_circle_points(radius):
    # This is the Bad Way of doing this, the least efficient way
    # Bill Atkinson cries
    found = []

    for tx in range(0, radius*2):
        for ty in range(0, radius*2):
            if ( math.pow(tx - radius, 2) + math.pow(ty - radius, 2) ) <= math.pow(radius, 2):
                # Center of circle should be 0,0
                found.append( (tx-radius, ty-radius) )

    # Done, eventually
    return found


def relocate_points(src, dest, points):
    # Move array of points and exclude any that fall off
    good_points = []
    for point in points:
        relocated = (point[0] + dest[0], point[1] + dest[1])
        if 0 <= relocated[0] < src.width and 0 <= relocated[1] < src.height:
            good_points.append(relocated)

    # Also bleh
    return good_points


def get_average_of_circle(src, center, radius):
    # Generate the circle plz
    check_points = generate_circle_points(radius)
    check_points = relocate_points(src, center, check_points)
    running_avg = 0

    # Average quantized color
    for point in check_points:
        found_col = quantize_color(src, 0, src.getpixel(point))
        #print("Color at " + str(point) + " is " + str(found_col))
        running_avg += found_col

    return running_avg / len(check_points)


def is_greytone(colo, thresh):
    if abs(colo[0] - colo[1]) < thresh and abs(colo[0] - colo[2]) < thresh and abs(colo[1]-colo[2]) < thresh:
        return True

    return False


def extract_temp_scale(src, cropzone):
    # Rotate, crop, and crush colors
    textread = src.crop(cropzone)
    textread = textread.resize((textread.width * 8, textread.height * 8), Image.Resampling.BICUBIC)
    textread = textread.convert('L')
    #textread = textread.point( lambda p: 0 if p > 120 else 255)
    #textread.show()
    #input()

    # OCR that bitch
    scale_text = pytesseract.image_to_string(textread, config='--psm 8').split('\n')
    scale_text = [ t.replace(' ', '') for t in scale_text if t ]
    #print(scale_text)

    # Did we end up with two numbers?
    if len(scale_text) < 1: return ''
    return ''.join(scale_text)
    

def map_color_to_temp(scale, width, color):
    return scale[0] + ( color / width ) * (scale[1]-scale[0])





# -----------------------------------------------------------------------------------
# Main function
if __name__ == "__main__":
    # Open image
    #img = Image.open(sys.argv[1])
    
    workscount = 0
    framescount = 0
    processed = 0

    reader = iio.get_reader(sys.argv[1])
    for i, im in enumerate(reader):
        framescount += 1
        if framescount % 80 == 0:
            img = Image.fromarray(im.astype('uint8'), 'RGB')
            scale_min = extract_temp_scale(img.rotate(180, expand=True), (11, 0, 80, 25))
            if scale_min != '': workscount += 1
            scale_max = extract_temp_scale(img.rotate(180, expand=True), (11, img.height-26, 80, img.height-1))
            if scale_max != '': workscount += 1
            processed += 1
            print(scale_min, " ", scale_max)

    print("Pulled " + str(workscount) + " of an expected " + str(processed*2) + " numbers")
    sys.exit(0)

    # Find average color of various locations in triangle
    #targets = [ ((346,499),8), ((386,484),8), ((388,514),8), ((374,498),24) ]
    #for target in targets:
    #    aver = get_average_of_circle(img, target[0], target[1])
    #    print("Area around " + str(target[0]) + " (rad " + str(target[1]) + ") is " + str(aver))
    #    print("  We think it's " + str(map_color_to_temp(scale, img.width, aver)) + " deg " + unit)
    
    
        
