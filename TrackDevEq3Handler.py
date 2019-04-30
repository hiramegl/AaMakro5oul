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
# Eq3 audio effect commands handler
# ******************************************************************************

class TrackDevEq3Handler(TrackDevBaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        TrackDevBaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)


    def config_device(self):
        self.m_bLogRxMsgs    = False
        self.m_bLogParamsVal = False # use True for development
        self.m_sDeviceClass  = 'FilterEQ3'

        self.config('/track/dev/eq3', self.m_bIgnoreRelease, self.m_bLogRxMsgs)
        self.m_aCmds = [
            'toggle/dev', # Device On
            'toggle/slp', # Slope (24/48 db)

            'toggle/low', # LowOn
            'toggle/mid', # MidOn
            'toggle/hi',  # HighOn

            'fader/low',  # GainLo
            'fader/mid',  # GainMid
            'fader/hi',   # GainHi

            'fader/flo',  # FreqLo
            'fader/fhi'   # FreqHi
        ]
        self.m_sAutoCmdPrm  = 'fader/low'
        self.m_sAutoCmdTx   = 'fader/low'
        self.m_nAutoCmdMax  = 0.85 # max value for bass should be 0.85 not 1.0!
        self.m_nAutoCmdRst  = 0.85 # reset value for bass should be 0.85 not 0.0!

        # used to manage presets
        self.m_sPresetsBase = 'eq3'
        self.m_sRootId      = 'track_dev_eq3'


    def register_param(self, _sTrackType, _nIdxAbs, _sParam, _sOriginal, _oParam):
        sCmd = None

        if (_sOriginal == 'Device On'):
            sCmd = 'toggle/dev'
        elif (_sOriginal == 'Slope'):
            sCmd = 'toggle/slp'

        elif (_sOriginal == 'LowOn'):
            sCmd = 'toggle/low'
        elif (_sOriginal == 'MidOn'):
            sCmd = 'toggle/mid'
        elif (_sOriginal == 'HighOn'):
            sCmd = 'toggle/hi'

        elif (_sOriginal == 'GainLo'):
            sCmd = 'fader/low'
        elif (_sOriginal == 'GainMid'):
            sCmd = 'fader/mid'
        elif (_sOriginal == 'GainHi'):
            sCmd = 'fader/hi'

        elif (_sOriginal == 'FreqLo'):
            sCmd = 'fader/flo'
        elif (_sOriginal == 'FreqHi'):
            sCmd = 'fader/fhi'

        # 'hParams': {'sCmd': oParam}
        if (sCmd != None):
            self.m_hDevices[_sTrackType][_nIdxAbs]['hParams'][sCmd] = _oParam


    def reset_custom_gui_params(self, _sChannel, _hDevice, _hParams):
        # turn band on
        _hParams['toggle/low'].value = 1.0
        _hParams['toggle/mid'].value = 1.0
        _hParams['toggle/hi'].value  = 1.0

        # reset faders to default value
        _hParams['fader/low'].value = self.m_nAutoCmdRst
        _hParams['fader/mid'].value = self.m_nAutoCmdRst
        _hParams['fader/hi'].value  = self.m_nAutoCmdRst

        # update GUI
        if (_sChannel != None):
            self.send_msg('toggle/low/%s' % (_sChannel), 1.0)
            self.send_msg('toggle/mid/%s' % (_sChannel), 1.0)
            self.send_msg('toggle/hi/%s'  % (_sChannel), 1.0)
            self.send_msg('fader/low/%s'  % (_sChannel), self.m_nAutoCmdRst)
            self.send_msg('fader/mid/%s'  % (_sChannel), self.m_nAutoCmdRst)
            self.send_msg('fader/hi/%s'   % (_sChannel), self.m_nAutoCmdRst)


    def parse_preset_cmd(self, _nIdx):
        if   (_nIdx == 1):
            return 'fader/low'
        elif (_nIdx == 2):
            return 'fader/mid'
        elif (_nIdx == 3):
            return 'fader/hi'
        elif (_nIdx == 4):
            return 'fader/flo'
        elif (_nIdx == 5):
            return 'fader/fhi'
        elif (_nIdx == 6):
            return 'toggle/low'
        elif (_nIdx == 7):
            return 'toggle/mid'
        elif (_nIdx == 8):
            return 'toggle/hi'
        elif (_nIdx == 9):
            return 'toggle/slp'
        else:
            return None


    def parse_preset_val(self, _nIdx, sValue):
        if   (_nIdx == 1):
            return float(sValue) # fader low
        elif (_nIdx == 2):
            return float(sValue) # fader mid
        elif (_nIdx == 3):
            return float(sValue) # fader hi
        elif (_nIdx == 4):
            return float(sValue) # fader flo
        elif (_nIdx == 5):
            return float(sValue) # fader fhi
        elif (_nIdx == 6):
            return 1 if (sValue == 'true') else 0 # toggle low
        elif (_nIdx == 7):
            return 1 if (sValue == 'true') else 0 # toggle mid
        elif (_nIdx == 8):
            return 1 if (sValue == 'true') else 0 # toggle hi
        elif (_nIdx == 9):
            return float(sValue) # toggle slp
        else:
            return None


    def get_preset_value(self, _sCmd, _oValue, _oParam):
        """
                               X                   Y
                               INPUT               OUTPUT
          6 db = 10^(  6/20) = 1.99526203        = 1.0
          0 db = 10^(  0/20) = 1.0               = 0.85
        -14 db = 10^(-14/20) = 0.199526231496888 = 0.501108236125
        -70 db = 10^(-70/20) = 0.00031622799     = 0.0            

        https://mycurvefit.com/ -> best approximation:
        'y = 1.593643 + (-0.02111829 - 1.593643)/(1 + (x/0.7523915)^0.5561272)
        """
        # convert if is gain param
        if (_sCmd == 'fader/low' or
            _sCmd == 'fader/mid' or
            _sCmd == 'fader/hi'):
            return 1.593643 -1.61476129/(1 + (_oValue / 0.7523915) ** 0.5561272)

        """
        Y               X: Preset value
        OUTPUT          INPUT
        0               50
        0.010101010101  52.4
        0.191919191919  121.0
        0.393939393939  307
        0.59595959596   778
        0.79797979798   1970
        1.0             5000
        https://mycurvefit.com/ -> best approximation:
        'y = 13.29612 + (-12.26034 - 13.29612)/(1 + (x/542.9489)^0.03400621)
        """
        # convert if is low freq param
        if (_sCmd == 'fader/flo'):
            return 13.29612 - 25.55646 /(1 + (_oValue / 542.9489) ** 0.03400621)

        """
        Y               X: Preset value
        OUTPUT          INPUT
        0               200
        0.0449438202247 245
        0.269662921348  673
        0.550561797753  2380
        0.662921348315  3950
        0.831460674157  8430
        1.0             18000
        https://mycurvefit.com/ -> best approximation:
        'y = 38.581 + (-38.9372 - 38.581)/(1 + (x/89.80067)^0.01147223)
        """
        # convert if is high freq param
        if (_sCmd == 'fader/fhi'):
            return 38.581 - 77.5182 / (1 + (_oValue / 89.80067) ** 0.01147223)

        # return the same value for the other type of params
        return _oValue


