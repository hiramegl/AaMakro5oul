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
# Effects channel commands handler
# ******************************************************************************

class TrackFxHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        self.m_bIgnoreRelease = False # we need to listen to toggle off messages (release messages)
        self.m_bLogRxMsgs     = False

        self.config('/track/fx', self.m_bIgnoreRelease, self.m_bLogRxMsgs)
        self.add_callbacks(['select', 'mode', 'reset', 'solo'])

        self.reset_track_selection()


    def disconnect(self):
        self.reset_track_selection()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'new_tracks_sel'): # SessionCmdHandler
            self.update_toggles()


    def reset_track_selection(self):
        self.m_bReturnMode = False
        self.send_msg('mode', 0.0)
        sId    = 'track_fx_reset'
        sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
        self.send('/EDIT', [sId, sAttrs])
        self.send_msg('solo', 0.0) # turn solo off

        aTrackMsgs = []

        for nTrackIdxAbs in range(self.max_track_sels()):
            self.append_mul_msg('select', nTrackIdxAbs, 0.0, aTrackMsgs)

        sMsg = 'TrackFxHandler, reset_track_selection, track/fx/select, reset'
        self.send_bundle(sMsg, aTrackMsgs)


    def update_toggles(self):
        if (self.m_bReturnMode == True):
            return # nothing else to do here, we are in 'return' mode

        # we are in 'track' mode, we need to update the track toggles!
        aFxTrackSel = self.sel_track_fx()
        sTrackType  = aFxTrackSel[0]
        nIdxAbs     = aFxTrackSel[1]

        if (sTrackType == 'return'):
            return # nothing else to do here, the selected track is a return track

        aTrackMsgs = []

        bIsVisible = self.is_track_visible(nIdxAbs)
        nIdxRel    = self.track_idx_rel(nIdxAbs)

        for nTrackIdxRel in range(self.max_track_sels()):
            nValue = 1.0 if (nTrackIdxRel == nIdxRel and bIsVisible) else 0.0
            self.append_mul_msg('select', nTrackIdxRel, nValue, aTrackMsgs)

        sMsg = 'TrackFxHandler, update_toggles, track indeces changed, updating'
        self.send_bundle(sMsg, aTrackMsgs)


    def handle(self, _aMessage):
        sCmd = self.m_aParts[0] # 'select', 'mode', 'reset' or 'solo'

        # handle 'mode' subcommand
        if (sCmd == 'mode'):
            bReturnMode = (_aMessage[2] > 0)
            self.m_bReturnMode = bReturnMode
            if (bReturnMode == True):
                self.alert('> Fx-track selection mode: Return')
            else:
                self.alert('> Fx-track selection mode: Track')

            # update the track toggle taking into consideration the new mode
            aFxTrackSel = self.sel_track_fx()
            sTrackType  = aFxTrackSel[0]
            nIdxAbs     = aFxTrackSel[1]

            # check if there is actually a track assigned to this fx channel
            if (sTrackType == 'track'):
                bIsVisible = self.is_track_visible(nIdxAbs)
                nIdxRel    = self.track_idx_rel(nIdxAbs)
                nValue     = 1.0 if (self.m_bReturnMode == False and bIsVisible) else 0.0
                self.send_msg('select', [nIdxRel, nValue])

            elif (sTrackType == 'return'):
                nValue  = 1.0 if (self.m_bReturnMode == True) else 0.0
                self.send_msg('select', [nIdxAbs, nValue])

            return # nothing else to do here!

        # handle 'reset' subcommand
        if (sCmd == 'reset'):
            self.update_observers('device_values_reset_fx')
            return # nothing else to do here!

        # handle 'solo' subcommand
        if (sCmd == 'solo'):
            aFxTrackSel = self.sel_track_fx()
            sTrackType  = aFxTrackSel[0]
            nIdxAbs     = aFxTrackSel[1]

            # check if there is actually a track assigned to that channel
            if (sTrackType != 'none'):
                if (sTrackType == 'track'):
                    oTrack = self.get_track(nIdxAbs)
                else:
                    oTrack = self.get_return(nIdxAbs)
                oTrack.solo = _aMessage[2] > 0.5
                self.send_msg('solo', _aMessage[2])

            else:
                self.send_msg('solo', 0.0) # turn toggle off immediately!

            return # nothing else to do here!

        # handle 'select' subcommand
        sTrackIdx = _aMessage[2] # track index relative or return index absolute
        nValue    = _aMessage[3] # toggle value

        nTrackIdx = int(sTrackIdx)
        bActive   = (nValue > 0.5) # is toggle active

        # validate index
        if (self.m_bReturnMode == False):
            # 'track' selection mode
            sTrackType = 'track'
            nIdxAbs    =  self.track_idx_abs(nTrackIdx)
            if (self.is_track_available(nIdxAbs) == False):
                self.send_msg('select', [nTrackIdx, 0.0]) # turn off the toggle button!
                return; # track does not exist, nothing else to do here
        else:
            # 'return' selection mode
            sTrackType = 'return'
            nIdxAbs    = nTrackIdx
            if (self.is_return_available(nIdxAbs) == False):
                self.send_msg('select', [nTrackIdx, 0.0]) # turn off the toggle button!
                return; # return-track does not exist, nothing else to do here

        aFxTrackSelOld = self.sel_track_fx()
        sTrackTypeOld  = aFxTrackSelOld[0]
        nIdxAbsOld     = aFxTrackSelOld[1]

        if (bActive == True):
            # check if there is any track already selected in this fx channel
            # and in case there is clear their values
            if (sTrackTypeOld != 'none'):
                # TrackDev[*]Handler: all devices in order to send their clear values in the GUI
                self.update_observers('device_values_clear_fx')

                if (sTrackTypeOld == 'track' and self.is_track_visible(nIdxAbsOld)):
                    nIdxRelOld = self.track_idx_rel(nIdxAbsOld)
                    self.send_msg('select', [nIdxRelOld, 0.0])
                else:
                    # is a return track (always gui visible)
                    self.send_msg('select', [nIdxAbsOld, 0.0])

                # unregister it from this channel (delete it)
                self.sel_track_fx('none')

                sId    = 'track_fx_reset'
                sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
                self.send('/EDIT', [sId, sAttrs])
                self.send_msg('solo', 0.0) # turn solo off

            # register in this channel and toggle on
            self.sel_track_fx(sTrackType, nIdxAbs)
            self.send_msg('select', [nTrackIdx, 1.0])

            if (sTrackType == 'track'):
                oTrack = self.get_track(nIdxAbs)
                sType  = 'T'
            else:
                oTrack = self.get_return(nIdxAbs)
                sType  = 'R'

            sName  = self.to_ascii(oTrack.name)
            sId    = 'track_fx_reset'
            sAttrs = '{"label": "%s%d: %s", "css": "background-color: %s"}' % (sType, nIdxAbs, sName, self.to_color(oTrack.color))
            self.send('/EDIT', [sId, sAttrs])

            # TrackDev[*]Handler: all devices in order to send their values to the GUI
            hArgs = {
                'sTrackType': sTrackType,
                'nIdxAbs'   : nIdxAbs
            }
            self.update_observers('device_values_update_fx', hArgs)
            self.log('> channel: x, type: %s, track sel: %d' % (sTrackType, nIdxAbs))
            self.alert('> channel: x, type: %s, track sel: %d' % (sTrackType, nIdxAbs))

        else:
            # TrackDev[*]Handler: all devices in order to send their clear values in the GUI
            self.update_observers('device_values_clear_fx')

            if (sTrackTypeOld == 'track' and self.is_track_visible(nIdxAbsOld)):
                # is a track, we are in track mode and is gui visible
                nIdxRelOld = self.track_idx_rel(nIdxAbsOld)
                self.send_msg('select', [nIdxRelOld, 0.0])
            else:
                # is a return track and we are in return mode (always gui visible)
                self.send_msg('select', [nIdxAbsOld, 0.0])

            # unregister it from this channel (delete it)
            self.sel_track_fx('none')

            sId    = 'track_fx_reset'
            sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
            self.send('/EDIT', [sId, sAttrs])
            self.send_msg('solo', 0.0) # turn solo off

            self.log('> channel: x -> cleared')
            self.alert('> channel: x -> cleared')


