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

from CoreHandler import CoreHandler

# ******************************************************************************
# Loop Jump commands handler
# ******************************************************************************

class LoopJumpHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/loop/jump', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks_pref('start/back', self.beats_list())
        self.add_callbacks_pref('start/forw', self.beats_list())
        self.add_callbacks_pref('end/back'  , self.beats_list())
        self.add_callbacks_pref('end/forw'  , self.beats_list())
        self.add_callbacks_pref('pos/back'  , self.beats_list())
        self.add_callbacks_pref('pos/forw'  , self.beats_list())


    def handle(self, _aMessage):
        oClip = self.song().view.highlighted_clip_slot.clip
        if (oClip.looping == False):
            return

        sPos  = self.m_aParts[0]
        sDir  = self.m_aParts[1]
        sBeat = self.m_aParts[2]
        nBeat = self.beat_value(sBeat)

        nLoopStart = oClip.loop_start
        nLoopEnd   = oClip.loop_end

        if (sPos == 'start'):
            if (sDir == 'back'):
                oClip.loop_start = nLoopStart - nBeat
            else: # sDir == 'forw'
                oClip.loop_start = nLoopStart + nBeat

        elif (sPos == 'end'):
            if (sDir == 'back'):
                oClip.loop_end = nLoopEnd - nBeat
            else: # sDir == 'forw'
                oClip.loop_end = nLoopEnd + nBeat

        else: # sPos == 'pos'
            if (sDir == 'back'):
                oClip.loop_start = nLoopStart - nBeat
                oClip.loop_end   = nLoopEnd   - nBeat
            else: # sDir == 'forw'
                oClip.loop_end   = nLoopEnd   + nBeat
                oClip.loop_start = nLoopStart + nBeat


