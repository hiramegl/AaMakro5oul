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
# Echo audio effect (Ping-Pong delay) commands handler
# ******************************************************************************

class TrackDevEchoHandler(TrackDevBaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        TrackDevBaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)


    def config_device(self):
        self.m_bLogRxMsgs     = False
        self.m_bLogParamsVal  = False # use True for development
        self.m_sDeviceClass   = 'AudioEffectGroupDevice'
        self.m_sDeviceNamePat = 'EchoOut'

        self.config('/track/dev/echo', self.m_bIgnoreRelease, self.m_bLogRxMsgs)
        self.m_aCmds = [
            'toggle/dev',   # Device On
            'fader/effect', # Macro 1, Chain Selector
            'fader/beatdl', # Macro 2, Beat Delay
            'fader/drywet', # Macro 3, Dry/Wet
            'fader/feedbk', # Macro 4, Feedback
            'fader/ffreq',  # Macro 5, Filter Freq
            'fader/fwidt',  # Macro 6, Filter Width
            'fader/mode',   # Macro 7, Mode
            'fader/tdelay', # Macro 8, Time Delay
            'push/echoout', # maximum effect for echoing out
        ]
        self.m_sAutoCmdPrm = 'fader/effect'
        self.m_sAutoCmdTx  = 'fader/effect'


    def register_param(self, _sTrackType, _nIdxAbs, _sParam, _sOriginal, _oParam):
        sCmd = None

        if (_sOriginal == 'Device On'):
            sCmd = 'toggle/dev'
        elif (_sOriginal == 'Macro 1'):
            sCmd = 'fader/effect'
        elif (_sOriginal == 'Macro 2'):
            sCmd = 'fader/beatdl'
        elif (_sOriginal == 'Macro 3'):
            sCmd = 'fader/drywet'
        elif (_sOriginal == 'Macro 4'):
            sCmd = 'fader/feedbk'
        elif (_sOriginal == 'Macro 5'):
            sCmd = 'fader/ffreq'
        elif (_sOriginal == 'Macro 6'):
            sCmd = 'fader/fwidt'
        elif (_sOriginal == 'Macro 7'):
            sCmd = 'fader/mode'
        elif (_sOriginal == 'Macro 8'):
            sCmd = 'fader/tdelay'

        # 'hParams': {'sCmd': oParam}
        if (sCmd != None):
            self.m_hDevices[_sTrackType][_nIdxAbs]['hParams'][sCmd] = _oParam


    def handle_param_msg(self, _sChannel, _sTrackType, _nIdxAbs, _sCmd, _sType, _nGuiValue, _bActive):
        hParams = self.m_hDevices[_sTrackType][_nIdxAbs]['hParams']
        oParam  = None

        if (_sCmd == 'push'):
            oParam      = hParams['fader/effect']
            nParamValue = 127
            self.send_msg('fader/effect/%s' % (_sChannel), 1.0)

        else:
            oParam      = hParams['%s/%s' % (_sCmd, _sType)]
            nParamValue = self.value_gui_to_param(_nGuiValue, oParam)

        oParam.value = nParamValue

        return oParam


