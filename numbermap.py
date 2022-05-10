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


class TemperatureMatcher:
    def __init__(self):
        # Load up the Tesseract model and set our temperature finding whitelist
        self.ocr_engine = tesserocr.PyTessBaseAPI()
        self.ocr_engine.SetVariable("tessedit_char_whitelist", "0123456789°FC")

    def __del__(self):
        self.ocr_engine.End()

    def matches_temperature(self, target: str) -> bool:
        # Takes a string and figures out if we consider it a valid temperature 
        # Regex in detail: match entire strings consisting of one to three numbers, a degree
        # symbol, and either an F or C
        return re.match("^[0-9]{1,3}[°][FC]$", target)

    def recognize_text(self, image: Image) -> str:
        # Runs OCR on an image and returns one line of output text
        self.ocr_engine.SetImage(image)
        return self.ocr_engine.GetUTF8Text().replace("\n", "")

    def pad_image(self, image: Image, size: int) -> Image:
        # Pads an image with its perceived background color
        pad_color = image.getpixel((0, 0))
        return ImageOps.expand(image, size, pad_color)

    def generate_candidates(self, image: Image) -> list[Image]:
        # Generate variations of the source image for OCRing
        candidates = []

        # TODO: do we need this many images? is there a better way of generating these images when needed vs before any OCR?

        # Various versions of greyscale images: lumosity based and color channel based
        for grey_image in [image.convert('L')] + list(image.split()):  

            # Both black-on-white and white-on-black versions
            for invert_image in [grey_image, ImageOps.invert(grey_image)]:  

                # The image, as-is
                candidates.append( invert_image )                                                
                
                for thresh in range(100, 220, 20):
                    candidates.append( invert_image.point(lambda p: 255 if p > thresh else 0) )       # Thresholded to either full black or full white

        # Resize images and add a sharpened copy
        bigger_candidates = []

        for candidate in candidates:
            big_candidate = candidate.resize((candidate.width * 8, candidate.height * 8))
            bigger_candidates.append( big_candidate )
            bigger_candidates.append( big_candidate.filter(ImageFilter.EDGE_ENHANCE_MORE) )

        # Shuffle the image array. Since the images are generated in a kind of order above (all from lumosity, all from red...), a bad source 
        # image - a confusing threshold or something - might generate a run of the same wrong number and fuck up the result. (Emphasis on might.)
        random.shuffle(bigger_candidates)

        # And return
        return bigger_candidates

    def get_temperature(self, image: Image) -> str:
        # Grabs the temperature that's written in the image. Source image should be cropped close (~1-4px) to the text inside.

        # Pad the image to make Tesseract's job easier
        image = self.pad_image(image, 16)

        # Generate some variations to try OCR on
        sources = self.generate_candidates(image)

        # See if there's a consensus
        results = Counter()
        desired_results = 10

        for source in sources:
            # Get OCR's take on it
            raw_result = self.recognize_text(source)

            # If the result is a syntactically valid temperature, add it to the results database
            if self.matches_temperature(raw_result): results[raw_result] += 1

            # Check for consensus
            if sum(results.values()) > desired_results:
                print(results)
                # Get the top two answers
                top_matches = results.most_common(2)

                # Assuming there's some matches for us...
                if len(top_matches) > 0:
                    # Return any match with >75% of the total matches
                    if len(top_matches) == 1 or (len(top_matches) > 1 and top_matches[0][1] > (len(results)*0.75)):
                        return top_matches[0][0],

                # If no consensus was achieved, raise our expectations
                desired_results += 10
        
        # If we couldn't reach consensus, return the most common match (or nothing if the OCR completely bombed)
        if sum(results.values()) > 0:
            return results.most_common(1)[0][0]
        else:
            return ""


if __name__ == "__main__":
    # Testing script
    temps = TemperatureMatcher()

    mv = imageio.get_reader(sys.argv[1])
    for i, iio in enumerate(mv):
        img = Image.fromarray(iio.astype('uint8'), 'RGB')
        img = img.rotate(180)
        numberzone = img.crop((16, 0, 70, 16))
        print(temps.get_temperature(numberzone))

