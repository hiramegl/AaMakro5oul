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

from __future__ import with_statement

import os
import time
import Live
import RemixNet

# ******************************************************************************
# Main script module AaMakro5oul
# ******************************************************************************

class AaMakro5oul:
    __doc__ = 'Script for AaMakro5oul controller'

    def __init__(self, _oCtrlInstance):
        self.c_instance      = _oCtrlInstance
        self.m_oCtrlInstance = _oCtrlInstance

        self.load_config()

        self.m_oOscServer = RemixNet.OSCServer(self, self.m_sTxAddr, self.m_nTxPort, self.m_sRxAddr, self.m_nRxPort)

        # load modules
        self.log('> %s: resetting controller ...' % (self.m_sProductName))

        self.m_aModules = []

        # higher prio during iteration of sync events
        self.add_modules('TrackDev', ['BeatRepeat', 'Eq3', 'Filter', 'Rev', 'Echo', 'Chorus', 'Flanger', 'Phaser', 'Select'])

        # lower prio for iteration of sync events
        self.add_modules('Root'    , ['Cmd'])
        self.add_modules('Session' , ['Cmd', 'Zoom', 'Tempo'])
        self.add_modules('Track'   , ['Cmd', 'Clip', 'VolAuto', 'Vol', 'Keyboard', 'Transpose', 'Fx'])
        self.add_modules('Scene'   , ['Cmd'])
        self.add_modules('Clip'    , ['Cmd', 'Loop'])
        self.add_modules('Cross'   , ['Cmd'])
        self.add_modules('Seq'     , ['Cmd', 'Beat', 'BeatNote'])
        self.add_modules('Loop'    , ['Jump', 'Roll'])
        self.add_modules('Move'    , ['Pos'])
        self.add_modules('Pad'     , ['Mouse'])

        self.log('> %s: controller reset' % (self.m_sProductName))
        self.send(self.m_sDeviceAddr, 1.0)

        # add this instance as on observer of modules
        for oModule in self.m_aModules:
            oModule.add_observer(self)


    def load_config(self):
        self.m_sProductName = 'AaMakro5oul'
        self.m_sProductDir  = self.m_sProductName

        # default configuration ************************************************

        # communications
        self.m_sTxAddr = '127.0.0.1' # the OSC server is running in the same computer as Ableton Live
        self.m_nTxPort = 2721

        self.m_sRxAddr = '127.0.0.1' # Ableton Live will open a UDP port in the localhost address
        self.m_nRxPort = 2720

        # device
        self.m_sDeviceId   = 'session_controller_%s'  % (self.m_sProductName)
        self.m_sDeviceAddr = '/session/controller/%s' % (self.m_sProductName)

        # features
        self.m_bSendBeat = True # Set to False for easier debugging
        self.m_nMinTempo = 90
        self.m_nMaxTempo = 140

        self.m_hConfig   = {
            'sProductName': self.m_sProductName,
            'sProductDir' : self.m_sProductDir,
            'bLog'        : True, # Set to True for debugging
            'bLogRxMsgs'  : True, # Set to True for debugging
            'nMinTempo'   : 90,
            'nMaxTempo'   : 140
        }

        # try to open configuration file ***************************************

        self.log('> %s: loading config ...' % (self.m_sProductName))

        sHome     = os.getenv('HOME')
        sFileName = 'config.txt'
        sFilePath = '%s/%s/%s' % (sHome, self.m_sProductDir, sFileName)

        bFileExists = os.path.isfile(sFilePath)
        if (bFileExists == False):
            self.log('> config file "%s" not found!' % (sFilePath))
            return # config file does not exist, nothing else to do here!

        self.log('> reading: "%s"' % (sFilePath))
        # read presets file
        oFile = open(sFilePath, 'r')

        # parse config lines
        for sLine in oFile:
            sLine = sLine.strip()

            # ignore empty lines and comment lines
            if (len(sLine) == 0):
                continue
            if (sLine[0] == '#'):
                continue

            # the first token in the line is the name of the config feature
            aTokens = sLine.split('|')

            # do not parse lines with less than 2 tokens
            if (len(aTokens) < 2):
                continue

            sName   = aTokens[0].strip()
            sValue  = aTokens[1].strip()
            self.log('>   parsing: %16s | %s' % (sName, sValue))

            # parse the value of the config feature

            if (sName == 'tx_addr'):
                self.m_sTxAddr = sValue
            elif (sName == 'tx_port'):
                self.m_nTxPort = int(sValue)
            elif (sName == 'rx_addr'):
                self.m_sRxAddr = sValue
            elif (sName == 'rx_port'):
                self.m_nRxPort = int(sValue)

            elif (sName == 'log'):
                self.m_hConfig['bLog'] = (sValue == 'true')
            elif (sName == 'log_rx_msgs'):
                self.m_hConfig['bLogRxMsgs'] = (sValue == 'true')

            elif (sName == 'send_beat'):
                self.m_bSendBeat = (sValue == 'true')
            elif (sName == 'min_tempo'):
                self.m_hConfig['nMinTempo'] = int(sValue)
            elif (sName == 'max_tempo'):
                self.m_hConfig['nMaxTempo'] = int(sValue)

            else:
                self.log('!Error: could not parse config feature "%s"!' % (sName))

        self.log('> %s: config loaded' % (self.m_sProductName))


    def add_modules(self, _sPrefix, _aModules):
        for sModule in _aModules:
            exec 'import ' + _sPrefix + sModule + 'Handler'
            eval('self.m_aModules.append(' + _sPrefix + sModule + 'Handler.' + _sPrefix + sModule + 'Handler(self.m_oCtrlInstance, self.m_oOscServer, self.m_hConfig))')


    def log(self, _sMessage):
        Live.Base.log(_sMessage)


    def alert(self, sMessage):
        self.m_oCtrlInstance.show_message(sMessage)


    def send(self, _sAddress, _oMessage):
        self.m_oOscServer.sendOSC(_sAddress, _oMessage)


    def update(self, _sEvent, _oArgs = None):
        # forward the event to the modules
        for oModule in self.m_aModules:
            oModule.update(_sEvent, _oArgs)


# #####################################################################
# Standard Ableton Methods

    def disconnect(self):
        self.log('> %s: disconnecting ...' % (self.m_sProductName))

        for oModule in self.m_aModules:
            oModule.disconnect()

        self.send('/session/tempo', '0.0')
        self.send('/session/tempo/fader', '0.0')
        self.send('/EDIT', [self.m_sDeviceId, '{"label": "-"}'])
        self.send(self.m_sDeviceAddr, 0.0)

        self.log('> %s: disconnected' % (self.m_sProductName))


    def build_midi_map(self, midi_map_handle):
        return


    def refresh_state(self):
        self.log('> %s: Refreshing state' % (self.m_sProductName));
        try:
            self.m_oSong = self.m_oCtrlInstance.song()
            try:
                self.m_nCurrSongTime = 0
                self.m_oSong.add_current_song_time_listener(self.on_current_song_time_changed)
                self.m_oSong.add_tempo_listener(self.on_tempo_changed)
            except:
                self.log('Could not add current song listeners')

            self.on_current_song_time_changed()
            self.on_tempo_changed()

        except:
            self.log('Could not get song handle')

        self.send(self.m_sDeviceAddr, 1.0)


    def update_display(self):
        """
        This function is run every 100ms, so we use it to allow us to process incoming
        OSC commands as quickly as possible under the current listener scheme.
        """
        # forward the event to the modules
        for oModule in self.m_aModules:
            oModule.update_prog_async_scheduled_tasks()
            oModule.update_async_scheduled_tasks()

        if self.m_oOscServer:
            try:
                self.m_oOscServer.processIncomingUDP()
            except:
                pass


    def on_current_song_time_changed(self):
        nCurrSongTime = int(self.m_oSong.current_song_time)

        if (nCurrSongTime != self.m_nCurrSongTime):
            self.m_nCurrSongTime  = nCurrSongTime
            nCurrSongBar          = nCurrSongTime / 4 + 1
            nCurrSongBeat         = nCurrSongTime % 4 + 1

            # forward the event to the modules
            for oModule in self.m_aModules:
                oModule.schedule_beat_tasks(nCurrSongTime, nCurrSongBar, nCurrSongBeat)

            # update the beat meter in the remote GUI
            if (self.m_bSendBeat):
                self.send('/EDIT', [self.m_sDeviceId, '{"label": "%d.%d"}' % (nCurrSongBar, nCurrSongBeat)])
                self.send(self.m_sDeviceAddr, 1.0)


    def connect_script_instances(self, instanciated_scripts):
        """
        Called by the Application as soon as all scripts are initialized.
        You can connect yourself to other running scripts here, as we do it
        connect the extension modules
        """
        return


    def is_extension(self):
        return False


    def request_rebuild_midi_map(self):
        """
        To be called from any components, as soon as their internal state changed in a
        way, that we do need to remap the mappings that are processed directly by the
        Live engine.
        Dont assume that the request will immediately result in a call to
        your build_midi_map function. For performance reasons this is only
        called once per GUI frame.
        """
        return


    def on_tempo_changed(self):
        nTempo = self.m_oSong.tempo
        self.send('/session/tempo', '%.2f' % (nTempo))

        nMinTempo = self.m_hConfig['nMinTempo']
        nMaxTempo = self.m_hConfig['nMaxTempo']
        nTempoFader = (nTempo - nMinTempo) / (nMaxTempo - nMinTempo)
        self.send('/session/tempo/fader', nTempoFader)

        # forward the event to the modules
        for oModule in self.m_aModules:
            oModule.on_tempo_changed(nTempo)



    def send_midi(self, midi_event_bytes):
        """
        Use this function to send MIDI events through Live to the _real_ MIDI devices
        that this script is assigned to.
        """
        pass


    def receive_midi(self, midi_bytes):
        return


    def can_lock_to_devices(self):
        return False


    def suggest_input_port(self):
        return 'Midi %s: 1' % (self.m_sProductName)


    def suggest_output_port(self):
        return 'Midi %s: 3' % (self.m_sProductName)


    def suggest_map_mode(self, cc_no, channel):
        return Live.MidiMap.MapMode.absolute


