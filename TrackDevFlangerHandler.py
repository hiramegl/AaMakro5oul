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
# Flanger audio effect commands handler
# ******************************************************************************

class TrackDevFlangerHandler(TrackDevBaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        TrackDevBaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)


    def config_device(self):
        self.m_bLogRxMsgs    = False
        self.m_bLogParamsVal = False # use True for development
        self.m_sDeviceClass  = 'Flanger'

        self.config('/track/dev/flan', self.m_bIgnoreRelease, self.m_bLogRxMsgs)
        self.m_aCmds = [
            'toggle/dev',   # toggle device on/off

            'fader/hipass', # Hi Pass
            'fader/drywet', # Dry/Wet

            'fader/dtime',  # Delay Time
            'fader/fback',  # Feedback
            'toggle/polar', # Polarity

            'fader/envmod', # Env. Modulation
            'fader/envatt', # Env. Attack
            'fader/envrel', # Env. Release

            'fader/lamnt',  # LFO Amount
            'select/lwavf', # LFO Waveform

            'fader/freq',   # Frequency
            'fader/srate',  # Sync Rate
            'toggle/sync',  # Sync

            'fader/lphas',  # LFO Phase
            'fader/lspin',  # LFO Spin
            'toggle/lster', # LFO Stereo Mode

            'fader/loffs',  # LFO Offset
            'fader/lwidth', # LFO Width (Random)
        ]


    def register_param(self, _sTrackType, _nIdxAbs, _sParam, _sOriginal, _oParam):
        sCmd = None

        if (_sOriginal == 'Device On'):
            sCmd = 'toggle/dev'

        elif (_sOriginal == 'Hi Pass'):
            sCmd = 'fader/hipass'
        elif (_sOriginal == 'Dry/Wet'):
            sCmd = 'fader/drywet'

        elif (_sOriginal == 'Delay Time'):
            sCmd = 'fader/dtime'
        elif (_sOriginal == 'Feedback'):
            sCmd = 'fader/fback'
        elif (_sOriginal == 'Polarity'):
            sCmd = 'toggle/polar'

        elif (_sOriginal == 'Env. Modulation'):
            sCmd = 'fader/envmod'
        elif (_sOriginal == 'Env. Attack'):
            sCmd = 'fader/envatt'
        elif (_sOriginal == 'Env. Release'):
            sCmd = 'fader/envrel'

        elif (_sOriginal == 'LFO Amount'):
            sCmd = 'fader/lamnt'
        elif (_sOriginal == 'LFO Waveform'):
            sCmd = 'select/lwavf'

        elif (_sOriginal == 'Frequency'):
            sCmd = 'fader/freq'
        elif (_sOriginal == 'Sync Rate'):
            sCmd = 'fader/srate'
        elif (_sOriginal == 'Sync'):
            sCmd = 'toggle/sync'

        elif (_sOriginal == 'LFO Phase'):
            sCmd = 'fader/lphas'
        elif (_sOriginal == 'LFO Spin'):
            sCmd = 'fader/lspin'
        elif (_sOriginal == 'LFO Stereo Mode'):
            sCmd = 'toggle/lster'

        elif (_sOriginal == 'LFO Offset'):
            sCmd = 'fader/loffs'
        elif (_sOriginal == 'LFO Width (Random)'):
            sCmd = 'fader/lwidth'

        # 'hParams': {'sCmd': oParam}
        if (sCmd != None):
            self.m_hDevices[_sTrackType][_nIdxAbs]['hParams'][sCmd] = _oParam


