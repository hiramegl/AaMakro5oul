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

from math import sqrt
import os
import time
import datetime
import Live
from pytagger import ID3v2

# ******************************************************************************
# Base handler to provide logging, alert, OSC communications and
# general Ableton Live accessors. Implements observer and observable patterns
# ******************************************************************************

class BaseHandler:

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        self.m_oCtrlInstance  = _oCtrlInstance
        self.m_oOscServer     = _oOscServer
        self.m_oCallbackMgr   = _oOscServer.callbackManager
        self.m_hConfig        = _hConfig

        self.m_sProductName   = _hConfig['sProductName']
        self.m_sProductDir    = _hConfig['sProductDir']
        self.m_bLog           = _hConfig['bLog']
        self.m_bLogRxMsgs     = _hConfig['bLogRxMsgs']

        self.m_aObservers     = []
        self.m_bIgnoreRelease = False


    def disconnect(self):
        return # subclasses should implement this method


    # Observable methods *******************************************************

    def add_observer(self, _oObserver):
        self.m_aObservers.append(_oObserver)


    def remove_observer(self, _oObserver):
        self.m_aObservers.remove(_oObserver)


    def update_observers(self, _sEvent, _oArgs = None):
        for oObserver in self.m_aObservers:
            oObserver.update(_sEvent, _oArgs)


    # Observer methods *********************************************************

    def update(self, _sEvent, _oArgs = None):
        return # subclasses should implement this method


    # OSC communication methods ************************************************

    def config(self, _sBaseAddress, _bIgnoreRelease, _bLogRxMsgs = False):
        self.m_sBaseAddress   = _sBaseAddress
        self.m_bIgnoreRelease = _bIgnoreRelease
        self.m_bLogRxMsgs     = _bLogRxMsgs


    def add_callback(self, _sAddress):
        #self.log('> adding handler for: %s' % (_sAddress))
        self.m_oCallbackMgr.add(self.handle_message, _sAddress)


    def add_callbacks(self, _aCmds):
        for sCmd in _aCmds:
            self.add_callback('%s/%s' % (self.m_sBaseAddress, sCmd))


    def add_callbacks_pref(self, _sPref, _aCmds):
        for oCmd in _aCmds:
            self.add_callback("%s/%s/%s" % (self.m_sBaseAddress, _sPref, str(oCmd)))


    def add_callback_cmd(self, _sCmd):
        self.add_callback("%s/%s" % (self.m_sBaseAddress, _sCmd))


    # _aMessage[0] -> address
    # _aMessage[1] -> parameter type
    # _aMessage[2] -> parameter value
    def handle_message(self, _aMessage):
        if (self.m_bIgnoreRelease == True and _aMessage[2] == 0.0):
            return

        self.m_sAddr  = _aMessage[0]
        self.m_sCmd   = _aMessage[0].replace('%s/' % (self.m_sBaseAddress), '')
        self.m_aParts = self.m_sCmd.split('/')

        if (self.m_bLogRxMsgs):
            self.log("=> %s: %s | %s | %s" % (self.m_sBaseAddress, self.m_sCmd, str(_aMessage[1]), str(_aMessage[2])))

        self.handle(_aMessage)


    def send(self, _sAddress, _sMessage):
        self.m_oOscServer.sendOSC(_sAddress, _sMessage)


    def send_msg(self, _sAddress, _oMessage):
        self.m_oOscServer.sendOSC('%s/%s' % (self.m_sBaseAddress, _sAddress), _oMessage)


    def send_bundle(self, _sLogMsg, _aMessages):
        self.log('> send_bundle: %s (%d messages)' % (_sLogMsg, len(_aMessages)))
        self.m_oOscServer.sendBundle(_aMessages)


    def append_msg(self, _sAddress, _nValue, _aMsgs):
        _aMsgs.append(['%s/%s' % (self.m_sBaseAddress, _sAddress), [_nValue]])


    def append_idx_msg(self, _sAddress, _oIndex, _nValue, _aMsgs):
        _aMsgs.append(['%s/%s/%s' % (self.m_sBaseAddress, _sAddress, str(_oIndex)), [_nValue]])


    def append_mul_msg(self, _sAddress, _nIndex, _nValue, _aMsgs):
        _aMsgs.append(['%s/%s' % (self.m_sBaseAddress, _sAddress), [_nIndex, _nValue]])


    def append_edit_msg(self, _sId, _sAttrs, _aMsgs):
        _aMsgs.append(['/EDIT', [_sId, _sAttrs]])


    # Utility methods **********************************************************

    def log(self, _sMessage):
        nTime = time.time()
        sTime = datetime.datetime.fromtimestamp(nTime).strftime('%Y-%m-%d %H:%M:%S.%f')
        if (self.m_bLog):
            Live.Base.log("%s: %s" % (sTime, _sMessage))


    def alert(self, _sMessage):
        self.m_oCtrlInstance.show_message(_sMessage)


    def read_id3(self, _sFilePath):
        return ID3v2(_sFilePath)


    def to_ascii(self, _sText, _nTruncate = 0):
        sAscii = ''.join([(ord(cChar) > 127 and '' or cChar.encode('utf-8')) for cChar in _sText])
        if (_nTruncate == 0):
            return sAscii
        else:
            return sAscii[:_nTruncate]


    def to_color(self, _sRgb):
        if (_sRgb == 0):
            return 'var(--color-raised)'

        sB = _sRgb & 255
        sG = (_sRgb >> 8) & 255
        sR = (_sRgb >> 16) & 255

        return '#%02x%02x%02x' % (sR, sG, sB)


    def get_cwd(self):
        return os.getcwd()


    def get_root_path(self):
        sHome = os.getenv('HOME')
        sRoot = '%s/%s' % (sHome, self.m_sProductDir)
        return sRoot


    # ableton live utility methods *********************************************

    def song(self):
        return self.m_oCtrlInstance.song()


    def tempo(self, _nNewTempo = -1):
        if (_nNewTempo == -1):
            return self.song().tempo
        self.song().tempo = _nNewTempo


    def current_song_time_bar_beat(self):
        nTime = int(self.m_oCtrlInstance.song().current_song_time)
        return (nTime, nTime / 4 + 1, nTime % 4 + 1)


    # events methods ***********************************************************

    def on_tempo_changed(self, _nTempo):
        pass # this method should be override by subclasses


    # scheduler methods ********************************************************

    def update_prog_async_scheduled_tasks(self):
        pass # this method should be override by subclasses


    def update_async_scheduled_tasks(self):
        pass # this method should be override by subclasses


    def schedule_beat_tasks(self, _nCurrSongTime, _nCurrSongBar, _nCurrSongBeat):
        pass # this method should be override by subclasses


