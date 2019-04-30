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
# AutoFilter audio effect commands handler
# ******************************************************************************

class TrackDevFilterHandler(TrackDevBaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        TrackDevBaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)


    def config_device(self):
        self.m_bLogRxMsgs    = False
        self.m_bLogParamsVal = False # use True for development
        self.m_sDeviceClass  = 'AutoFilter'

        self.config('/track/dev/filter', self.m_bIgnoreRelease, self.m_bLogRxMsgs)
        self.m_aCmds = [
            'toggle/dev',  # toggle on/off device

            'fader/emod',  # Env. Modulation
            'fader/eatt',  # Env. Attack
            'fader/erel',  # Env. Release

            'select/type', # Filter Type
            'select/circ', # Filter Circuit: Clean, OSR, MS2, SMP, PRD (for LowPass & HiPass filter types)
            'select/circ2',# Filter Circuit: Clean, OSR (for BandPass, Notch & Morph filter ypes)
            'toggle/slp',  # Slope: 12/24 dB
            'toggle/quan', # LFO Quantize On
            'select/quan', # LFO Quantize Rate: 0.5, 1, 2, 3, 4,5, 6, 8, 12, 16

            'fader/freq',  # Frequency
            'fader/resnc', # Resonance
            'fader/drive', # Drive

            'fader/lamnt', # LFO amount
            'select/lwav', # LFO waveform

            'fader/lrate', # LFO sync rate
            'toggle/sync', # LFO sync (free/sync)

            'fader/lphas', # LFO phase
            'fader/lspin', # LFO spin
            'toggle/ster', # LFO stereo mode

            'fader/lfreq', # LFO Frequency
            'fader/loffs', # LFO Offset
            'fader/morph', # Morph

            'fader/flo',  # change value for lowpass freq and activate lowpass filter
            'fader/fhi',  # change value for highpass freq and activate highpass filter
        ]
        self.m_sAutoCmdPrm = 'fader/freq'
        self.m_sAutoCmdTx  = 'fader/fhi'


    def register_param(self, _sTrackType, _nIdxAbs, _sParam, _sOriginal, _oParam):
        sCmd = None

        if (_sOriginal == 'Device On'):
            sCmd = 'toggle/dev'

        elif (_sOriginal == 'Env. Modulation'):
            sCmd = 'fader/emod'
        elif (_sOriginal == 'Env. Attack'):
            sCmd = 'fader/eatt'
        elif (_sOriginal == 'Env. Release'):
            sCmd = 'fader/erel'

        elif (_sOriginal == 'Filter Type'):
            sCmd = 'select/type'
        elif (_sOriginal == 'Filter Circuit - LP/HP'):
            sCmd = 'select/circ'
        elif (_sOriginal == 'Filter Circuit - BP/NO/Morph'):
            sCmd = 'select/circ2'
        elif (_sOriginal == 'Slope'):
            sCmd = 'toggle/slp'
        elif (_sOriginal == 'LFO Quantize On'):
            sCmd = 'toggle/quan'
        elif (_sOriginal == 'LFO Quantize Rate'):
            sCmd = 'select/quan'

        elif (_sOriginal == 'Frequency'):
            sCmd = 'fader/freq'
        elif (_sOriginal == 'Resonance'):
            sCmd = 'fader/resnc'
        elif (_sOriginal == 'Drive'):
            sCmd = 'fader/drive'

        elif (_sOriginal == 'LFO Amount'):
            sCmd = 'fader/lamnt'
        elif (_sOriginal == 'LFO Waveform'):
            sCmd = 'select/lwav'

        elif (_sOriginal == 'LFO Sync Rate'):
            sCmd = 'fader/lrate'
        elif (_sOriginal == 'LFO Sync'):
            sCmd = 'toggle/sync'

        elif (_sOriginal == 'LFO Phase'):
            sCmd = 'fader/lphas'
        elif (_sOriginal == 'LFO Spin'):
            sCmd = 'fader/lspin'
        elif (_sOriginal == 'LFO Stereo Mode'):
            sCmd = 'toggle/ster'

        elif (_sOriginal == 'LFO Freq'):
            sCmd = 'fader/lfreq'
        elif (_sOriginal == 'LFO Offset'):
            sCmd = 'fader/loffs'
        elif (_sOriginal == 'Morph'):
            sCmd = 'fader/morph'

        # 'hParams': {'sCmd': oParam}
        if (sCmd != None):
            self.m_hDevices[_sTrackType][_nIdxAbs]['hParams'][sCmd] = _oParam


    def handle_param_msg(self, _sChannel, _sTrackType, _nIdxAbs, _sCmd, _sType, _nGuiValue, _bActive):
        hParams = self.m_hDevices[_sTrackType][_nIdxAbs]['hParams']
        oParam  = None

        oTypeParam = hParams['select/type']
        oFreqParam = hParams['fader/freq']
        nFreqMin   = oFreqParam.min
        nFreqMax   = oFreqParam.max

        if (_sCmd == 'fader' and _sType == 'flo'):
            oTypeParam.value = 0
            oFreqParam.value = (_nGuiValue * (nFreqMax - nFreqMin)) + nFreqMin
            oParam           = oFreqParam

        elif (_sCmd == 'fader' and _sType == 'fhi'):
            oTypeParam.value = 1
            oFreqParam.value = (_nGuiValue * (nFreqMax - nFreqMin)) + nFreqMin
            oParam           = oFreqParam

        else:
            oParam = hParams['%s/%s' % (_sCmd, _sType)]
            oParam.value = self.value_gui_to_param(_nGuiValue, oParam)

        return oParam


    def update_custom_params(self, _hParams, _sChannel, _aTrackMsgs):
        oTypeParam = _hParams['select/type']
        oFreqParam = _hParams['fader/freq']
        nFreqValue = oFreqParam.value
        nFreqMin   = oFreqParam.min
        nFreqMax   = oFreqParam.max
        nValue     = (nFreqValue - nFreqMin) / (nFreqMax - nFreqMin)

        if (oTypeParam.value == 0): # is configured as low pas filter
            self.append_idx_msg('fader/fhi', _sChannel, 0.0   , _aTrackMsgs)
            self.append_idx_msg('fader/flo', _sChannel, nValue, _aTrackMsgs)

        elif (oTypeParam.value == 1): # is configured as low pas filter
            self.append_idx_msg('fader/fhi', _sChannel, nValue, _aTrackMsgs)
            self.append_idx_msg('fader/flo', _sChannel, 1.0   , _aTrackMsgs)

        else: # is configured as some other type of filter
            self.append_idx_msg('fader/fhi', _sChannel, 0.0, _aTrackMsgs)
            self.append_idx_msg('fader/flo', _sChannel, 1.0, _aTrackMsgs)


    def clear_custom_gui_params(self, _sChannel, _aDevMsgs):
        self.append_idx_msg('fader/fhi', _sChannel, 0.0, _aDevMsgs)
        self.append_idx_msg('fader/flo', _sChannel, 1.0, _aDevMsgs)


    def reset_custom_gui_params(self, _sChannel, _hDevice, _hParams):
        oTypeParam = _hParams['select/type']
        oTypeParam.value = 1 # hi pass filter after reseting

        if (_sChannel != None):
            self.send_msg('fader/fhi/%s' % (_sChannel), 0.0)
            self.send_msg('fader/flo/%s' % (_sChannel), 1.0)
            self.send_msg('select/type/%s' % (_sChannel), 1)


