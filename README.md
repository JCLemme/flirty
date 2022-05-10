# flirty
Extract temperature information from thermal camera stills
![Example](/doc/banner_small.PNG)

## What can it do 

The idea here is to get numeric data from thermal camera images. Thermal cameras use a meaningless bullshit color scale for temperature, and if you convert a thermal camera still to greyscale the easy way (lumosity) you'll get a useless result where the greys have no correlation to temperature. In addition, the temperatures this scale refers to change frame to frame, and the only indication of this are two **really poorly** rendered numbers at either end.

These Python scripts will beat images like that into crunchable data. 

## This doesn't look like a finished product 

It's not, so

## What can I do with this

`flirty.py` is the original data extractor script that I wrote. It's written to work on a specific set of input videos but if you need to do something similar it's a jumping off point.

`colormap.py` includes functions that desaturate an image according to an arbitrary gradient of colors. 

`numbermap.py` fetches temperature min/max values from an image via OCR. Reliably, even, which took way more work than was worth.

The rest is yet to be made useful, but eventually there will be a script like `flirty` that isn't hardcoded and uses the new functions. The capstone project I was writing this for concluded, so motivation is low at the moment.
