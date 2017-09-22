# Lighthouse 0.0.1
# Author: Timothy Garcia (http://timothygarcia.ca)
# Date: September 2017
# 
# Description:
# Web Interface for Hexbox
# Stores sensor json in a sqlite3 database
# Neopixel visual feedback
#
# Hardware Used:
# Raspberry Pi Zero W / 12-Bit NeoPixel Ring 
# 
#  License: This code is public domain. You can redistribute it and/or modify it under the terms of the GNU Lesser General Public License as published
#  by the Free Software Foundation.  <http://www.gnu.org/licenses/>.
#  Certain libraries used may be under a different license.


import time
from flask import Flask
from flask import request
from flask import jsonify
from neopixel import *
import requests
import sqlite3
import sys


# LED strip configuration:
LED_COUNT      = 12      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 5       # DMA channel to use for generating signal (try 5)
LED_BRIGHTNESS = 15     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_STRIP      = ws.WS2811_STRIP_GRB   # Strip type and colour ordering

strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL, LED_STRIP)
# Intialize the library (must be called once before other functions).
strip.begin()

app = Flask('Lighthouse')

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
	"""Wipe color across display a pixel at a time."""
	for i in range(strip.numPixels()):
		strip.setPixelColor(i, color)
		strip.show()
		time.sleep(wait_ms/1000.0)

@app.route('/scan')
def postSqlite():
    colorWipe(strip, Color(255,255,255))
    strip.show()
    db = sqlite3.connect('hexbox_samples.db')
    hexbox = requests.get('http://hexbox.local/tcs34725.json')
    sample = hexbox.json()
    with db:
        cur = db.cursor()
        cur.execute("CREATE TABLE IF NOT EXISTS logbook (time INT PRIMARY KEY, name TEXT)")
        cur.execute("INSERT INTO logbook (time,name) VALUES (?,?)",(
         str(sample['device_time']),
         sample['device_name']
        ))
        cur.execute("CREATE TABLE IF NOT EXISTS samples (time INT PRIMARY KEY, red_raw INT, green_raw INT, blue_raw INT, clear_raw INT, r INT, g, INT, b INT, c INT, hex TEXT)")
        cur.execute("INSERT INTO samples (time,red_raw,green_raw,blue_raw,clear_raw,r,g,b,c,hex) VALUES (?,?,?,?,?,?,?,?,?,?)",(
         str(sample['device_time']),
         sample['raw']['red'],
         sample['raw']['green'],
         sample['raw']['blue'],
         sample['raw']['clear'],
         sample['compensated']['red'],
         sample['compensated']['green'],
         sample['compensated']['blue'],
         sample['compensated']['clear'],
         str(sample['compensated']['hex'])
        ))
        cur.execute("CREATE TABLE IF NOT EXISTS attributes (time INT PRIMARY KEY, ir INT, cratio REAL, saturation INT, saturation75 INT, is_saturated INT, cpl REAL, max_lux REAL, lux REAL, ct REAL, gain INT, timems INT, atime INT)")
        cur.execute("INSERT INTO attributes (time,ir,cratio,saturation,saturation75,is_saturated,cpl,max_lux,lux,ct,gain,timems,atime) values(?,?,?,?,?,?,?,?,?,?,?,?,?)",(
         str(sample['device_time']),
         sample['attributes']['ir'],
         sample['attributes']['cratio'],
         sample['attributes']['saturation'],
         sample['attributes']['saturation75'],
         sample['attributes']['isSaturated'],
         sample['attributes']['cpl'],
         sample['attributes']['maxlux'],
         sample['attributes']['lux'],
         sample['attributes']['ct'],
         sample['attributes']['gain'],
         sample['attributes']['timems'],
         sample['attributes']['atime']
        ))

        if sample['compensated']['red'] > sample['compensated']['blue'] and sample['compensated']['red'] > sample['compensated']['green']:
         colorWipe(strip, Color(255,0,0))
        elif sample['compensated']['blue'] > sample['compensated']['red'] and sample['compensated']['blue'] > sample['compensated']['green']:
         colorWipe(strip, Color(0,0,255))
        else:
         colorWipe(strip, Color(0,255,0))

        colorWipe(strip, Color(0, 0, 0))
        strip.show()
        
    return 'OK'
    #return jsonify(sample) # Return as JSON

app.run(host='0.0.0.0', port= 8090)