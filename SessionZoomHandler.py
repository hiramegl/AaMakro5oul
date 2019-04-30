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
# Session Zoom commands handler
# ******************************************************************************

class SessionZoomHandler(BaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        BaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/session/zoom', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks(['in', 'out'])


    def handle(self, _aMessage):
        # managed by a ruby script (UDP server) which transforms
        # OSC messages into physical keyboard strokes
        return

