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

import math
from CoreHandler import CoreHandler

# ******************************************************************************
# Loop Roll commands handler
# ******************************************************************************

class LoopRollHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/loop/roll', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks_pref('bar/curr' , self.beats_list())
        self.add_callbacks_pref('bar/next' , self.beats_list())
        self.add_callbacks_pref('beat/curr', self.beats_list())
        self.add_callbacks_pref('beat/next', self.beats_list())
        self.add_callbacks_pref('pos/curr' , self.beats_list())


    def handle(self, _aMessage):
        oClip = self.song().view.highlighted_clip_slot.clip
        if (oClip.looping):
            oClip.looping = False
            return

        # parse command parts
        sLen   = self.m_aParts[0]
        sPos   = self.m_aParts[1]
        sBeat  = self.m_aParts[2]
        nBeat  = self.beat_value(sBeat)

        nPlayPos  = oClip.playing_position
        nCurrBar  = (math.floor(math.floor(nPlayPos)/ 4.0)) * 4.0
        nNextBar  = (math.floor(math.floor(nPlayPos)/ 4.0) + 1.0) * 4.0
        nCurrBeat = math.floor(nPlayPos)
        nNextBeat = math.floor(nPlayPos) + 1.0

        oClip.looping = True;

        if (sLen == 'bar'):
            if (sPos == 'curr'):
                oClip.position = nCurrBar
                oClip.loop_end = nCurrBar + nBeat
            else: # sPos == 'next'
                oClip.position = nNextBar
                oClip.loop_end = nNextBar + nBeat

        elif (sLen == 'beat'):
            if (sPos == 'curr'):
                oClip.position = nCurrBeat
                oClip.loop_end = nCurrBeat + nBeat
            else: # sPos == 'next'
                oClip.position = nNextBeat
                oClip.loop_end = nNextBeat + nBeat

        else: # sLen == 'pos'
            oClip.position = nPlayPos
            oClip.loop_end = nPlayPos + nBeat


