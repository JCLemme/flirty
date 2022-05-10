import os
import csv
import re
import sys
import math
import datetime
import random
import typing
from collections import Counter

import colormap
import imageio
import pytesseract
import tesserocr
from PIL import Image, ImageFilter, ImageOps


class Regionmap
    def __init__(self):
        self.scale = (0, 0, 0, 0)
        self.temp_min = (0, 0, 0, 0)
        self.temp_max = (0, 0, 0, 0)
        self.interests = []

    # Standard regions: simple crops to get temperature and scale info
    def get_scale(self, image: Image) -> Image:
        return image.crop(self.scale)

    def get_temp_min(self, image: Image) -> Image:
        return image.crop(self.temp_min)

    def get_temp_max(self, image: Image) -> Image:
        return image.crop(self.temp_max)

    # Dynamic regions: getting values from arbitrary shapes in the image
    def calculate_averages(self, image: Image) -> list[float]:
        # For all the masks we defined...
        for region in self.interests:
            # Calculate average color
            
