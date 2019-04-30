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

import time

from TrackDevBaseHandler import TrackDevBaseHandler

# ******************************************************************************
# Beat Repeat audio effect commands handler
# ******************************************************************************

class TrackDevBeatRepeatHandler(TrackDevBaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        TrackDevBaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)


    def config_device(self):
        self.m_bLogRxMsgs    = False
        self.m_bLogParamsVal = False # use True for development
        self.m_sDeviceClass  = 'BeatRepeat'

        self.config('/track/dev/brepeat', self.m_bIgnoreRelease, self.m_bLogRxMsgs)
        self.m_aCmds = [
            'toggle/dev',    # Device On

            'fader/inter',   # Interval (2)
            'fader/offset',  # Offset (3)

            'toggle/repeat', # Repeat (17)

            'fader/chance',  # Chance (1)
            'fader/gate',    # Gate (8)

            'fader/grid',    # Grid (4)
            'toggle/btripl', # Block Triplets (5)

            'fader/variat',  # Variation (6)
            'select/vtype',  # Variation Type (7)

            'fader/pitch',   # Pitch (11)
            'fader/pdecay',  # Pitch Decay (10)

            'fader/volume',  # Volume (13)
            'fader/decay',   # Decay (9)

            'toggle/filter', # Filter On (14)
            'fader/ffreq',   # Filter Freq (15)
            'fader/fwidth',  # Filter Width (16)

            'select/mtype',  # Mix Type (12)

            'bprog/buildup',  # Beat Program: Build-Up drop
            'bprog/breakdw',  # Beat Program: Break-Down drop
            'bprog/next4'  ,  # Beat Program: stop and start other clip in 4 beats

            'push/grid1',     # Grid = 1   bar
            'push/grid2',     # Grid = 1/2 bar
            'push/grid3',     # Grid = 1/4 bar
            'push/griddown',  # Grid down
            'push/gridup',    # Grid up
        ]
        self.m_sAutoCmdPrm  = 'fader/grid' # actually it will never be used
        self.m_sAutoCmdTx   = 'fader/grid' # actually it will never be used
        self.m_nDevToggRst  = 0.0 # turn it off when resetting channel

        # used to manage presets
        self.m_sPresetsBase = 'beatrepeat'
        self.m_sRootId      = 'track_dev_brepeat'


    def register_param(self, _sTrackType, _nIdxAbs, _sParam, _sOriginal, _oParam):
        sCmd = None

        if (_sOriginal == 'Device On'):
            sCmd = 'toggle/dev'

        elif (_sOriginal == 'Interval'):
            sCmd = 'fader/inter'
        elif (_sOriginal == 'Offset'):
            sCmd = 'fader/offset'

        elif (_sOriginal == 'Repeat'):
            sCmd = 'toggle/repeat'

        elif (_sOriginal == 'Chance'):
            sCmd = 'fader/chance'
        elif (_sOriginal == 'Gate'):
            sCmd = 'fader/gate'

        elif (_sOriginal == 'Grid'):
            sCmd = 'fader/grid'
        elif (_sOriginal == 'Block Triplets'):
            sCmd = 'toggle/btripl'

        elif (_sOriginal == 'Variation'):
            sCmd = 'fader/variat'
        elif (_sOriginal == 'Variation Type'):
            sCmd = 'select/vtype'

        elif (_sOriginal == 'Pitch'):
            sCmd = 'fader/pitch'
        elif (_sOriginal == 'Pitch Decay'):
            sCmd = 'fader/pdecay'

        elif (_sOriginal == 'Volume'):
            sCmd = 'fader/volume'
        elif (_sOriginal == 'Decay'):
            sCmd = 'fader/decay'

        elif (_sOriginal == 'Filter On'):
            sCmd = 'toggle/filter'
        elif (_sOriginal == 'Filter Freq'):
            sCmd = 'fader/ffreq'
        elif (_sOriginal == 'Filter Width'):
            sCmd = 'fader/fwidth'

        elif (_sOriginal == 'Mix Type'):
            sCmd = 'select/mtype'

        # 'hParams': {'sCmd': oParam}
        if (sCmd != None):
            self.m_hDevices[_sTrackType][_nIdxAbs]['hParams'][sCmd] = _oParam


    # ------------------------------------------------------
    # Grid parameter values:
    # 0  => 1/256 bar => 1/64 beat
    # 1  => 1/128 bar => 1/32 beat
    # 2  => 1/96  bar => 0.04 beat  [triplet]
    # 3  => 1/64  bar => 1/16 beat
    # 4  => 1/48  bar => 0.08 beat  [triplet]
    # 5  => 1/32  bar => 1/8  beat
    # 6  => 1/24  bar => 0.16 beat  [triplet]
    # 7  => 1/16  bar => 1/4  beat
    # 8  => 1/12  bar => 0.33 beat  [triplet]
    # 9  => 1/8   bar => 1/2  beat
    # 10 => 1/6   bar => 0.66 beat  [triplet]
    # 11 => 1/4   bar => 1    beat
    # 12 => 1/3   bar => 1.5  beats [triplet]
    # 13 => 1/2   bar => 2    beats
    # 14 => 3/4   bar => 3    beats [triplet]
    # 15 => 1     bar => 4    beats
    # ------------------------------------------------------

    def handle_param_msg(self, _sChannel, _sTrackType, _nIdxAbs, _sCmd, _sType, _nGuiValue, _bActive):
        hParams = self.m_hDevices[_sTrackType][_nIdxAbs]['hParams']
        oParam  = None

        if (_sCmd == 'push'):
            oParam     = hParams['fader/grid']
            nGridValue = oParam.value;
            if (_sType == 'grid1'):
                nParamValue = 15 # 1 bar = 4 beats

            elif (_sType == 'grid2'):
                nParamValue = 13 # 1/2 bar = 2 beats

            elif (_sType == 'grid3'):
                nParamValue = 11 # 1/4 bar = 1 beat

            elif (_sType == 'griddown'):
                if (nGridValue == 0):
                    return # already in min value, nothing else to do here
                bTriple = (hParams['toggle/btripl'].value > 0.5)
                if (bTriple == False):
                    nParamValue = nGridValue - 1
                else:
                    nParamValue = (int(nGridValue / 2) * 2) - 1

            elif (_sType == 'gridup'):
                if (nGridValue == 15):
                    return # already in max value, nothing else to do here
                bTriple = (hParams['toggle/btripl'].value > 0.5)
                if (bTriple == False):
                    nParamValue = nGridValue + 1
                else:
                    nParamValue = (int((nGridValue + 1) / 2) * 2) + 1

            nGuiValue = self.value_param_to_gui(nParamValue, oParam)
            self.send_msg('fader/grid/%s' % (_sChannel), nGuiValue)

        else:
            oParam      = hParams['%s/%s' % (_sCmd, _sType)]
            nParamValue = self.value_gui_to_param(_nGuiValue, oParam)

        oParam.value = nParamValue

        return oParam


    def reset_custom_gui_params(self, _sChannel, _hDevice, _hParams):
        # load default values for a beat repeater
        aParamsVals = [
            ['fader/inter'  , 0.78], # 1 Bar
            ['fader/offset' , 0],    # 0
            ['toggle/repeat', 0],    # Off
            ['fader/chance' , 1],    # 100 %
            ['fader/gate'   , 0.41], # 7/16
            ['fader/grid'   , 0.49], # 1/16
            ['toggle/btripl', 0],    # Off
            ['fader/variat' , 0],    # 0
            ['select/vtype' , 0],    # Trigger
            ['fader/pitch'  , 0],    # 0 st
            ['fader/pdecay' , 0],    # 0 %
            ['fader/volume' , 0.85], # 0 %
            ['fader/decay'  , 0],    # 0 %
            ['toggle/filter', 0],    # Off
            ['fader/ffreq'  , 0.51], # 1 kHz
            ['fader/fwidth' , 0.42], # 4
            ['select/mtype' , 0],    # Mix
        ]
        aParamsMsgs = []
        self.add_reset_params(aParamsVals, _hParams, _sChannel, aParamsMsgs)

        if (_sChannel != None):
            sMsg = 'TrackDevBeatRepeatHandler, reset_custom_gui_params, params, reset'
            self.send_bundle(sMsg, aParamsMsgs)


    def add_reset_params(self, _aParamsVals, _hParams, _sChannel, _aMsgs):
        for i in range(len(_aParamsVals)):
            aParam    = _aParamsVals[i]
            sName     = aParam[0]
            nGuiValue = aParam[1]
            oParam = _hParams[sName]
            oParam.value = self.value_gui_to_param(nGuiValue, oParam);

            if (_sChannel != None):
                self.append_idx_msg(sName, _sChannel, nGuiValue, _aMsgs)

    def parse_preset_cmd(self, _nIdx):
        if   (_nIdx == 1):
            return 'fader/chance'
        elif (_nIdx == 2):
            return 'fader/inter'
        elif (_nIdx == 3):
            return 'fader/offset'
        elif (_nIdx == 4):
            return 'fader/grid'
        elif (_nIdx == 5):
            return 'toggle/btripl'
        elif (_nIdx == 6):
            return 'fader/variat'
        elif (_nIdx == 7):
            return 'select/vtype'
        elif (_nIdx == 8):
            return 'fader/gate'
        elif (_nIdx == 9):
            return 'fader/decay'
        elif (_nIdx == 10):
            return 'fader/pdecay'
        elif (_nIdx == 11):
            return 'fader/pitch'
        elif (_nIdx == 12):
            return 'select/mtype'
        elif (_nIdx == 13):
            return 'fader/volume'
        elif (_nIdx == 14):
            return 'toggle/filter'
        elif (_nIdx == 15):
            return 'fader/ffreq'
        elif (_nIdx == 16):
            return 'fader/fwidth'
        elif (_nIdx == 17):
            return 'toggle/repeat'
        else:
            return None


    def parse_preset_val(self, _nIdx, sValue):
        if   (_nIdx == 1):
            return float(sValue) # fader chance
        elif (_nIdx == 2):
            return int(sValue) # fader inter
        elif (_nIdx == 3):
            return int(sValue) # fader offset
        elif (_nIdx == 4):
            return int(sValue) # fader grid
        elif (_nIdx == 5):
            return 1 if (sValue == 'true') else 0 # toggle btripl
        elif (_nIdx == 6):
            return float(sValue) # fader variat
        elif (_nIdx == 7):
            return int(sValue) # select vtype
        elif (_nIdx == 8):
            return int(sValue) # fader gate
        elif (_nIdx == 9):
            return float(sValue) # fader decay
        elif (_nIdx == 10):
            return float(sValue) # fader pdecay
        elif (_nIdx == 11):
            return int(sValue) # fader pitch
        elif (_nIdx == 12):
            return int(sValue) # select mtype
        elif (_nIdx == 13):
            return float(sValue) # fader volume
        elif (_nIdx == 14):
            return 1 if (sValue == 'true') else 0 # toggle filter
        elif (_nIdx == 15):
            return float(sValue) # fader ffreq
        elif (_nIdx == 16):
            return float(sValue) # fader fwidth
        elif (_nIdx == 17):
            return 1 if (sValue == 'true') else 0 # toggle repeat
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
        if (_sCmd == 'fader/volume'):
            return 1.593643 -1.61476129/(1 + (_oValue/0.7523915) ** 0.5561272)

        """
        FilterWidth, min: 0.0, max: 1.0
        X  = Param value, from preset min,max (50, 18000)
        X' = Param value, linearly extrapolated to match min,max (0, 1)
           = return (_oValue - 50)/(18000 - 50)
        Y' = Actual param value when X' is the input

        X      Y'     X'
        50     50     0.0
        100    50.8   0.00278551532033
        500    58.0   0.025069637883
        1000   68.3   0.0529247910864
        2000   94.8   0.108635097493
        4000   183    0.220055710306
        6000   352    0.33147632312
        8000   678    0.442896935933
        10000  1310   0.554317548747
        12000  2520   0.66573816156
        14000  4850   0.777158774373
        16000  9340   0.888579387187
        17000  13000  0.944289693593
        17500  15300  0.972144846797
        18000  18000  1.0

        https://mycurvefit.com/ -> best approximation: Nonlinear -> 4PL, symmetrical sigmoidal
        y = 17.95639 + (-16.59301 - 17.95639)/(1 + (x/2767.385)^0.01967403)
        """
        if (_sCmd == 'fader/ffreq'):
            return 17.95639 - 34.5494 / (1 + (_oValue / 2767.385) ** 0.01967403)

        # return the same value for the other type of params
        return _oValue


    def schedule_beat_sync_task(self, _sDevKey, _nTempo, _nCurrSongTime, _nCurrSongBar, _nCurrSongBeat):
        self.m_bProgUpdating = True

        hSchedule    = {}
        hBeatSchdDev = self.m_hBeatSchdDevs[_sDevKey]
        nFireProgBar = hBeatSchdDev['nFireProgBar']

        # build-up program:
        # Beat | 1 | 2 | 3       | 4
        # -----+------------------------------
        # Bar 1| 1 | 2 | 3       | 4
        # Bar 2| 1 | 2 | 3       | 4
        # Bar 3| 1 | 2 | 1       | 2
        # Bar 4| 1 | 1 | 1/2 1/2 | 1/4 1/4 1/4 1/4

        if (hBeatSchdDev['sType'] == 'buildup'):
            if (_nCurrSongBar == nFireProgBar + 1):
                if (_nCurrSongBeat == 1):
                    hSchedule['4 beats']  = [time.time(), 1] # turn device on, set grid to 1 bar (4 beats)

            elif (_nCurrSongBar == nFireProgBar + 3):
                if (_nCurrSongBeat == 1):
                    hSchedule['2 beats']  = [time.time(), 2] # set grid to 1/2 bar (2 beats)

            elif (_nCurrSongBar == nFireProgBar + 4):
                if (_nCurrSongBeat == 1):
                    hSchedule['1 beat']   = [time.time(), 3] # set grid to 1/4 bar (1 beat)

                elif (_nCurrSongBeat == 3):
                    nBeatDelta            = 60.0 / _nTempo   # in seconds
                    hSchedule['1/2 beat'] = [time.time(), 4] # set grid to 1/8 bar (1/2 beat)
                    hSchedule['1/4 beat'] = [time.time() + nBeatDelta * 0.75, 5] # set grid to 1/16 bar (1/4 beat)

                elif (_nCurrSongBeat == 4):
                    nBeatDelta            = 60.0 / _nTempo   # in seconds
                    hSchedule['off']      = [time.time() + nBeatDelta * 0.70, 6] # turn device off
                    self.add_prog_schedule(_sDevKey, hBeatSchdDev, hSchedule)
                    return True # done with the program

            self.add_prog_schedule(_sDevKey, hBeatSchdDev, hSchedule)
            return False # not done until the last program beat is executed

        elif (hBeatSchdDev['sType'] == 'breakdw'):
            self.m_bProgUpdating = False
            return True # not yet implemented

        elif (hBeatSchdDev['sType'] == 'next4'):
            if (_nCurrSongBar == nFireProgBar + 4):
                if (_nCurrSongBeat == 2):
                    hSchedule['off'] = [time.time(), 11] # start the other clips
                    self.add_prog_schedule(_sDevKey, hBeatSchdDev, hSchedule)
                    self.log('> done programming, execution about to start ...')
                    return True # done with the program

        elif (hBeatSchdDev['sType'] == 'next8'):
            if (_nCurrSongBar == nFireProgBar + 8):
                if (_nCurrSongBeat == 2):
                    hSchedule['off'] = [time.time(), 11] # start the other clips
                    self.add_prog_schedule(_sDevKey, hBeatSchdDev, hSchedule)
                    self.log('> done programming, execution about to start ...')
                    return True # done with the program

            return False


    def add_prog_schedule(self, _sDevKey, _hBeatSchdDev, _hSchedule):
        hParams                        = _hBeatSchdDev['hDevice']['hParams']
        hProgSchdDev                   = {}
        hProgSchdDev['oDevParam']      = hParams['toggle/dev']
        hProgSchdDev['oRepeatParam']   = hParams['toggle/repeat']
        hProgSchdDev['oGridParam']     = hParams['fader/grid']
        hProgSchdDev['oVariatParam']   = hParams['fader/variat']
        hProgSchdDev['oPitchParam']    = hParams['fader/pitch']
        hProgSchdDev['oPDecayParam']   = hParams['fader/pdecay']
        hProgSchdDev['oVolumeParam']   = hParams['fader/volume']
        hProgSchdDev['oDecayParam']    = hParams['fader/decay']
        hProgSchdDev['oFilterParam']   = hParams['toggle/filter']
        hProgSchdDev['oFFreqParam']    = hParams['fader/ffreq']
        hProgSchdDev['oFWidthParam']   = hParams['fader/fwidth']
        hProgSchdDev['oMixParam']      = hParams['select/mtype']
        hProgSchdDev['hDevice']        = _hBeatSchdDev['hDevice']
        hProgSchdDev['hSchedule']      = _hSchedule
        self.m_hProgSchdDevs[_sDevKey] = hProgSchdDev

        self.m_bProgRunOn    = True
        self.m_bProgUpdating = False


    # ------------------------------------------------------
    # Grid parameter values:
    # 0  => 1/256 bar => 1/64 beat
    # 1  => 1/128 bar => 1/32 beat
    # 2  => 1/96  bar => 0.04 beat  [triplet]
    # 3  => 1/64  bar => 1/16 beat
    # 4  => 1/48  bar => 0.08 beat  [triplet]
    # 5  => 1/32  bar => 1/8  beat
    # 6  => 1/24  bar => 0.16 beat  [triplet]
    # 7  => 1/16  bar => 1/4  beat
    # 8  => 1/12  bar => 0.33 beat  [triplet]
    # 9  => 1/8   bar => 1/2  beat
    # 10 => 1/6   bar => 0.66 beat  [triplet]
    # 11 => 1/4   bar => 1    beat
    # 12 => 1/3   bar => 1.5  beats [triplet]
    # 13 => 1/2   bar => 2    beats
    # 14 => 3/4   bar => 3    beats [triplet]
    # 15 => 1     bar => 4    beats
    # ------------------------------------------------------

    def execute_beat_program_step(self, _nExecIdx, _sDevKey):
        hProgSchdDev = self.m_hProgSchdDevs[_sDevKey]

        if (_nExecIdx == 1):
            # set constant parameters
            hProgSchdDev['oDevParam'].value    = 1    # turn device on
            hProgSchdDev['oRepeatParam'].value = 1    # turn repeat on
            hProgSchdDev['oFilterParam'].value = 1    # turn filter on

            hProgSchdDev['oVariatParam'].value = 0    # turn variation off
            hProgSchdDev['oPitchParam'].value  = 0    # turn pitch down off
            hProgSchdDev['oPDecayParam'].value = 0    # turn pitch decay off
            hProgSchdDev['oVolumeParam'].value = 0.85 # 0 dB volume
            hProgSchdDev['oDecayParam'].value  = 0    # turn volume decay off
            hProgSchdDev['oMixParam'].value    = 1    # use 'Ins' mix mode

            # variable parameters
            hProgSchdDev['oGridParam'].value   = 15   # set grid to 1 bar [4 beats]
            hProgSchdDev['oFFreqParam'].value  = 0.6
            hProgSchdDev['oFWidthParam'].value = 8.0

            # toggle device button on in the remote GUI
            self.send_msg('toggle/dev/%s' % (hProgSchdDev['hDevice']['sChannel']), 1.0)

        elif (_nExecIdx == 2):
            hProgSchdDev['oGridParam'].value = 13 # set grid to 1/2 bar [2 beats]
            hProgSchdDev['oFFreqParam'].value  = 0.70

        elif (_nExecIdx == 3):
            hProgSchdDev['oGridParam'].value = 11 # set grid to 1/4 bar [1 beat]
            hProgSchdDev['oFFreqParam'].value  = 0.75

            # we could dispatch an event to fire clips in TrackClipHandler but instead
            # we fire them here for performance's sake (is faster)

            # launch the next clips
            aNextClips = self.next_clips()
            for aNextClip in aNextClips:
                oTrack        = self.get_track(aNextClip[0])
                aAllClipSlots = oTrack.clip_slots
                oClipSlot     = aAllClipSlots[aNextClip[1]]
                oClipSlot.fire()

            # TrackClipHandler: clear next clips since we have used them now
            self.update_observers('next_clips_clear')

        elif (_nExecIdx == 4):
            hProgSchdDev['oGridParam'].value = 9 # set grid to 1/8 bar [1/2 beat]
            return False # not done yet, after this step we will execute step 5

        elif (_nExecIdx == 5):
            hProgSchdDev['oGridParam'].value = 7 # set grid to 1/16 bar [1/4 beat]

        elif (_nExecIdx == 6):
            # reset constant parameters
            hProgSchdDev['oDevParam'].value    = 0 # turn device off
            hProgSchdDev['oRepeatParam'].value = 0 # turn repeat off
            hProgSchdDev['oFilterParam'].value = 0 # turn filter off

            # toggle device button off in the remote GUI
            self.send_msg('toggle/dev/%s' % (hProgSchdDev['hDevice']['sChannel']), 0.0)

        elif (_nExecIdx == 11):
            # we could dispatch an event to fire clips in TrackClipHandler but instead
            # we fire them here for performance's sake (is faster)

            # launch the next clips
            aNextClips = self.next_clips()
            for aNextClip in aNextClips:
                oTrack        = self.get_track(aNextClip[0])
                aAllClipSlots = oTrack.clip_slots
                oClipSlot     = aAllClipSlots[aNextClip[1]]
                oClipSlot.fire()

            # TrackClipHandler: clear next clips since we have used them now
            self.update_observers('next_clips_clear')

        return True # done


