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

from CoreHandler import CoreHandler

# ******************************************************************************
# Track Volume commands handler
# ******************************************************************************

class TrackVolHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = False # the index of sends can be 0 (may appear as a release)
        bLogInfo       = False # do not log (fader messages overflow the log!)
        self.config('/track/vol', bIgnoreRelease, bLogInfo)

        # these commands apply to all gui visible tracks, the master track,
        # the cue volume and to the selected track
        self.m_aCmds = [
            'fader',  # volume fader
            'reset',  # volume reset:  85 %
            'min',    # volume min  :   0 %
            'max',    # volume max  : 100 %
        ]
        aTracks = self.track_indeces_list()
        for sCmd in self.m_aCmds:
            self.add_callbacks_pref(sCmd, aTracks + ['cue'])

        # NOTE: use 'aTracks' variable when we actually have separated
        #       controls for every track sends, currently we have not :-(

        # sends volumes apply only to the selected track,
        # master track and audio tracks are not handled
        self.add_callbacks_pref('sends', ['selected']) # use aTracks when GUI implemented

        # returns are managed with a multifader
        self.add_callback_cmd('returns')

        self.m_hTrackListeners = {}

        self.reset_tracks()
        self.update_tracks()
        self.update_selected_track()
        self.add_listeners()


    def disconnect(self):
        self.remove_listeners()
        self.reset_tracks()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'new_tracks_sel' or # SessionCmdHandler
            _sEvent == 'session_reset'):   # SessionCmdHandler
            self.update_tracks()

        elif (_sEvent == 'tracks_changed'):# TrackCmdHandler
            self.add_listeners()
            self.update_tracks()
            self.update_selected_track()

        elif (_sEvent == 'new_track_sel'): # TrackCmdHandler
            self.update_selected_track()


    def reset_tracks(self):
        aTrackMsgs = []

        aTracks = self.track_indeces_list() + ['cue']
        for nTrackIdxRel in aTracks:
            self.append_idx_msg('fader', nTrackIdxRel, 0.0, aTrackMsgs)

        # reset the values of the selected-track sends
        for nSendIdxAbs in self.gui_vis_sends_range():
            self.append_mul_msg('sends/selected', nSendIdxAbs, 0.0, aTrackMsgs)

        for nReturnIdxAbs in self.gui_vis_returns_range():
            self.append_mul_msg('returns', nReturnIdxAbs, 0.0, aTrackMsgs)

        sMsg = 'TrackVolHandler, reset_tracks, track/vol/fader, reset'
        self.send_bundle(sMsg, aTrackMsgs)


    def update_tracks(self):
        aTrackMsgs = []

        # iterate through the visible tracks in the GUI by using the
        # absolute indeces of the tracks and send the volumes and
        # sends values for the selected track
        for nTrackIdxAbs in self.gui_visible_tracks_abs_range():
            nTrackIdxRel = self.track_idx_rel(nTrackIdxAbs)
            nVolume      = 0.0

            # check if the track is actually available
            if (self.is_track_available(nTrackIdxAbs)):
                oTrack = self.get_track(nTrackIdxAbs)
                oMixDev = oTrack.mixer_device
                nVolume = oMixDev.volume.value
                aSends  = oMixDev.sends

                # NOTE: Do this when we actually have a GUI for the sends
                #       of every track
                # for nSendIdxAbs in range(len(aSends)):
                #     nSendValue = aSends[nSendIdxAbs]
                #     self.append_mul_msg('sends/%d' % (nTrackIdxRel), nSendIdxAbs, nSendValue, aTrackMsgs)

                if (self.sel_track_idx_abs() == nTrackIdxAbs):
                    for nSendIdxAbs in range(len(aSends)):
                        nSendValue = aSends[nSendIdxAbs].value
                        self.append_mul_msg('sends/selected', nSendIdxAbs, nSendValue, aTrackMsgs)

            else: # track is unavailable, reset sends values in case is selected track

                if (self.sel_track_idx_abs() == nTrackIdxAbs):
                    for nSendIdxAbs in range(len(aSends)):
                        nSendValue = aSends[nSendIdxAbs].value
                        self.append_mul_msg('sends/selected', nSendIdxAbs, 0.0, aTrackMsgs)

            self.append_idx_msg('fader', nTrackIdxRel, nVolume, aTrackMsgs)

        # master track and cue volumes
        oMixDev = self.master().mixer_device
        self.append_idx_msg('fader', 'master', oMixDev.volume.value    , aTrackMsgs)
        self.append_idx_msg('fader', 'cue'   , oMixDev.cue_volume.value, aTrackMsgs)

        # returns volumes
        for nReturnIdxAbs in self.gui_vis_returns_range():
            nVolume = 0.0
            if (self.is_return_available(nReturnIdxAbs)):
                oReturn = self.get_return(nReturnIdxAbs)
                nVolume = oReturn.mixer_device.volume.value
            self.append_mul_msg('returns', nReturnIdxAbs, nVolume, aTrackMsgs)

        sMsg = 'TrackVolHandler, update_tracks, track/vol/fader, update'
        self.send_bundle(sMsg, aTrackMsgs)


    def update_selected_track(self):
        aTrackMsgs = []

        oTrack  = self.sel_track()
        oMixDev = oTrack.mixer_device
        self.append_idx_msg('fader', 'selected', oMixDev.volume.value, aTrackMsgs)

        # update sends volumes if is not a return-track
        if (self.is_return_track(oTrack) == False):
            aSends = oMixDev.sends
            for nSendIdxAbs in range(len(aSends)):
                nSendValue = aSends[nSendIdxAbs].value
                self.append_mul_msg('sends/selected', nSendIdxAbs, nSendValue, aTrackMsgs)

        sMsg = 'TrackVolHandler, update_selected_track, track/vol/fader/selected, update'
        self.send_bundle(sMsg, aTrackMsgs)


    def handle(self, _aMessage):
        # first of all handle returns volumes
        if (self.m_sCmd == 'returns'):
            nReturnIdxAbs = int(_aMessage[2])
            nReturnValue  = _aMessage[3]

            # check if the return-track is actually available
            if (self.is_return_available(nReturnIdxAbs) == False):
                self.send_msg('returns', [nReturnIdxAbs, 0.0])
                return # return-track not available, nothing else to do here!

            oReturn = self.get_return(nReturnIdxAbs)
            oReturn.mixer_device.volume.value = nReturnValue
            return # done changing the return-track volume, nothing else to do here!

        sCmd         = self.m_aParts[0] # fader, reset, min, max, sends, returns
        sTrackIdxRel = self.m_aParts[1]

        # find out which track is operated (master, selected, 0-7)
        if (sTrackIdxRel == 'master'):
            oTrack = self.master()

        elif (sTrackIdxRel == 'selected'):
            oTrack = self.sel_track()

        elif (sTrackIdxRel == 'cue'):
            oTrack = self.master()

        else:
            nTrackIdxAbs = self.track_idx_abs(int(sTrackIdxRel))
            if (self.is_track_available(nTrackIdxAbs) == False):
                return # unavailable track, nothing else to do here!
            oTrack = self.get_track(nTrackIdxAbs)

        oMixDev = oTrack.mixer_device
        nVolume = -1.0

        if (sCmd == 'fader'):
            nVolume = _aMessage[2]

        elif (sCmd == 'reset'):
            nVolume = 0.85

        elif (sCmd == 'max'):
            nVolume = 1.0

        elif (sCmd == 'min'):
            nVolume = 0.0

        if (sCmd == 'sends'):
            nSendIdxAbs = int(_aMessage[2])
            nSendValue  = _aMessage[3]

            # return-tracks have no sends!
            if (self.is_return_track(oTrack)):
                self.send_msg('sends/selected', [nSendIdxAbs, 0.0])
                return # is a return-track, nothing else to do here!

            # check that the send is actually available for this track!
            aSends = oTrack.mixer_device.sends
            if (nSendIdxAbs < len(aSends)):
                aSends[nSendIdxAbs].value = nSendValue
            else:
                self.send_msg('sends/selected', [nSendIdxAbs, 0.0])
            return # nothing else to do here

        if (sTrackIdxRel == 'cue'):
            oMixDev.cue_volume.value = nVolume
        else:
            oMixDev.volume.value = nVolume


    # Ableton Live events management *******************************************

    def add_listeners(self):
        self.remove_listeners()

        oMasterMixDev = self.master().mixer_device
        if (not oMasterMixDev.volume.value_has_listener(self.on_master_changed)):
            oMasterMixDev.volume.add_value_listener(self.on_master_changed)
        if (not oMasterMixDev.cue_volume.value_has_listener(self.on_cue_changed)):
            oMasterMixDev.cue_volume.add_value_listener(self.on_cue_changed)

        for nTrackIdxAbs in self.tracks_and_returns_range():
            oTrack = self.get_track_or_return(nTrackIdxAbs)
            self.add_track_listeners(nTrackIdxAbs, oTrack)


    def on_master_changed(self):
        nVolume = self.master().mixer_device.volume.value
        self.send_msg('fader/master', nVolume)


    def on_cue_changed(self):
        nVolume = self.master().mixer_device.cue_volume.value
        self.send_msg('fader/cue', nVolume)


    def add_track_listeners(self, _nTrackIdxAbs, _oTrack):
        fVolCallback  = lambda :self.on_track_vol_changed(_nTrackIdxAbs, _oTrack)
        fSendCallback = lambda :self.on_track_send_changed(_nTrackIdxAbs, _oTrack)

        if (not _oTrack in self.m_hTrackListeners):
            oMixDev = _oTrack.mixer_device
            oMixDev.volume.add_value_listener(fVolCallback)
            self.m_hTrackListeners[_oTrack] = [fVolCallback]

            if (self.is_return_track(_oTrack)):
                return # return-track, nothing else to do

            # normal track: add listeners to sends
            aSends = oMixDev.sends
            for nSendIdxAbs in range(len(aSends)):
                if (not aSends[nSendIdxAbs].value_has_listener(fSendCallback)):
                    aSends[nSendIdxAbs].add_value_listener(fSendCallback)

            self.m_hTrackListeners[_oTrack].append(fSendCallback)


    def on_track_vol_changed(self, _nTrackIdxAbs, _oTrack):
        if (self.is_return_track(_oTrack)):
            nReturnIdxAbs = _nTrackIdxAbs - len(self.tracks())
            nVolume       = _oTrack.mixer_device.volume.value
            self.send_msg('returns', [nReturnIdxAbs, nVolume])

        elif (self.is_track_visible(_nTrackIdxAbs)):
            nTrackIdxRel = self.track_idx_rel(_nTrackIdxAbs)
            nVolume      = _oTrack.mixer_device.volume.value
            self.send_msg('fader/%d' % (nTrackIdxRel), nVolume)

        if (self.sel_track_idx_abs() == _nTrackIdxAbs):
            self.send_msg('fader/selected', nVolume)


    def on_track_send_changed(self, _nTrackIdxAbs, _oTrack):
        oMixDev = _oTrack.mixer_device
        aSends  = oMixDev.sends

        aTrackMsgs = []

        # NOTE: Do this when we actually have a GUI for the sends
        #       of every track
        # if (self.is_track_visible(_nTrackIdxAbs)):
        #     nTrackIdxRel = self.track_idx_rel(_nTrackIdxAbs)
        #     for nSendIdxAbs in range(len(aSends)):
        #         nSendValue = aSends[nSendIdxAbs].value
        #         self.append_mul_msg('sends/%d' % (nTrackIdxRel), nSendIdxAbs, nSendValue, aTrackMsgs)

        if (self.sel_track_idx_abs() == _nTrackIdxAbs):
            for nSendIdxAbs in range(len(aSends)):
                nSendValue = aSends[nSendIdxAbs].value
                self.append_mul_msg('sends/selected', nSendIdxAbs, nSendValue, aTrackMsgs)

        sMsg = 'TrackVolHandler, on_track_send_changed, track/vol/send/*, updating_all_sends_values'
        self.send_bundle(sMsg, aTrackMsgs)


    def remove_listeners(self):
        oMasterMixDev = self.master().mixer_device
        if (oMasterMixDev.volume.value_has_listener(self.on_master_changed)):
            oMasterMixDev.volume.remove_value_listener(self.on_master_changed)
        if (oMasterMixDev.cue_volume.value_has_listener(self.on_cue_changed)):
            oMasterMixDev.cue_volume.remove_value_listener(self.on_cue_changed)

        try:
            for oTrack in self.m_hTrackListeners:
                if (not oTrack in self.m_hTrackListeners):
                    continue # the key exists but the hash cannot recover the value!!!

                if (oTrack != None):
                    aListeners    = self.m_hTrackListeners[oTrack]
                    fVolCallback  = aListeners[0]
                    fSendCallback = aListeners[1]

                    oMixDev       = oTrack.mixer_device
                    aSends        = oMixDev.sends

                    if (oMixDev.volume.value_has_listener(fVolCallback)):
                        oMixDev.volume.remove_value_listener(fVolCallback)

                    for nSendIdxAbs in range(len(aSends)):
                        if (aSends[nSendIdxAbs].value_has_listener(fSendCallback)):
                            aSends[nSendIdxAbs].remove_value_listener(fSendCallback)
        except IndexError as oError:
            self.log('! Error: %s' % (str(oError)))

        self.m_hTrackListeners = {}


