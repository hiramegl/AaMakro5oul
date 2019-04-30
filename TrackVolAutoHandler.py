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
# Track Volume Autocontrol commands handler
# ******************************************************************************

class TrackVolAutoHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = False # do not ignore release toggle buttons
        bLogRxMsgs     = False # do not log (fader messages overflow the log!)
        self.config('/track/vol/auto', bIgnoreRelease, bLogRxMsgs)

        aRelIdxTracks = self.gui_visible_tracks_rel_range()
        self.m_aCmds = ['incr', 'decr', 'select']
        for sCmd in self.m_aCmds:
            self.add_callbacks_pref(sCmd, aRelIdxTracks)

        self.m_nDefaultBars = 24
        self.m_nDefaultVol  = 0.85 # 0 [dB]
        self.reset_tracks()
        self.update_tracks()


    def disconnect(self):
        self.reset_tracks()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'new_tracks_sel' or # SessionCmdHandler
            _sEvent == 'session_reset'):   # SessionCmdHandler
            self.update_tracks()

        elif (_sEvent == 'tracks_changed'):# TrackCmdHandler
            self.reset_tracks()

        elif (_sEvent == 'track_reboot'):  # TrackCmdHandler
            nTrackIdxAbs = _oArgs['nTrackIdxAbs']

            # stop auto update
            self.stop_auto(nTrackIdxAbs)


    def reset_tracks(self):
        # stop updating
        self.m_bAsyncAutoOn   = False
        self.m_bAsyncUpdating = False
        self.m_hAutoTracks    = {}

        # reset track configurations
        self.m_hTrackCfgs = {}
        for nTrackIdxAbs in self.tracks_and_returns_range():
            self.m_hTrackCfgs[nTrackIdxAbs] = self.m_nDefaultBars;

        # reset remote GUI controls
        aTrackMsgs = []

        aRelIdxTracks = self.gui_visible_tracks_rel_range()
        for sCmd in self.m_aCmds:
            for nTrackIdxRel in aRelIdxTracks:
                self.append_idx_msg(sCmd, nTrackIdxRel, 0.0, aTrackMsgs)

        sMsg = 'TrackVolAutoHandler, reset_tracks, track/vol/auto/*/*, reset'
        self.send_bundle(sMsg, aTrackMsgs)


    def update_tracks(self):
        aTrackMsgs = []

        for nTrackIdxRel in self.gui_visible_tracks_rel_range():
            nTrackIdxAbs = self.track_idx_abs(nTrackIdxRel)
            nDelayBars   = self.m_hTrackCfgs[nTrackIdxAbs]
            self.append_idx_msg('select', nTrackIdxRel, nDelayBars, aTrackMsgs)

            if (nTrackIdxAbs in self.m_hAutoTracks):
                # the track is auto-fading! turn on the correct auto-toggle!
                hAutoTrack = self.m_hAutoTracks[nTrackIdxAbs]
                sAutoType  = hAutoTrack['sAutoType']
                sOtherType = 'incr' if (sAutoType == 'decr') else 'decr'
                self.append_idx_msg(sAutoType , nTrackIdxRel, 1.0, aTrackMsgs)
                self.append_idx_msg(sOtherType, nTrackIdxRel, 0.0, aTrackMsgs)

            else:
                # turn off both toggles for this track
                self.append_idx_msg('incr', nTrackIdxRel, 0.0, aTrackMsgs)
                self.append_idx_msg('decr', nTrackIdxRel, 0.0, aTrackMsgs)

        sMsg = 'TrackVolAutoHandler, update_tracks, track/vol/auto/select/*, update'
        self.send_bundle(sMsg, aTrackMsgs)


    def stop_auto(self, _nTrackIdxAbs):
        self.m_bAsyncUpdating = True

        # the user is deactivating the automatic update!
        if (_nTrackIdxAbs in self.m_hAutoTracks):
            self.log('> stopping auto updating and removing from hash of async auto update volumes')
            hAutoTrack = self.m_hAutoTracks[_nTrackIdxAbs]
            self.send_msg('%s/%s' % (hAutoTrack['sAutoType'], _nTrackIdxAbs), 0.0)
            del self.m_hAutoTracks[_nTrackIdxAbs]
            self.log('> Auto update vol OFF, track: %d, type: %s' % (_nTrackIdxAbs, sCmd))
            self.alert('> Auto update vol OFF, track: %d, type: %s' % (_nTrackIdxAbs, sCmd))

        # check if is necessary to turn automatic control update off
        if (len(self.m_hAutoTracks) == 0):
            self.m_bAsyncAutoOn = False

        self.m_bAsyncUpdating = False


    def compute_params(self, _nTrackIdxAbs):
        # check that track is actually auto fading
        if (_nTrackIdxAbs in self.m_hAutoTracks):
            nDelayBars   = self.m_hTrackCfgs[_nTrackIdxAbs]

            nBeatsInABar = 4.0
            nTempo       = self.song().tempo
            nTimeStart   = time.time()
            nTimeDelta   = 60.0 / nTempo * nBeatsInABar * nDelayBars

            oTrack       = self.get_track_or_return(_nTrackIdxAbs)
            nValueStart  = oTrack.mixer_device.volume.value

            hAutoTrack   = self.m_hAutoTracks[_nTrackIdxAbs]
            nValueEnd    = self.m_nDefaultVol if (hAutoTrack['sAutoType'] == 'incr') else 0.0
            nValueDelta  = nValueEnd - nValueStart
            nSlope       = nValueDelta / nTimeDelta

            hAutoTrack['nTimeStart']  = nTimeStart
            hAutoTrack['nTimeEnd']    = nTimeStart + nTimeDelta
            hAutoTrack['nValueStart'] = nValueStart
            hAutoTrack['nValueEnd']   = nValueEnd
            hAutoTrack['nSlope']      = nSlope


    def handle(self, _aMessage):
        sCmd         = self.m_aParts[0]
        sTrackIdxRel = self.m_aParts[1]
        nTrackIdxAbs = self.track_idx_abs(int(sTrackIdxRel))

        self.m_bAsyncUpdating = True

        if (sCmd == 'select'):
            self.m_hTrackCfgs[nTrackIdxAbs] = _aMessage[2]
            self.compute_params(nTrackIdxAbs)

        else:
            nGuiValue  = _aMessage[2]
            bActive    = (nGuiValue > 0.5) # is the toggle active?

            if (bActive == True):
                hAutoTrack = {'sAutoType': sCmd}
                if (sCmd == 'decr'):
                    hAutoTrack['nValueEnd'] = 0.0
                    self.send_msg('decr/%s' % (sTrackIdxRel), 1.0)
                    self.send_msg('incr/%s' % (sTrackIdxRel), 0.0)

                else:
                    hAutoTrack['nValueEnd'] = self.m_nDefaultVol
                    self.send_msg('decr/%s' % (sTrackIdxRel), 0.0)
                    self.send_msg('incr/%s' % (sTrackIdxRel), 1.0)

                self.m_hAutoTracks[nTrackIdxAbs] = hAutoTrack
                self.compute_params(nTrackIdxAbs)
                self.m_bAsyncAutoOn = True
                self.log('> Auto update vol ON, track: %d, type: %s' % (nTrackIdxAbs, sCmd))
                self.alert('> Auto update vol ON, track: %d, type: %s' % (nTrackIdxAbs, sCmd))

            else:
                # the user is deactivating the automatic update!
                if (nTrackIdxAbs in self.m_hAutoTracks):
                    self.log('> stopping auto updating and removing from hash of async auto update volumes')
                    hAutoTrack = self.m_hAutoTracks[nTrackIdxAbs]
                    self.send_msg('%s/%s' % (hAutoTrack['sAutoType'], nTrackIdxAbs), 0.0)
                    del self.m_hAutoTracks[nTrackIdxAbs]
                    self.log('> Auto update vol OFF, track: %d, type: %s' % (nTrackIdxAbs, sCmd))
                    self.alert('> Auto update vol OFF, track: %d, type: %s' % (nTrackIdxAbs, sCmd))

                else:
                    self.log('> track not found in hash! doing nothing!')

            # check if is necessary to turn automatic control update off
            if (len(self.m_hAutoTracks) == 0):
                self.m_bAsyncAutoOn = False

        self.m_bAsyncUpdating = False


    # this function is run approx every 100ms
    def update_async_scheduled_tasks(self):
        if (self.m_bAsyncAutoOn == False or self.m_bAsyncUpdating):
            return # nothing else to do here

        nTime = time.time()
        aTracksToDelete = []

        for nTrackIdxAbs in self.m_hAutoTracks.keys():
            hAutoTrack = self.m_hAutoTracks[nTrackIdxAbs]

            # check if the time has already reached end time
            if (nTime > hAutoTrack['nTimeEnd']):
                nNewValue = self.final_value_reached(nTrackIdxAbs, hAutoTrack, aTracksToDelete)

            else:
                # the time has not reached end time, compute the new volume value
                nNewValue = hAutoTrack['nValueStart'] + hAutoTrack['nSlope'] * (nTime - hAutoTrack['nTimeStart'])

            # check if the new param value has already reached end value
            if (hAutoTrack['nSlope'] < 0):
                # for negative slope check if the value is less than the final value
                if (nNewValue < hAutoTrack['nValueEnd']):
                    nNewValue = self.final_value_reached(nTrackIdxAbs, hAutoTrack, aTracksToDelete)
            else:
                # for positive slope check if the value is greater than the final value
                if (nNewValue > hAutoTrack['nValueEnd']):
                    nNewValue = self.final_value_reached(nTrackIdxAbs, hAutoTrack, aTracksToDelete)

            try:
                oTrack = self.get_track_or_return(nTrackIdxAbs)
                oTrack.mixer_device.volume.value = nNewValue

            except Exception as e:
                self.log("> Error: could not update track volume '%d' with value %f: %s" % (nTrackIdxAbs, nNewValue, str(e)))

        # remove the tracks from the hash after iterating
        for nTrackIdxAbs in aTracksToDelete:
            if (nTrackIdxAbs in self.m_hAutoTracks):
                del self.m_hAutoTracks[nTrackIdxAbs]

        # check if there is any track left to auto-update
        # if empty then turn auto update off
        if (len(self.m_hAutoTracks) == 0):
            self.m_bAsyncAutoOn = False


    def final_value_reached(self, _nTrackIdxAbs, _hAutoTrack, _aTracksToDelete):
        nTrackIdxRel = self.track_idx_rel(_nTrackIdxAbs)
        self.send_msg('decr/%d' % (nTrackIdxRel), 0.0)
        self.send_msg('incr/%d' % (nTrackIdxRel), 0.0)
        _aTracksToDelete.append(_nTrackIdxAbs)

        return _hAutoTrack['nValueEnd']


