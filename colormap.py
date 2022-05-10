import os
import csv
import re
import sys
import math
import datetime
import random
import typing

from PIL import Image


# Useful for comparisons: this is the largest feasable distance between two colors
MaxColorDist = math.dist( (0, 0, 0, 0), (255, 255, 255, 255) )


class Color:
    def __init__(self, source: tuple):
        self.r = source[0]
        self.g = source[1]
        self.b = source[2]
        self.c = source[3]

    def __iter__(self):
        yield self.r
        yield self.g
        yield self.b
        yield self.a


def is_grey(target: Color, thresh: int=0) -> bool:
    # Check if the channel values of a color match (enough), which means they're a shade of grey
    # TODO: figure out the right way to auto-color tuples
    target = Color(target)

    return abs(target.r - target.g) <= thresh and abs(target.r - target.b) <= thresh and abs(target.g - target.b) <= thresh


class Colormap:
    def __init__(self):
        self.data = []
        self.cache = {}

    def from_image(self, image: Image):
        # Load the colormap from an image, with least intense at (0,0) and most intense at (width,0)
        new_data = []

        for x in range(image.width):
            new_data.append(image.getpixel((x, 0)))

        self.data = new_data
        self.cache = {}

    def intensity_of(self, target: Color, use_cache: bool=True) -> float:
        # Find the approximate place a color would lie on a colorline
        # Zeroth, hit up the cache and see if we've converted this color before
        if use_cache and target in self.cache:
            return self.cache[target]

        # First a simple optimization: if the color is exact, return the index right away
        # TODO: do we care about caching this? Seems like it wouldn't matter...
        if target in self.data:
            intensity = float(self.data.index(target) / len(self.data))
            if use_cache: self.cache[target] = intensity
            return intensity

        # If that didn't work, find the closest color that matches
        # TODO: flip these around - get index first
        close_dist = min(self.data, key = lambda c: math.dist(c, target))
        close = self.data.index(close_dist)
        close_dist = math.dist(close_dist, target) # Oops, forgot to turn the color back into a distance. Should probably be renamed

        # At this point, we know the target color doesn't exactly match a scale color
        # So figure out where the target would be in between colors
        dist_left = (-1 * math.dist(self.data[close-1], target)) if close > 0 else (MaxColorDist)       
        dist_right = (math.dist(self.data[close+1], target)) if close < (len(self.data)-1) else (MaxColorDist)
        next_close_dist = (dist_left) if abs(dist_left) < dist_right else (dist_right)
        
        close_ratio = (close_dist / next_close_dist) * 0.5
        intensity = (close + close_ratio) / len(self.data)

        if use_cache: self.cache[target] = intensity
        return intensity
