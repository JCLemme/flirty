#!/usr/bin/env python3

import os
import csv
import re
import sys
import math
import datetime
import random

import imageio
import pytesseract
import numpy as np
from PIL import Image, ImageFilter, ImageOps


# Scale and color manipulation
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
        

def extract_temp_scale(src):
    # Rotate, crop, and crush colors
    #textread = src.rotate(90, expand=True)
    textread = src
    textread = textread.crop((0, 0, 100, textread.height-1))
    textread = textread.convert('L')
    textread = textread.point( lambda p: 255 if p > 100 else 0 )
    #textread.show()

    # OCR that bitch
    print(pytesseract.image_to_data(textread))
    scale_text = pytesseract.image_to_string(textread).split('\n')
    scale_text = [ t.replace(' ', '') for t in scale_text if t ]
    
    # Did we end up with two numbers?
    if len(scale_text) != 2: return (0, 0), ''

    # Extract numbers, onvert to integer, and return as tuple plus unit
    try:
        temp_scale = ( int(re.sub('[^0-9]', '', scale_text[1])), int(re.sub('[^0-9]', '', scale_text[0])) )
        temp_unit = scale_text[0][-1:]
        return temp_scale, (temp_unit) if temp_unit.isalpha() else ('')
    except ValueError:
        return (0,0), ''
    

def map_color_to_temp(scale, width, color):
    return scale[0] + ( color / width ) * (scale[1]-scale[0])




# -----------------------------------------------------------------------------------
# Main function
if __name__ == "__main__":

    # This hardcoded main function was written to work on a handful of specific thermal camera videos.
    # Its operation should be straightforward enough to understand and modify to suit your needs.
    # That being said, if you run this script just on whatever video, the results will be meaningless (and it might crash!)

    # Open movie file
    mov = imageio.get_reader(sys.argv[1])
    framecount = 0

    # Then make a CSV to write the results to
    datafile = open(sys.argv[2], 'w')
    datacsv = csv.writer(datafile)

    # We love hardcoding 
    datacsv.writerow(['frame', 'min_temp', 'max_temp', 'temp_unit', 'a_raw', 'a_norm', 'b_raw', 'b_norm', 'c_raw', 'c_norm', 'd_raw', 'd_norm'])

    # Every 75th frame we read...
    for i, iio_img in enumerate(mov):
        if framecount % 75 == 0:
            # Convert from ImageIO frame to PIL image
            img = Image.fromarray(iio_img.astype('uint8'), 'RGB')
            img = img.rotate(180)

            # Get scale
            scale, unit = extract_temp_scale(img)
            print(scale)

            img = img.rotate(-90, expand=True)

            # Find average color of various (hardcoded) locations in triangle
            targets = [ ((346,499),8), ((386,484),8), ((388,514),8), ((374,498),24) ]
            avers = []
            for target in targets:
                aver = get_average_of_circle(img, target[0], target[1])
                if unit != '': norm = map_color_to_temp(scale, img.width, aver)
                else: norm = 0
                print("Area around " + str(target[0]) + " (rad " + str(target[1]) + ") is " + str(aver))
                print("  We think it's " + str(norm) + " deg " + unit)
                avers.append((aver, norm))

            datacsv.writerow([framecount, scale[0], scale[1], unit, avers[0][0], avers[0][1], avers[1][0], avers[1][1], avers[2][0], avers[2][1], avers[3][0], avers[3][1] ])
        framecount += 1

    datafile.close()


            
            
        
