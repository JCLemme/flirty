import os
import csv
import re
import sys
import math
import datetime
import random



class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __iter__(self):
        yield self.x
        yield self.y


class Color:
    def __init__(self, source):
        self.r = source[0]
        self.g = source[1]
        self.b = source[2]
        self.c = source[3]

    def __iter__(self):
        yield self.r
        yield self.g
        yield self.b
        yield self.a


class Colormap:

