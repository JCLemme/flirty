
import os
import csv
import re
import sys
import math
import datetime
import random
import typing

import imageio
import pytesseract
from PIL import Image, ImageFilter, ImageOps

from utility import Point, Color, point_delta


# Useful for comparisons: this is the largest feasable distance between two colors
MaxColorDist = math.dist( (0, 0, 0, 0), (255, 255, 255, 255) )

def extract_scale(image: Image, start: Point, stop: Point) -> list[Color]:
    # We're trying, essentially, to "sample" a given line of the image and store it
    scale = []
    delta = point_delta(start, stop)
    cursor = Point(start.x, start.y)

    while cursor != stop:
        scale.append(image.getpixel(cursor))
        cursor = Point( cursor[0] + delta[0], cursor[1] + delta[1] )

    return scale


def map_color_to_scale(scale: list[Color], target: Color) -> float:
    # Find the approximate place a color would lie on a colorline
    # First a simple optimization: if the color is exact, return the index right away
    if target in scale:
        return float(scale.index(target))

    # If that didn't work, find the closest color that matches
    close = min(scale, key = lambda c: math.dist(c, target))
    
    # At this point, we know the target color doesn't exactly match a scale color
    # So figure out where the target would be in between colors
    dist_left = (-1 * math.dist(scale[close-1], target)) if close > 0 else (MaxColorDist)       
    dist_right = (math.dist(scale[close+1], target)) if close < len(scale) else (MaxColorDist)
    next_close_dist = (dist_left) if abs(dist_left) < dist_right else (dist_right)
    
    close_dist = math.dist(scale[close], target) 
    close_ratio = (close_dist / next_close_dist) / 0.5
    return close_dist + close_ratio 


def scaled_color_to_grey(scale: list[Color], index: float) -> Color:
    # Generate a greyscale value for a given color somewhere on a colorline
    intensity = (index / len(scale)) * 255
    return Color(intensity, intensity, intensity, 255)


def colormap_image(image: Image, scale: list[Color]) -> Image:
    # Convert an image to greyscale provided a colorline
    result = Image.new('RGBA', (image.width, image.height))

    for x in image.width:
        for y in image.height:
            result.putpixel( (x, y), scaled_color_to_grey(scale, map_color_to_scale(scale, image.getpixel((x, y)))))

    return result
