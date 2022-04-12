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

import pytesseract
import tesserocr
from PIL import Image, ImageFilter, ImageOps


tess_api=tesserocr.PyTessBaseAPI()
tess_api.SetVariable("tessedit_char_whitelist", "0123456789°FC" )

def better_extract(image):
    # Compile a set of images to try converting
    sources = []

    # TODO: do we need this many images? is there a better way of generating these images when needed vs before any OCR?

    # Various versions of greyscale images: lumosity based and color channel based
    for grey_image in [image.convert('L')] + list(image.split()):  

        # Both black-on-white and white-on-black versions
        for invert_image in [grey_image, ImageOps.invert(grey_image)]:  

            # The image, as-is
            sources.append( grey_image )                                                
            
            for thresh in range(100, 220, 20):
                sources.append( image.convert('L').point(lambda p: p if p > thresh else 0) )       # Thresholded to either full black or full white

    # Shuffle the image array. Since the images are generated in a kind of order above (all from lumosity, all from red...), a bad source 
    # image - a confusing threshold or something - might generate a run of the same wrong number and fuck up the result. (Emphasis on might.)
    random.shuffle(sources)
    
    # Now that we have more pictures than the Louvre, try and get text from them 
    results = []
    desired_matches = 10
    runs_required = 0
    
    for i, run_image in enumerate(sources):
        run_results = []

        # Pad and enlarge the image, then OCR with and without sharpening 
        run_image_padded = ImageOps.expand(run_image, 16)
        run_image_big = run_image_padded.resize(tuple([8*d for d in run_image_padded.size]))

        tess_api.SetImage(run_image_big)
        run_results.append(tess_api.GetUTF8Text())

        run_image_crunched = run_image_big.resize((run_image_padded.width, run_image_padded.height))
        run_image_sharp = run_image_big.filter(ImageFilter.EDGE_ENHANCE_MORE)

        tess_api.SetImage(run_image_sharp)
        run_results.append(tess_api.GetUTF8Text())

        runs_required += len(run_results)

        # Eliminate anything that doesn't fit our idea of a temperature
        for result in run_results:
            result = result.replace(' ', '')
            result = result.replace('\n', '')
            if re.match("^[0-9]{1,3}[°][FC]$", result): 
                results.append(result)

        # Once we have some successful temperature matches...
        if len(results) > desired_matches:
            # If one value has more than 75% of the total matches, go with that
            check_count = Counter(results)
            top_matches = check_count.most_common(2)

            if top_matches[0][1] > int(len(results)*0.75):
                return top_matches[0][0], 
            
            # Otherwise, set our expectations higher and try again
            desired_matches += 10
    
    # If the conversion failed completely, return a placeholder value
    if len(results) == 0:
        return '-'

    # If we ran out of images, return the most common result
    check_count = Counter(results)
    top_matches = check_count.most_common(1)
    return top_matches[0][0]
