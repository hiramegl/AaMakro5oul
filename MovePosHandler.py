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
# Song position commands handler
# ******************************************************************************

class MovePosHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/move/pos', bIgnoreRelease, bLogRxMsgs)

        self.add_callback_cmd('cue')
        self.add_callbacks_pref('curr/back' , self.beats_list())
        self.add_callbacks_pref('curr/forw' , self.beats_list())
        self.add_callbacks_pref('start/back', self.beats_list())
        self.add_callbacks_pref('start/forw', self.beats_list())
        self.add_callbacks_pref('end/back'  , self.beats_list())
        self.add_callbacks_pref('end/forw'  , self.beats_list())

        self.m_nBackBeatForCue = 16


    def handle(self, _aMessage):
        # parse command parts
        sPos = self.m_aParts[0]

        if (sPos == 'cue'):
            oClip            = self.song().view.highlighted_clip_slot.clip
            nLoopStart       = oClip.loop_start
            oClip.looping    = False
            nSongStart       = oClip.loop_start
            oClip.loop_start = nLoopStart - self.m_nBackBeatForCue
            oClip.looping    = True
            return

        sDir  = self.m_aParts[1]
        sBeat = self.m_aParts[2]
        nBeat = self.beat_value(sBeat)

        if (sPos == 'curr'):
            if (sDir == 'back'):
                self.song().jump_by(-nBeat)
            else: # sDir == 'forw'
                self.song().jump_by(nBeat)
            return # nothing else to do here!

        oClip = self.song().view.highlighted_clip_slot.clip
        bLooping = oClip.looping
        oClip.looping = False
        nStart = oClip.loop_start
        nEnd   = oClip.loop_end

        if (sPos == 'start'):
            if (sDir == 'back'):
                oClip.loop_start = nStart - nBeat
            else: # sDir == 'forw'
                oClip.loop_start = nStart + nBeat

        else: # sPos == 'end'
            if (sDir == 'back'):
                oClip.loop_end = nEnd - nBeat
            else: # sDir == 'forw'
                oClip.loop_end = nEnd + nBeat

        oClip.looping = bLooping


