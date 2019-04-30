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
# Reverb audio effect commands handler
# ******************************************************************************

class TrackDevRevHandler(TrackDevBaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        TrackDevBaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)


    def config_device(self):
        self.m_bLogRxMsgs    = False
        self.m_bLogParamsVal = False # use True for development
        self.m_sDeviceClass  = 'Reverb'

        self.config('/track/dev/rev', self.m_bIgnoreRelease, self.m_bLogRxMsgs)
        self.m_aCmds = [
            'toggle/dev',   # toggle device on/off

            'toggle/locut', # In LowCut On
            'toggle/hicut', # In HighCut On
            'fader/iffreq', # In Filter Freq
            'fader/ifwidt', # In Filter Width
            'fader/predel', # PreDelay

            'toggle/espin', # ER Spin On
            'fader/esrate', # ER Spin Rate
            'fader/esamnt', # ER Spin Amount
            'fader/eshape', # ER Shape

            'select/qual',  # Quality: Eco, Mid, High
            'fader/rsize',  # Room Size
            'fader/stimg',  # Stereo Image

            'toggle/hishe', # HiShelf On
            'fader/hsfreq', # HiShelf Freq
            'fader/hsgain', # HiShelf Gain

            'toggle/loshe', # LowShelf On
            'fader/lsfreq', # LowShelf Freq
            'fader/lsgain', # LowShelf Gain

            'toggle/choru', # Chorus On
            'fader/chrate', # Chorus Rate
            'fader/chamnt', # Chorus Amount

            'fader/dectim', # Decay Time
            'toggle/freez', # Freeze On
            'toggle/flat',  # Flat On
            'toggle/cut',   # Cut On
            'fader/densit', # Density
            'fader/scale',  # Scale

            'fader/elevel', # ER Level
            'fader/diffus', # Diffuse Level
            'fader/drywet', # Dry/Wet
        ]


    def register_param(self, _sTrackType, _nIdxAbs, _sParam, _sOriginal, _oParam):
        sCmd = None

        if (_sOriginal == 'Device On'):
            sCmd = 'toggle/dev'

        elif (_sOriginal == 'In LowCut On'):
            sCmd = 'toggle/locut'
        elif (_sOriginal == 'In HighCut On'):
            sCmd = 'toggle/hicut'
        elif (_sOriginal == 'In Filter Freq'):
            sCmd = 'fader/iffreq'
        elif (_sOriginal == 'In Filter Width'):
            sCmd = 'fader/ifwidt'
        elif (_sOriginal == 'PreDelay'):
            sCmd = 'fader/predel'

        elif (_sOriginal == 'ER Spin On'):
            sCmd = 'toggle/espin'
        elif (_sOriginal == 'ER Spin Rate'):
            sCmd = 'fader/esrate'
        elif (_sOriginal == 'ER Spin Amount'):
            sCmd = 'fader/esamnt'
        elif (_sOriginal == 'ER Shape'):
            sCmd = 'fader/eshape'

        elif (_sOriginal == 'Quality'):
            sCmd = 'select/qual'
        elif (_sOriginal == 'Room Size'):
            sCmd = 'fader/rsize'
        elif (_sOriginal == 'Stereo Image'):
            sCmd = 'fader/stimg'

        elif (_sOriginal == 'HiShelf On'):
            sCmd = 'toggle/hishe'
        elif (_sOriginal == 'HiShelf Freq'):
            sCmd = 'fader/hsfreq'
        elif (_sOriginal == 'HiShelf Gain'):
            sCmd = 'fader/hsgain'

        elif (_sOriginal == 'LowShelf On'):
            sCmd = 'toggle/loshe'
        elif (_sOriginal == 'LowShelf Freq'):
            sCmd = 'fader/lsfreq'
        elif (_sOriginal == 'LowShelf Gain'):
            sCmd = 'fader/lsgain'

        elif (_sOriginal == 'Chorus On'):
            sCmd = 'toggle/choru'
        elif (_sOriginal == 'Chorus Rate'):
            sCmd = 'fader/chrate'
        elif (_sOriginal == 'Chorus Amount'):
            sCmd = 'fader/chamnt'

        elif (_sOriginal == 'Decay Time'):
            sCmd = 'fader/dectim'
        elif (_sOriginal == 'Freeze On'):
            sCmd = 'toggle/freez'
        elif (_sOriginal == 'Flat On'):
            sCmd = 'toggle/flat'
        elif (_sOriginal == 'Cut On'):
            sCmd = 'toggle/cut'
        elif (_sOriginal == 'Density'):
            sCmd = 'fader/densit'
        elif (_sOriginal == 'Scale'):
            sCmd = 'fader/scale'

        elif (_sOriginal == 'ER Level'):
            sCmd = 'fader/elevel'
        elif (_sOriginal == 'Diffuse Level'):
            sCmd = 'fader/difuss'
        elif (_sOriginal == 'Dry/Wet'):
            sCmd = 'fader/drywet'

        # 'hParams': {'sCmd': oParam}
        if (sCmd != None):
            self.m_hDevices[_sTrackType][_nIdxAbs]['hParams'][sCmd] = _oParam


