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

import copy
from CoreHandler import CoreHandler

# ******************************************************************************
# Track selection used to handle device controller events
# ******************************************************************************

class TrackDevSelectHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        self.m_bIgnoreRelease = False # we need to listen to toggle off messages (release messages)
        self.m_bLogRxMsgs     = False
        self.config('/track/dev/select', self.m_bIgnoreRelease, self.m_bLogRxMsgs)

        for sCmd in ['track','reset','solo','volume']:
            self.add_callbacks_pref(sCmd, CoreHandler.m_aChannels)
        self.add_callbacks(['mode'])

        self.reset_track_selection()

        self.m_bReturnMode = False
        bActive = 1.0 if self.m_bReturnMode else 0.0
        self.send_msg('mode', bActive)


    def disconnect(self):
        self.reset_track_selection()

        self.m_bReturnMode = False
        bActive = 1.0 if self.m_bReturnMode else 0.0
        self.send_msg('mode', bActive)


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'track_reboot'): # TrackCmdHandler
            nTrackIdxAbs = _oArgs['nTrackIdxAbs']
            self.reset_channels_for_track(nTrackIdxAbs)

        elif (_sEvent == 'track_solo_update'): # TrackCmdHandler
            nTrackIdxAbs = _oArgs['nTrackIdxAbs']
            bSolo        = _oArgs['bSolo']

            sChannel = self.search_channel_for_track('track', nTrackIdxAbs)
            if (sChannel != None):
                nValue = 1.0 if (bSolo == True) else 0.0
                self.send_msg('solo/%s' % (sChannel), nValue) # update solo toggle for channel

        elif (_sEvent == 'new_tracks_sel'): # SessionCmdHandler
            self.update_toggles()


    def update_toggles(self):
        if (self.m_bReturnMode == True):
            return # nothing else to do here, we are in 'return' mode

        aTrackMsgs = []

        # we are in 'track' mode, we need to update the track toggles!
        for sChannel in CoreHandler.m_aChannels:
            aDevTrackSel = self.sel_track_dev(sChannel)
            sTrackType   = aDevTrackSel[0]
            nIdxAbs      = aDevTrackSel[1]

            if (sTrackType == 'return'):
                next # nothing else to do here, the selected track is a return track

            bIsVisible = self.is_track_visible(nIdxAbs)
            nIdxRel    = self.track_idx_rel(nIdxAbs)

            for nTrackIdxRel in range(self.max_track_sels()):
                nValue = 1.0 if (nTrackIdxRel == nIdxRel and bIsVisible) else 0.0
                self.append_mul_msg('track/%s' % (sChannel), nTrackIdxRel, nValue, aTrackMsgs)

        sMsg = 'TrackDevSelectHandler, update_toggles, track indeces changed, updating'
        self.send_bundle(sMsg, aTrackMsgs)


    def reset_channels_for_track(self, _nTrackIdxAbs):
        # reset the devices in the _TRACK_ itself (if a channel is found)
        sChannel = self.search_channel_for_track('track', _nTrackIdxAbs)
        if (sChannel != None):
            hArgs = { 'sChannel': sChannel }
        else:
            hArgs = { 'sTrackType': 'track', 'nIdxAbs': _nTrackIdxAbs }

        # TrackDevBaseHandler: device values reset
        self.update_observers('device_values_reset', hArgs)

        # reset the devices in the track's used _RETURNS_ (if any channel is found)
        oTrack = self.get_track(_nTrackIdxAbs)
        aSends = oTrack.mixer_device.sends

        # iterate through the list of sends for this track
        # and find out which channel needs to be reseted
        nReturnIdxAbs = 0
        for oSend in aSends:
            if (oSend.value > 0.1):
                sChannel = self.search_channel_for_track('return', nReturnIdxAbs)
                if (sChannel != None):
                    hArgs = { 'sChannel': sChannel }
                else:
                    hArgs = { 'sTrackType': 'return', 'nIdxAbs': nReturnIdxAbs }
                # TrackDev[*]Handler: device values reset
                self.update_observers('device_values_reset', hArgs)
            nReturnIdxAbs += 1


    def search_channel_for_track(self, _sType, _nTrackIdxAbs):
        for sChannel in CoreHandler.m_hDevTrackSel.keys():
            aDevTrackSel = CoreHandler.m_hDevTrackSel[sChannel]

            # check if the type and the index match
            if (aDevTrackSel[0] == _sType and aDevTrackSel[1] == _nTrackIdxAbs):
                return sChannel # channel found!

        return None # channel not found!


    def reset_track_selection(self):
        aTrackMsgs = []

        for sChannel in CoreHandler.m_aChannels:
            for nTrackIdxRel in range(self.max_track_sels()):
                self.append_mul_msg('track/%s' % (sChannel), nTrackIdxRel, 0.0, aTrackMsgs)
            sId    = 'track_dev_select_reset_%s' % (sChannel)
            sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
            self.send('/EDIT', [sId, sAttrs])
            self.send_msg('solo/%s' % (sChannel), 0.0) # turn solo off

        sMsg = 'TrackDevSelectHandler, reset_track_selection, track/dev/select, reset'
        self.send_bundle(sMsg, aTrackMsgs)


    def handle(self, _aMessage):
        sCmd = self.m_aParts[0] # 'track', 'mode' or 'reset'

        # handle 'mode' subcommand
        if (sCmd == 'mode'):
            bReturnMode = _aMessage[2] > 0
            self.m_bReturnMode = bReturnMode
            if (bReturnMode == True):
                self.alert('> Device-track selection mode: Return')
            else:
                self.alert('> Device-track selection mode: Track')

            # update the track toggle taking into consideration the new mode
            for sChannel in CoreHandler.m_aChannels:
                aDevTrackSel = self.sel_track_dev(sChannel)
                sTrackType   = aDevTrackSel[0]
                nIdxAbs      = aDevTrackSel[1]

                # check if there is actually a track assigned to this channel
                if (sTrackType == 'track'):
                    bIsVisible = self.is_track_visible(nIdxAbs)
                    nIdxRel    = self.track_idx_rel(nIdxAbs)
                    nValue  = 1.0 if (self.m_bReturnMode == False and bIsVisible) else 0.0
                    self.send_msg('track/%s' % (sChannel), [nIdxRel, nValue])

                elif (sTrackType == 'return'):
                    nValue  = 1.0 if (self.m_bReturnMode == True) else 0.0
                    self.send_msg('track/%s' % (sChannel), [nIdxAbs, nValue])

            return # nothing else to do here!

        sChannel = self.m_aParts[1] # 'a', 'b', 'c' or 'd'

        # handle 'reset' subcommand
        if (sCmd == 'reset'):
            hArgs = { 'sChannel': sChannel }
            self.update_observers('device_values_reset', hArgs)
            return # nothing else to do here!

        # handle 'solo' subcommand
        if (sCmd == 'solo'):
            aDevTrackSel = self.sel_track_dev(sChannel)
            sTrackType   = aDevTrackSel[0]
            nIdxAbs      = aDevTrackSel[1]

            # check if there is actually a track assigned to that channel
            if (sTrackType != 'none'):
                if (sTrackType == 'track'):
                    oTrack = self.get_track(nIdxAbs)
                else:
                    oTrack = self.get_return(nIdxAbs)
                oTrack.solo = _aMessage[2] > 0.5
                self.send_msg('solo/%s' % (sChannel), _aMessage[2])

            else:
                self.send_msg('solo/%s' % (sChannel), 0.0) # turn toggle off immediately!

            return # nothing else to do here!

        if (sCmd == 'volume'):
            aDevTrackSel = self.sel_track_dev(sChannel)
            sTrackType   = aDevTrackSel[0]
            nIdxAbs      = aDevTrackSel[1]

            # check if there is actually a track assigned to that channel
            if (sTrackType != 'none'):
                if (sTrackType == 'track'):
                    oTrack = self.get_track(nIdxAbs)
                else:
                    oTrack = self.get_return(nIdxAbs)
                oMixDev              = oTrack.mixer_device
                oMixDev.volume.value = _aMessage[2]
                #self.send_msg('volume/%s' % (sChannel), _aMessage[2])

            else:
                self.send_msg('volume/%s' % (sChannel), 0.0) # turn volume off immediately!

            return # nothing else to do here!


        # handle 'track' subcommand
        sTrackIdx = _aMessage[2]     # track index relative or return index absolute
        nValue    = _aMessage[3]     # toggle value

        nTrackIdx = int(sTrackIdx)
        bActive   = (nValue > 0.5)   # is toggle active
        aOthers   = copy.copy(CoreHandler.m_aChannels)
        aOthers.remove(sChannel)     # the other channels

        # validate index
        if (self.m_bReturnMode == False):
            # 'track' selection mode
            sTrackType = 'track'
            nIdxAbs    = self.track_idx_abs(nTrackIdx)
            if (self.is_track_available(nIdxAbs) == False):
                self.send_msg('track/%s' % (sChannel), [nTrackIdx, 0.0]) # turn off the toggle button!
                return; # track does not exist, nothing else to do here
        else:
            # 'return' selection mode
            sTrackType = 'return'
            nIdxAbs    = nTrackIdx
            if (self.is_return_available(nIdxAbs) == False):
                self.send_msg('track/%s' % (sChannel), [nTrackIdx, 0.0]) # turn off the toggle button!
                return; # return-track does not exist, nothing else to do here

        aDevTrackSelOld = self.sel_track_dev(sChannel)
        sTrackTypeOld   = aDevTrackSelOld[0]
        nIdxAbsOld      = aDevTrackSelOld[1]

        if (bActive == True):
            # check if the track is already selected in other channel
            for sOtherChannel in aOthers:
                aDevTrackSelOther = self.sel_track_dev(sOtherChannel)
                sTrackTypeOther = aDevTrackSelOther[0]
                nIdxAbsOther    = aDevTrackSelOther[1]
                if (sTrackTypeOther == sTrackTypeOld and nIdxAbsOther == nIdxAbsOld):
                    # TrackDev[*]Handler: all devices in order to send their clear values in the GUI
                    hArgs = { 'sChannel': sOtherChannel }
                    self.update_observers('device_values_clear', hArgs)

                    # unregister it from the other channel (delete it)
                    self.sel_track_dev(sOtherChannel, 'none')
                    self.send_msg('track/%s' % (sOtherChannel), [nTrackIdx, 0.0])
                    sId    = 'track_dev_select_reset_%s' % (sOtherChannel)
                    sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
                    self.send('/EDIT', [sId, sAttrs])

            # check if there is any track already selected in this channel,
            # if there is any then remove it first from this channel

            if (sTrackTypeOld != 'none'):
                # TrackDev[*]Handler: all devices in order to send their clear values in the GUI
                hArgs = { 'sChannel': sChannel }
                self.update_observers('device_values_clear', hArgs)

                if (sTrackTypeOld == 'track' and self.is_track_visible(nIdxAbsOld)):
                    # is a track and is gui visible
                    nIdxRelOld = self.track_idx_rel(nIdxAbsOld)
                    self.send_msg('track/%s' % (sChannel), [nIdxRelOld, 0.0])
                else:
                    # is a return track
                    self.send_msg('track/%s' % (sChannel), [nIdxAbsOld, 0.0])

                # unregister it from this channel (delete it)
                self.sel_track_dev(sChannel, 'none')

                sId    = 'track_dev_select_reset_%s' % (sChannel)
                sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
                self.send('/EDIT', [sId, sAttrs])
                self.send_msg('solo/%s' % (sChannel), 0.0) # turn solo off

            # register in this channel and toggle on
            self.sel_track_dev(sChannel, sTrackType, nIdxAbs)
            self.send_msg('track/%s' % (sChannel), [nTrackIdx, 1.0])

            if (sTrackType == 'track'):
                oTrack = self.get_track(nIdxAbs)
                sType  = 'T'
            else:
                oTrack = self.get_return(nIdxAbs)
                sType  = 'R'
            sName  = self.to_ascii(oTrack.name)
            sId    = 'track_dev_select_reset_%s' % (sChannel)
            sAttrs = '{"label": "%s%d: %s", "css": "background-color: %s"}' % (sType, nIdxAbs, sName, self.to_color(oTrack.color))
            self.send('/EDIT', [sId, sAttrs])


            # update solo state and volume for selected track
            nSolo = 1.0 if (oTrack.solo) else 0.0
            self.send_msg('solo/%s' % (sChannel), nSolo)
            self.send_msg('volume/%s' % (sChannel), oTrack.mixer_device.volume.value)

            # TrackDev[*]Handler: all devices in order to send their values to the GUI
            hArgs = {
                'sChannel'  : sChannel,
                'sTrackType': sTrackType,
                'nIdxAbs'   : nIdxAbs
            }
            self.update_observers('device_values_update', hArgs)
            self.log('> channel: %s, type: %s, track sel: %d' % (sChannel, sTrackType, nIdxAbs))
            self.alert('> channel: %s, type: %s, track sel: %d' % (sChannel, sTrackType, nIdxAbs))

        else:
            # TrackDev[*]Handler: all devices in order to send their clear values in the GUI
            hArgs = { 'sChannel': sChannel }
            self.update_observers('device_values_clear', hArgs)

            if (sTrackTypeOld == 'track' and self.is_track_visible(nIdxAbsOld)):
                # is a track and is gui visible
                nIdxRelOld = self.track_idx_rel(nIdxAbsOld)
                self.send_msg('track/%s' % (sChannel), [nIdxRelOld, 0.0])
            else:
                # is a return track (always gui visible)
                self.send_msg('track/%s' % (sChannel), [nIdxAbsOld, 0.0])

            # unregister in this channel and toggle off
            self.sel_track_dev(sChannel, 'none')

            sId    = 'track_dev_select_reset_%s' % (sChannel)
            sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
            self.send('/EDIT', [sId, sAttrs])
            self.send_msg('solo/%s' % (sChannel), 0.0) # turn solo off

            self.log('> channel: %s -> cleared' % (sChannel))
            self.alert('> channel: %s -> cleared' % (sChannel))


