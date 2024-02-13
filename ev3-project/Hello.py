#!/usr/bin/env python3

from time import sleep

from ev3dev2.motor import LargeMotor, OUTPUT_A, OUTPUT_B, SpeedPercent, MoveTank
from ev3dev2.sensor import INPUT_1
from ev3dev2.sensor.lego import TouchSensor
from ev3dev2.led import Leds
from ev3dev2.sound import Sound

ts = TouchSensor()
leds = Leds()

sound = Sound()
sound.speak("Go!")
    
firstTime = False
while True:
    if ts.is_pressed:
        if( firstTime == False):
            firstTime = True
            sound.speak("pressed")
        leds.set_color("LEFT", "GREEN")
        leds.set_color("RIGHT", "GREEN")
    else:
        if( firstTime == True):
            firstTime = False
            sound.speak("released")
        leds.set_color("LEFT", "RED")
        leds.set_color("RIGHT", "RED")
    # don't let this loop use 100% CPU
    sleep(0.1)