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

import time

from CoreHandler import CoreHandler

# ******************************************************************************
# Transpose effect commands handler
# ******************************************************************************

class TrackTransposeHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/track/transp', bIgnoreRelease, bLogRxMsgs)

        self.m_aCmds = ['incr', 'decr', 'reset']
        for sCmd in self.m_aCmds:
            self.add_callbacks_pref(sCmd, ['selected'])


    def handle(self, _aMessage):
        sCmd         = self.m_aParts[0]
        sTrackIdxRel = self.m_aParts[1]

        if (sTrackIdxRel == 'selected'):
            oSelClipSlot = self.sel_clip_slot()
            if (oSelClipSlot.has_clip == False):
                return # nothing else to do here
            oClip = oSelClipSlot.clip

        # else:
        # check what clip is actually playing in the specified track

        if (sCmd == 'incr'):
            nPitch = oClip.pitch_coarse
            oClip.pitch_coarse = nPitch + 1

        elif (sCmd == 'decr'):
            nPitch = oClip.pitch_coarse
            oClip.pitch_coarse = nPitch - 1

        else: # sCmd == 'reset'
            oClip.pitch_coarse = 0



