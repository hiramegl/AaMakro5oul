```
# ******************************************************************************
# This file is part of the AaMakro5oul project
# (An OSC/MIDI controller for Ableton Live with DJ features)
#
# Full project source: https://github.com/hiramegl/AaMakro5oul
#
# License     : Apache License 2.0
# Full license: https://github.com/hiramegl/AaMakro5oul/blob/master/LICENSE
#
# Copyright 2018, 2019 by Hiram Galicia (hiramegl@yahoo.com)
# http://www.unasystems.com
#
# All rights reserved.
# ******************************************************************************
```

# AaMakro5oul

_OSC/MIDI Controller for Ableton Live 9 with DJ features._


## Features
* 5 Views:
  * Session
  * Clip / Fx
  * Sequencer
  * Keyboard (108 keys, 9 octaves)
  * Mix (for DJ'ing)
* Macro-controls
  * Automatic volume control (increase and decrease)
  * Automatic effect control (increase and decrease dry/wet)
  * Automatic crossfader control (fading from A to B or B to A)
  * 4 channels for automatic effects control (increase or decrease dry/wet)
  * 1 channel for detailed control of effects
* 8 scenes / 8 tracks matrix
* 8 sends and 8 returns control
* Clip loops
* Loop roll
* Loop jump
* Transpose control
* Duplicate clip / scene
* Copy, paste and cut clips
* Multiple clip selection
* Mouse cursor positioning from GUI
* Mouse scrolling from GUI
* Cue/Solo toggle
* Legato toggle
* Session/Arrangement toggle
* Clip/Effects toggle


## Objective
My objective with this project is to develop an Ableton Live controller for DJ'ing with the capability to add and edit
loops on-the-go during gigs. I also wanted to create functions or commands ("macros") that perform many operations
simultaneously, just with the touch of one button.

---

## Installation

In order to install AaMakro5oul, you should install the following dependencies (in this order):
1. Open Stage Control (0.23.0)
1. Ruby
1. Virtual MIDI Port (MAC OS)
1. Deploying scripts (MAC OS)

### 1. Open Stage Control 0.23.0
Open Stage Control is used as a bridge between the AaMakro5oul GUI and Ableton Live. The GUI configuration is saved in the file
'ifc/latest.json' and is loaded when the script 'AaMakro5oul_server.sh' is executed. Open Stage Control has released many new
versions after 0.23.0 but unfortunately I was not cautious enough to download the latest versions and try my 'latest.json'
every time.
Sadly, when I tried the latest versions the GUI did not work at all, but it works fine with 0.23.0. The link to download
Open Stage Control 0.23.0 is here:

[Official Open Stage Control 0.23.0 download](https://github.com/jean-emmanuel/open-stage-control/releases/tag/v0.23.0)

Updating to the latest version of Open Stage Control is in the roadmap.

### Ruby and 'mouse' gem
In order to be able to use some special commands is necessary to install Ruby (scripting language interpreter). If you use
MAC OS then you already have ruby. Furthermore, is necessary to install the gem 'mouse' that 'AaMakro5oul_server.rb' uses.
In order to install the gem you need to run the command 'sudo gem install mouse' in a terminal and accept the installation.
Afterwards, it will be possible to start the script 'AaMakro5oul_server.rb' and have the functionality that it provides.

### Virtual MIDI Port (MAC OS)
A Virtual MIDI Port is necessary in order to be able to use the keyboard view and the drumpad. You can use the following
instructions to create a Virtual MIDI Port (only for MAC OS):
1. Open the application called "Audio MIDI Setup"
2. Activate the "IAC Driver"
3. Create a virtual MIDI port "AbletonLive"
4. Confirm that you virtual MIDI port is actually found by Open Stage Control by running the command "open-stage-control -m list".
5. Select the MIDI Port "AbletonLive" that you just created when configuring your control surface in the "Preferences" dialog
   of your Ableton Live 9.

### Deploying scripts (MAC OS)

1. The root 'AaMakro5oul' directory (containing 'AaMakro5oul.py') shoud be copied inside Ableton Live 9:
```
/Applications/Ableton Live 9 Standard.app/Contents/App-Resources/MIDI Remote Scripts/AaMakro5oul
```

1. The 'AaMakro5oul' subdirectory (containg config.txt) should be copied in your user directory:
```
/Users/<your_user_name>/AaMakro5oul
```

## SW Connections

The sofware connections diagram is this:

![alt text](https://github.com/hiramegl/AaMakro5oul/AaMakro5oul/doc/images/AaMakro5oul_SW_connections.png "AaMakro5oul Software connections")

---

## Hardware

One of the amusing things with this project was to assemble the hardware as well. I bought all parts separated and
afterwards assembled them into one plastic case that I made myself. The parts are:

1. LCD touchscreen (to display and interact with the GUI)
2. Raspberry Pi B+ (the bridge between the touchscreen and the Open Stage Control server)
3. External soundcard Behringer U-Phoria UMC404HD (in order to output the sound to the speakers from Ableton Live)

### Touchscreen

I found a thread with some tips about cheap touchscreens for raspberry Pi.

* [Cheap touch screen for Raspberry Pi](https://www.raspberrypi.org/forums/viewtopic.php?t=36259)

After checking the alternatives I decided to invest in this one:

* [LCD with capacitive touchscreen](https://www.chalk-elec.com/?page_id=1283&_escaped_fragment_=/~/product/category=3094861%2526id=14647633#!/15-6-HDMI-interface-LCD-with-capacitive-touchscreen/p/38127425/category=3094861)

There is a couple of videos in that page showing how to connect the touchscreen with the Raspberry Pi (no rocket science at all).
I selected this touchscreen because it was big, but I'm still looking for a bigger one! :-D

### Raspberry Pi B+

I bought the Raspberry Pi in an electronics store and it was really easy to get started just by watching some videos in youtube.
Again, no rocket science to assemble the Raspberry Pi B+ neither.

### U-Phoria UMC404HD

I was looking for a soundcard with balanced XLR connectors since it was the most common interface in the places I had been playing.
It also has a headphones output for monitoring. I'm really happy with this soundcard and I highly recommend it!

## HW Connections

The hardware connections diagram is this:

![alt text](https://github.com/hiramegl/AaMakro5oul/AaMakro5oul/doc/images/AaMakro5oul_HW_connections.png "AaMakro5oul Hardware connections")

---

## Why _AaMakro5oul_?

### Aa
This is the first project that I program in Python. While developing this project my script used to crash very, very often,
so in order to load it again I needed to scroll in the list of MIDI controllers until I found it, which was time consuming.
Therefore, I put the 'Aa' at the beginning so that I would not need to scroll and just find it quickly.

### Makro
Originally 'M4kro' but I tought it would be more confusing to pronounce, therefore I left it as 'Makro'. Makro is for
"macroinstructions" or "macrocommands", i.e., commands that execute things automatically, like autovolume control, autoeffect
control, build-up automation, rebooting a channel, etc. I want to save time by clicking one button that does everything for me.

### 5oul

I got inspired after watching a couple of videos of two of my all-time favorite DJ's: Paul Van Dyk and Deadmau5.
Indeed, that is the reason why I have the '5' in my DJ name 'Lua5oul' and in my controller, which would be the soul of my mix :-D

  * [Future Music Live Set Up With Deadmau5](https://www.youtube.com/watch?v=GTCqeWu094I)
  * [PAUL VAN DYK - My Sound Set Up At Space Miami](https://www.youtube.com/watch?v=P1zRiRnen5M&feature=youtu.be)


## About the author
My name is Hiram Galicia (hiramegl@yahoo.com) and have a great passion for music and programming.

