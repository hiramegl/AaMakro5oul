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

from CoreHandler import CoreHandler

# ******************************************************************************
# Crossfader commands handler
# ******************************************************************************

class CrossCmdHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = False # Do not ignore release events (used to detect play/pause autocross command)
        bLogRxMsgs     = False # False -> do not log fader events (they overflow the log!)
        self.config('/cross/cmd', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks(['fader', 'center', 'delay', 'factor', 'play'])
        self.add_callbacks_pref('fade', ['a', 'b'])
        self.add_callbacks_pref('auto', ['a', 'b'])

        self.m_oCrossfader = self.master().mixer_device.crossfader
        self.reset_fader()


    def disconnect(self):
        self.reset_fader()


    def reset_fader(self):
        self.m_oCrossfader.value = 0.0

        self.m_bAutoOn = False
        self.m_sSide   = 'a' # by default fade to 'a' side
        self.m_nDelay  = 4
        self.m_nFactor = 4

        self.m_nCount   = 0
        self.m_nMsgRate = 5 # 5 x 100 ms => update every half sec

        self.m_nTimeStart  = 0
        self.m_nTimeEnd    = 0
        self.m_nValueStart = 0
        self.m_nValueEnd   = 0
        self.m_nSlope      = 0
        self.m_nMaxBars    = 5

        aCrossMsgs = []
        for nIndex in range(1, self.m_nMaxBars + 1):
            self.append_mul_msg('delay', nIndex, 0.0, aCrossMsgs)
        self.append_mul_msg('delay', self.m_nDelay, 1.0, aCrossMsgs)
        self.append_msg('fader' , 0.0           , aCrossMsgs)
        self.append_msg('factor', self.m_nFactor, aCrossMsgs)

        sMsg = 'CrossCmdHandler, reset_fader, fader_delay_bars_factor, reset'
        self.send_bundle(sMsg, aCrossMsgs)


    def handle(self, _aMessage):
        if (self.m_sCmd == 'fader'):
            self.m_oCrossfader.value = _aMessage[2]
            self.m_bAutoOn = False
            self.send_msg('play', 0.0)

        elif (self.m_sCmd == 'center'):
            self.log('> crossfade center')
            self.m_oCrossfader.value = 0.0
            self.send_msg('fader', 0.0)
            self.send_msg('play', 0.0)
            self.m_bAutoOn = False

        elif (self.m_sCmd == 'delay'):
            self.log('> new delay selected: %f [bars], factor: %s' % (_aMessage[2], self.m_nFactor))
            self.m_nDelay = int(_aMessage[2])
            self.compute_params()

            aCrossMsgs = []
            for nIndex in range(1, self.m_nMaxBars + 1):
                nValue = 1.0 if (nIndex == self.m_nDelay) else 0.0
                self.append_mul_msg('delay', nIndex, nValue, aCrossMsgs)

            sMsg = 'CrossCmdHandler, handle, delay, update'
            self.send_bundle(sMsg, aCrossMsgs)

        elif (self.m_sCmd == 'factor'):
            self.log('> new factor selected: %f [bars], factor: %s' % (self.m_nDelay, _aMessage[2]))
            self.m_nFactor = _aMessage[2]
            self.compute_params()

        elif (self.m_sCmd == 'play'):
            bActive = _aMessage[2] > 0.5
            bFade   = self.m_bAutoOn

            # compute parameters before fading on
            if (bActive == True):
                self.compute_params()

            self.m_bAutoOn = bActive
            self.send_msg('play', _aMessage[2])
            self.log('> play: %d' % (self.m_bAutoOn))

        else:
            sCmd         = self.m_aParts[0]
            self.m_sSide = self.m_aParts[1]

            if (sCmd == 'fade'):
                self.log('> crossfade cmd: %s to %s immediately' % (sCmd, self.m_sSide))
                nValue = -1 if (self.m_sSide == 'a') else 1
                self.m_oCrossfader.value = nValue
                self.send_msg('fader', nValue)
                self.send_msg('play', 0.0)
                self.m_bAutoOn = False

            elif (sCmd == 'auto'):
                self.log('> crossfade cmd: %s to %s in %d bars' % (sCmd, self.m_sSide, self.m_nDelay * self.m_nFactor))
                self.compute_params()
                self.send_msg('play', 1.0)
                self.m_bAutoOn = True


    def compute_params(self):
        nBeatsInABar       = 4.0
        nTempo             = self.song().tempo
        nTimeDelta         = 60.0 / nTempo * nBeatsInABar * self.m_nDelay * self.m_nFactor
        self.m_nTimeStart  = time.time()
        self.m_nTimeEnd    = self.m_nTimeStart + nTimeDelta

        self.m_nValueStart = self.m_oCrossfader.value
        self.m_nValueEnd   = -1 if (self.m_sSide == 'a') else 1
        nValueDelta        = self.m_nValueEnd - self.m_nValueStart

        self.m_nSlope      = nValueDelta / nTimeDelta
        self.m_nCount      = 0 # reset update-gui count

        lLog = (self.m_nTimeStart, self.m_nTimeEnd, self.m_nValueStart, self.m_nValueEnd, self.m_nSlope, nTimeDelta, nValueDelta, nTempo)
        self.log('> time [%f, %f], value [%f, %f], slope: %f, delta time: %f, delta value: %f, tempo: %f' % lLog)


    def update_async_scheduled_tasks(self):
        if (self.m_bAutoOn == False):
            return

        nTime = time.time()

        if (nTime > self.m_nTimeEnd):
            nNewValue    = self.m_nValueEnd
            self.m_bAutoOn = False
            self.send_msg('play', 0.0)
        else:
            nNewValue = self.m_nValueStart + self.m_nSlope * (nTime - self.m_nTimeStart)

        if (self.m_nSlope < 0):
            if (nNewValue < -1.0):
                self.m_bAutoOn = False
                nNewValue      = -1.0
                self.send_msg('play', 0.0)
        else:
            if (nNewValue > 1.0):
                self.m_bAutoOn = False
                nNewValue      = 1.0
                self.send_msg('play', 0.0)

        #self.log('---- cross auto -> time: %f, old: %f, new: %f' % (nTime, self.m_oCrossfader.value, nNewValue))
        self.m_oCrossfader.value = nNewValue

        self.m_nCount += 1
        if (self.m_nCount % self.m_nMsgRate == 0):
            self.send_msg('fader', nNewValue)


