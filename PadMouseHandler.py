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

from BaseHandler import BaseHandler

# ******************************************************************************
# Mousepad commands handler
# ******************************************************************************

class PadMouseHandler(BaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        BaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False # False -> ignore mouse position events (they overflow the log)
        self.config('/pad/mouse', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks(['tools', 'macro/111'])
        self.add_callbacks_pref('pos'         , ['touch', 'xy', 'center'])
        self.add_callbacks_pref('click/left'  , ['1', '2'])
        self.add_callbacks_pref('click/right' , ['1', '2'])
        self.add_callbacks_pref('scroll/left' , ['1', '2', '3', '4'])
        self.add_callbacks_pref('scroll/right', ['1', '2', '3', '4'])
        self.add_callbacks_pref('scroll/up'   , ['1', '2', '3', '4'])
        self.add_callbacks_pref('scroll/down' , ['1', '2', '3', '4'])
        self.add_callbacks_pref('tools/key'   , ['up', 'down', 'left', 'right'])


    def handle(self, _aMessage):
        if (self.m_sCmd == 'pos/center'):
            self.log('> centering pad');
            self.send('/pad/mouse/pos/xy', [0.5, 0.5])

        # managed by a ruby script (UDP server) which transforms OSC messages into physical mouse and keyboard events
        return

