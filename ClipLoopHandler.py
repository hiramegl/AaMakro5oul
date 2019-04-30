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
# Clip Loop commands handler: toggle/duplicate/divide/multiply loop
# ******************************************************************************

class ClipLoopHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/clip/loop', bIgnoreRelease, bLogRxMsgs)
        self.add_callbacks(['toggle', 'duplicate'])
        self.add_callbacks_pref('start' , ['div/2', 'mul/2'])
        self.add_callbacks_pref('middle', ['div/2', 'mul/2'])
        self.add_callbacks_pref('end'   , ['div/2', 'mul/2'])


    def handle(self, _aMessage):
        oClip      = self.sel_clip_slot().clip
        bLooping   = oClip.looping
        nLoopStart = oClip.loop_start
        nLoopEnd   = oClip.loop_end
        nLoopLen   = nLoopEnd - nLoopStart

        if (self.m_sCmd == 'toggle'):
            oClip.looping = not bLooping

        elif (self.m_sCmd == 'start/div/2' and bLooping):
            oClip.loop_start = nLoopStart + (nLoopLen / 2.0)

        elif (self.m_sCmd == 'start/mul/2' and bLooping):
            oClip.loop_start = nLoopStart - nLoopLen

        elif (self.m_sCmd == 'end/div/2' and bLooping):
            oClip.loop_end = nLoopEnd - (nLoopLen / 2.0)

        elif (self.m_sCmd == 'end/mul/2' and bLooping):
            oClip.loop_end = nLoopEnd + nLoopLen

        elif (self.m_sCmd == 'middle/div/2' and bLooping):
            oClip.loop_start = nLoopStart + (nLoopLen / 4.0)
            oClip.loop_end   = nLoopEnd   - (nLoopLen / 4.0)

        elif (self.m_sCmd == 'middle/mul/2' and bLooping):
            oClip.loop_start = nLoopStart - (nLoopLen / 2.0)
            oClip.loop_end   = nLoopEnd   + (nLoopLen / 2.0)

        elif (self.m_sCmd == 'duplicate' and bLooping):
            oClip.duplicate_loop()
            # SeqBeatHandler in order to update the beat grid
            self.update_observers('duplicated_loop')


