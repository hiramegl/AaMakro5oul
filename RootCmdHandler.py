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
# Root handler: dummy handler that does nothing but register calls
# ******************************************************************************

class RootCmdHandler(BaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        BaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        # do not log these messages
        self.m_bLogRxMsgs = False

        # dummy callback handlers
        self.add_callback('/root')
        self.add_callback('/label')
        self.add_callback('/session/tools')
        self.add_callback('/session/controller/%s' % (self.m_sProductName))
        self.add_callback('/pad/mouse/pos/song')


