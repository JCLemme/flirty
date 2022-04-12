import os
import csv
import re
import sys
import math
import datetime
import random



class Point:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __iter__(self):
        yield self.x
        yield self.y


