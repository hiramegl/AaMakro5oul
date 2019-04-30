#!/bin/sh

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

# ******************************************************************************
# This script starts the Open Stage Control server that is used as a bridge
# between the GUI interface of AaMakro5oul and Ableton Live 9.
#
# Parameters:
# -p 43210             -> http port where the Open Source Control server
#                         will be available to open in a web browser
# -s 127.0.0.1:2720    -> address and port where the OSC messages will be sent
#                         (i.e., where Ableton Live will be listening to)
# -l ".../latest.json" -> path of the AaMakro5oul GUI session file
# -o 2721              -> OSC input port for the Open Stage Control server
#                         (i.e., where Ableton Live will be sending from)
# -m AbletonLive:1,1   -> midi router settings
# -d                   -> debug (log received OSC messages in the console)
# -n                   -> disable default GUI
# -t light             -> use light theme
#
# These parameters should match with the ones found in 'config.txt'
#
# More options at: http://osc.ammd.net/getting-started/
# ******************************************************************************

# configuration
PRODUCT_DIR=AaMakro5oul
HTTP_PORT=43210
OSC_TX_ADDR=127.0.0.1
OSC_TX_PORT=2720
OSC_RX_PORT=2721
MIDI_ROUTE=AbletonLive:1,1

# command
/Applications/open-stage-control-23.app/Contents/MacOS/open-stage-control \
   -l "$HOME/$PRODUCT_DIR/ifc/latest.json" \
   -p $HTTP_PORT \
   -s $OSC_TX_ADDR:$OSC_TX_PORT \
   -o $OSC_RX_PORT \
   -m $MIDI_ROUTE \
   -d \
   -n \
   -t light

