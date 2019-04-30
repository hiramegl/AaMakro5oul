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

from TrackDevBaseHandler import TrackDevBaseHandler

# ******************************************************************************
# Chorus audio effect commands handler
# ******************************************************************************

class TrackDevChorusHandler(TrackDevBaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        TrackDevBaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)


    def config_device(self):
        self.m_bLogRxMsgs    = False
        self.m_bLogParamsVal = False # use True for development
        self.m_sDeviceClass  = 'Chorus'

        self.config('/track/dev/chor', self.m_bIgnoreRelease, self.m_bLogRxMsgs)
        self.m_aCmds = [
            'toggle/dev',   # toggle device on/off

            'fader/d1time', # Delay 1 Time
            'fader/d1hi'  , # Delay 1 HiPass

            'fader/d2time', # Delay 2 Time
            'select/d2mode',# Delay 2 Mode: Off, Fix Mod (0, 1, 2)

            'toggle/linkon',# Link On

            'fader/lamnt',  # LFO Amount
            'fader/lrate',  # LFO Rate
            'toggle/lext',  # LFO Extend On

            'fader/feedbk', # Feedback
            'toggle/polar', # Polarity: -, + (0, 1)
            'fader/drywet', # Dry/Wet
        ]


    def register_param(self, _sTrackType, _nIdxAbs, _sParam, _sOriginal, _oParam):
        sCmd = None

        if (_sOriginal == 'Device On'):
            sCmd = 'toggle/dev'

        elif (_sOriginal == 'Delay 1 Time'):
            sCmd = 'fader/d1time'
        elif (_sOriginal == 'Delay 1 HiPass'):
            sCmd = 'fader/d1hi'

        elif (_sOriginal == 'Delay 2 Time'):
            sCmd = 'fader/d2time'
        elif (_sOriginal == 'Delay 2 Mode'):
            sCmd = 'select/d2mode'

        elif (_sOriginal == 'Link On'):
            sCmd = 'toggle/linkon'

        elif (_sOriginal == 'LFO Amount'):
            sCmd = 'fader/lamnt'
        elif (_sOriginal == 'LFO Rate'):
            sCmd = 'fader/lrate'
        elif (_sOriginal == 'LFO Extend On'):
            sCmd = 'toggle/lext'

        elif (_sOriginal == 'Feedback'):
            sCmd = 'fader/feedbk'
        elif (_sOriginal == 'Polarity'):
            sCmd = 'toggle/polar'

        elif (_sOriginal == 'Dry/Wet'):
            sCmd = 'fader/drywet'

        # 'hParams': {'sCmd': oParam}
        if (sCmd != None):
            self.m_hDevices[_sTrackType][_nIdxAbs]['hParams'][sCmd] = _oParam


