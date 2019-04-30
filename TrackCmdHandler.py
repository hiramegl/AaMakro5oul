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
# Track commands handler
# ******************************************************************************

class TrackCmdHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)
        self.m_aCmds = ['enable','solo','crossa','crossb','stop','arm','select','reboot','loop']

        bIgnoreRelease = False # we need to listen when the toggles get off (released)
        bLogRxMsgs     = False
        self.config('/track/cmd', bIgnoreRelease)

        for sCmd in self.m_aCmds:
            self.add_callbacks_pref(sCmd, self.track_indeces_list())
        self.add_callbacks(['lockreboot'])

        self.m_nDefaultVol     = 0.85 # 0 [dB]
        self.m_hTrackListeners = {}
        self.m_hFocusedClips   = {}

        # not necessary to reset tracks now, just update
        self.update_tracks()
        self.update_selected_track()
        self.add_listeners()

        self.m_bLockReboot = True
        self.send_msg('lockreboot', 1.0)


    def disconnect(self):
        self.remove_listeners()
        self.reset_tracks()


    def update(self, _sEvent, _hArgs = None):
        if (_sEvent == 'new_tracks_sel' or # SessionCmdHandler
            _sEvent == 'session_reset'):   # SessionCmdHandler
            # the session region has moved left or right or the
            # session has been reset, update the tracks!
            self.update_tracks()

        if (_sEvent == 'clip_state_updated'):
            nTrackIdxAbs = _hArgs['nTrackIdxAbs']
            nSceneIdxAbs = _hArgs['nSceneIdxAbs']
            self.handle_focused_clip(nTrackIdxAbs, nSceneIdxAbs)


    def handle_focused_clip(self, _nTrackIdxAbs, _nSceneIdxAbs):
        # the clip could have been activated but the track might not be visible
        # in the remote GUI, check that is visible
        if (self.is_track_visible(_nTrackIdxAbs) == False):
            return # track not visible, nothing else to do here!

        # track is visible, update the loop toggle of the track
        oTrack        = self.get_track(_nTrackIdxAbs)
        aAllClipSlots = oTrack.clip_slots
        oClipSlot     = aAllClipSlots[_nSceneIdxAbs]
        nTrackIdxRel  = self.track_idx_rel(_nTrackIdxAbs)


        if (oClipSlot.has_clip):
            oClip = oClipSlot.clip

            # update the looping status
            sLabelCss  = ".label {color:blue}"
            sToggleCss = ".toggle.on:after {left: 0; top: 0; right: 0; height: 40px !important; opacity: 0.5; background-color: red}"
            sAttrs     = '{"css": "%s %s"}' % (sLabelCss, sToggleCss)
            self.send('/EDIT', ['track_cmd_loop_%d' % (nTrackIdxRel), sAttrs])

            nLoop = 1.0 if (oClip.looping == True) else 0.0
            self.send_msg("loop/%d" % (nTrackIdxRel), nLoop)

            self.m_hFocusedClips[_nTrackIdxAbs] = _nSceneIdxAbs

        else:
            # change color of the looping toggle for this track (to unavailable)
            # since the clip is no longer available
            sCss   = ".label {color: darkgray}"
            sAttrs = '{"css": "%s"}' % (sCss)
            self.send('/EDIT', ['track_cmd_loop_%d' % (nTrackIdxRel), sAttrs])
            self.send_msg("loop/%d" % (nTrackIdxRel), 0.0)

            if (_nTrackIdxAbs in self.m_hFocusedClips):
                del self.m_hFocusedClips[_nTrackIdxAbs]


    def reset_tracks(self):
        self.m_bLockReboot = True
        self.send_msg('lockreboot', 1.0)

        self.m_hFocusedClips = {}

        aTrackMsgs = []

        # reset track labels in remote GUI (use relative indeces: 0, 1, 2, ...)
        for nTrackIdxRel in self.gui_visible_tracks_rel_range():
            # reset track selection labels
            sAttrs = '{"label": "-%d-", "css": "background-color: var(--color-raised)"}' % (nTrackIdxRel)
            self.append_edit_msg('track_cmd_select_%d'  % (nTrackIdxRel), sAttrs, aTrackMsgs)

            # reset track loop toggles
            sAttrs = '{"css": "color: darkgray"}'
            self.append_edit_msg('track_cmd_loop_%d'  % (nTrackIdxRel), sAttrs, aTrackMsgs)
            self.append_idx_msg('loop', nTrackIdxRel, 0.0, aTrackMsgs)

        # reset track buttons in remote GUI (even selected track,
        # use relative track indeces: 0, 1, 2, ...)
        for nTrackIdxRel in self.gui_visible_tracks_rel_range(['selected']):
            for sCmd in self.m_aCmds:
                self.append_idx_msg(sCmd, nTrackIdxRel, 0.0, aTrackMsgs)

        sMsg = 'TrackCmdHandler, reset_tracks, track/cmd, reset'
        self.send_bundle(sMsg, aTrackMsgs)


    def update_tracks(self):
        aTrackMsgs   = []

        # update all visible tracks in the remote GUI by using
        # the absolute track indices
        for nTrackIdxAbs in self.gui_visible_tracks_abs_range():
            sName   = '-%d-' % (nTrackIdxAbs)
            sColor  = 'background-color: var(--color-raised)'
            nEnable = 1.0
            nSolo   = 0.0
            nCrossA = 0.0
            nCrossB = 0.0
            nArm    = 0.0
            nLoop   = 0.0
            sLoopColor = 'darkgray'

            if (self.is_track_available(nTrackIdxAbs)):
                oTrack  = self.get_track(nTrackIdxAbs)
                oMixDev = oTrack.mixer_device
                sName   = self.to_ascii(oTrack.name, 20)
                sColor  = self.to_color(oTrack.color)

                if (oTrack.mute): nEnable = 0.0
                if (oTrack.solo): nSolo   = 1.0
                if (oMixDev.crossfade_assign == 0): nCrossA = 1.0
                if (oMixDev.crossfade_assign == 2): nCrossB = 1.0
                if (oTrack.arm): nArm     = 1.0
                if (nTrackIdxAbs in self.m_hFocusedClips):
                    # there is a focused clip for this track!
                    sLoopColor = 'blue'

                    # toggle loop on if clip is actually looping!
                    nSceneIdxAbs = self.m_hFocusedClips[nTrackIdxAbs]
                    aAllClipSlots = oTrack.clip_slots
                    oClipSlot     = aAllClipSlots[nSceneIdxAbs]
                    if (oClipSlot.has_clip == True):
                        oClip = oClipSlot.clip
                        if (oClip.looping == True):
                            nLoop = 1.0

            nTrackIdxRel = self.track_idx_rel(nTrackIdxAbs)

            # track label
            sAttrs = '{"label": "%s", "css": "background-color: %s"}' % (sName, sColor)
            self.append_edit_msg('track_cmd_select_%d'  % (nTrackIdxRel), sAttrs, aTrackMsgs)

            # track loop label
            sLabelCss  = ".label {color:%s}" % (sLoopColor)
            sToggleCss = ".toggle.on:after {left: 0; top: 0; right: 0; height: 40px !important; opacity: 0.5; background-color: red}"
            sAttrs     = '{"css": "%s %s"}' % (sLabelCss, sToggleCss)
            self.append_edit_msg('track_cmd_loop_%d'  % (nTrackIdxRel), sAttrs, aTrackMsgs)

            self.append_idx_msg('enable', nTrackIdxRel, nEnable, aTrackMsgs)
            self.append_idx_msg('solo'  , nTrackIdxRel, nSolo  , aTrackMsgs)
            self.append_idx_msg('crossa', nTrackIdxRel, nCrossA, aTrackMsgs)
            self.append_idx_msg('crossb', nTrackIdxRel, nCrossB, aTrackMsgs)
            self.append_idx_msg('arm'   , nTrackIdxRel, nArm   , aTrackMsgs)
            self.append_idx_msg('loop'  , nTrackIdxRel, nLoop  , aTrackMsgs)

        sMsg = 'TrackCmdHandler, update_tracks, track/cmd, update'
        self.send_bundle(sMsg, aTrackMsgs)


    def update_selected_track(self):
        oSelTrack = self.sel_track()

        if (self.is_return_track(oSelTrack)):
           return # is a return-track, nothing else to do here

        oMixDev = oSelTrack.mixer_device

        sName   = self.to_ascii(oSelTrack.name, 20)
        sColor  = self.to_color(oSelTrack.color)
        nEnable = 0.0 if (oSelTrack.mute) else 1.0
        nSolo   = 1.0 if (oSelTrack.solo) else 0.0
        nCrossA = 1.0 if (oMixDev.crossfade_assign == 0) else 0.0
        nCrossB = 1.0 if (oMixDev.crossfade_assign == 2) else 0.0
        try:
            nArm = 1.0 if (oSelTrack.arm) else 0.0
        except Exception as e:
            nArm = 0.0

        aTrackMsgs   = []

        sAttrs = '{"label": "%s", "css": "background-color: %s"}' % (sName, sColor)
        self.append_edit_msg('track_selected', sAttrs, aTrackMsgs)

        self.append_idx_msg('enable', 'selected', nEnable, aTrackMsgs)
        self.append_idx_msg('solo'  , 'selected', nSolo  , aTrackMsgs)
        self.append_idx_msg('crossa', 'selected', nCrossA, aTrackMsgs)
        self.append_idx_msg('crossb', 'selected', nCrossB, aTrackMsgs)
        self.append_idx_msg('arm'   , 'selected', nArm   , aTrackMsgs)

        sMsg = 'TrackCmdHandler, update_selected_track, track/cmd, update'
        self.send_bundle(sMsg, aTrackMsgs)


    def handle(self, _aMessage):
        sCmd       = self.m_aParts[0]
        nValue     = _aMessage[2]
        bActivated = (nValue > 0.5)

        if (sCmd == 'lockreboot'):
            self.m_bLockReboot = bActivated
            self.log('>>> New lock reboot value: %d' % (bActivated))
            return # lock reboot command processed, nothing else to do here!

        sTrackIdxRel = self.m_aParts[1]

        # check if user tries to operate in master track
        if (sTrackIdxRel == 'master'):
            if (sCmd == 'solo' and bActivated):
                for nTrackIdxAbs in self.tracks_range():
                    oTrack      = self.get_track(nTrackIdxAbs)
                    oTrack.solo = False

                    if (self.is_track_visible(nTrackIdxAbs)):
                        nTrackIdxRel = self.track_idx_rel(nTrackIdxAbs)
                        self.send_msg('solo/%d' % (nTrackIdxRel), 0.0)

            return # we do not manage any other command for master track

        # check if user tries to operate in selected track
        elif (sTrackIdxRel == 'selected'):
            oTrack       = self.sel_track()
            nTrackIdxAbs = self.sel_track_idx_abs()
            nTrackIdxRel = self.track_idx_rel(nTrackIdxAbs)

        # the user tries to operate in a normal track
        else:
            nTrackIdxRel = int(sTrackIdxRel)
            nTrackIdxAbs = self.track_idx_abs(nTrackIdxRel)

            if (self.is_track_available(nTrackIdxAbs) == False):
                if (sCmd == 'loop'):
                    # toggle off immediately since there is no track available for that toggle
                    self.send_msg("loop/%d" % (nTrackIdxRel), 0.0)

                return # unavailable track, nothing else to do here!

            # get the track
            oTrack = self.get_track(nTrackIdxAbs)

        oMixDev = oTrack.mixer_device

        if (sCmd == 'enable'):
            oTrack.mute = not bActivated

        elif (sCmd == 'solo'):
            oTrack.solo = bActivated

        elif (sCmd == 'crossa'):
            if (bActivated):
                oMixDev.crossfade_assign = 0 # turn on crossfade to 'A'
            else:
                oMixDev.crossfade_assign = 1 # change crossfade to 'none'

        elif (sCmd == 'crossb'):
            if (bActivated):
                oMixDev.crossfade_assign = 2 # turn on crossfade to 'B'
            else:
                oMixDev.crossfade_assign = 1 # change crossfade to 'none'

        elif (sCmd == 'stop'):
            bQuantizedStop = True
            oTrack.stop_all_clips(bQuantizedStop)

        elif (sCmd == 'reboot'):
            if (self.m_bLockReboot == True):
                # the reboot process occurrs in two steps:
                # 1) The first step happens when we receive the reboot bActivated = TRUE and
                #    we stop track, stop the volume auto-update and reset the effects
                # 2) The second step happens when we receive the reboot bActivated = FALSE and
                #    we reset the volume to the default volume and remove muted track
                if (bActivated == True):
                    bQuantizedStop = False
                    oTrack.stop_all_clips(bQuantizedStop)

                    # TrackVolAutoHandler  : stop the volume auto update for this track
                    # TrackDevSelectHandler: reset the effect devices affecting this track
                    self.update_observers('track_reboot', {'nTrackIdxAbs': nTrackIdxAbs})

                else:
                    # reset the volume and remove mute track
                    oMixDev.volume.value = self.m_nDefaultVol
                    oTrack.mute          = False

                    sName = self.to_ascii(oTrack.name, 20)
                    self.alert('> Rebooting track "%s"' % (sName))
            else:
                if (bActivated == True):
                    bQuantizedStop = False
                    oTrack.stop_all_clips(bQuantizedStop)

        elif (sCmd == 'arm'):
            oTrack.arm = bActivated

        elif (sCmd == 'select'):
            self.sel_track(oTrack)

        elif (sCmd == 'loop'):
            if (nTrackIdxAbs in self.m_hFocusedClips):
                nSceneIdxAbs = self.m_hFocusedClips[nTrackIdxAbs]
                aAllClipSlots = oTrack.clip_slots
                oClipSlot     = aAllClipSlots[nSceneIdxAbs]
                if (oClipSlot.has_clip == True):
                    # the clip is available! change the looping status!
                    oClip = oClipSlot.clip
                    oClip.looping = bActivated
                    self.send_msg("loop/%d" % (nTrackIdxRel), bActivated) # ACK message

                else:
                    # the clip is gone! remove it from hash and reset toggle button
                    del self.m_hFocusedClips[nTrackIdxAbs]
                    self.send_msg("loop/%d" % (nTrackIdxRel), 0.0)

            else:
                # toggle off immediately since there is no focused clip available for that track
                self.send_msg("loop/%d" % (nTrackIdxRel), 0.0)


    # Ableton Live events management *******************************************

    def add_listeners(self):
        self.remove_listeners()

        if (not self.song().tracks_has_listener(self.on_tracks_changed)):
            self.song().add_tracks_listener(self.on_tracks_changed)
        if (not self.song().view.selected_track_has_listener(self.on_sel_track_changed)):
            self.song().view.add_selected_track_listener(self.on_sel_track_changed)

        for nTrackIdxAbs in self.tracks_range():
            oTrack = self.get_track(nTrackIdxAbs)

            # foldable tracks (i.e. the tracks grouping other sub-tracks)
            # will not be managed
            if (oTrack.is_foldable == False):
                self.add_track_listeners(nTrackIdxAbs, oTrack)


    def on_tracks_changed(self):
        self.log('> TrackCmdHandler: tracks changed, updating listeners and GUI')
        self.add_listeners()
        self.update_tracks()
        self.update_selected_track()

        # TrackClipHandler: reload track clips
        # TrackVolHandler: update track volumes
        self.update_observers('tracks_changed')


    def on_sel_track_changed(self):
        self.update_selected_track()

        # ClipCmdHandler: update selected clip info
        # TrackVolHandler: update selected track volume
        self.update_observers('new_track_sel')


    def add_track_listeners(self, _nTrackIdxAbs, _oTrack):
        fStateCallback = lambda :self.on_track_state_changed(_oTrack, _nTrackIdxAbs)
        fViewCallback  = lambda :self.on_track_view_changed(_oTrack, _nTrackIdxAbs)

        if (not _oTrack in self.m_hTrackListeners):
            _oTrack.add_mute_listener(fStateCallback)
            _oTrack.add_solo_listener(fStateCallback)
            _oTrack.add_arm_listener(fStateCallback)
            _oTrack.mixer_device.add_crossfade_assign_listener(fStateCallback)
            _oTrack.add_name_listener(fViewCallback)
            _oTrack.add_color_listener(fViewCallback)
            self.m_hTrackListeners[_oTrack] = [fStateCallback, fViewCallback]


    def on_track_state_changed(self, _oTrack, _nTrackIdxAbs):
        if (self.is_track_visible(_nTrackIdxAbs)):
            aTrackMsgs = []

            nEnable = 0.0 if (_oTrack.mute) else 1.0
            nSolo   = 1.0 if (_oTrack.solo) else 0.0
            nArm    = 1.0 if (_oTrack.arm)  else 0.0
            oMixDev = _oTrack.mixer_device
            nCrossA = 1.0 if (oMixDev.crossfade_assign == 0) else 0.0
            nCrossB = 1.0 if (oMixDev.crossfade_assign == 2) else 0.0

            nTrackIdxRel = self.track_idx_rel(_nTrackIdxAbs)
            self.append_idx_msg('enable', nTrackIdxRel, nEnable, aTrackMsgs)
            self.append_idx_msg('solo'  , nTrackIdxRel, nSolo  , aTrackMsgs)
            self.append_idx_msg('crossa', nTrackIdxRel, nCrossA, aTrackMsgs)
            self.append_idx_msg('crossb', nTrackIdxRel, nCrossB, aTrackMsgs)
            self.append_idx_msg('arm'   , nTrackIdxRel, nArm   , aTrackMsgs)

            if (self.sel_track_idx_abs() == _nTrackIdxAbs):
                self.append_idx_msg('enable', 'selected', nEnable, aTrackMsgs)
                self.append_idx_msg('solo'  , 'selected', nSolo  , aTrackMsgs)
                self.append_idx_msg('crossa', 'selected', nCrossA, aTrackMsgs)
                self.append_idx_msg('crossb', 'selected', nCrossB, aTrackMsgs)
                self.append_idx_msg('arm'   , 'selected', nArm   , aTrackMsgs)

            sMsg = 'TrackCmdHandler, on_track_state_changed, track/cmd, update'
            self.send_bundle(sMsg, aTrackMsgs)

            # TrackDevSelectHandler: update solo toggle for channel assigned to this track
            hArgs = { 'nTrackIdxAbs': _nTrackIdxAbs, 'bSolo': _oTrack.solo }
            self.update_observers('track_solo_update', hArgs)


    def on_track_view_changed(self, _oTrack, _nTrackIdxAbs):
        if (self.is_track_visible(_nTrackIdxAbs)):
            nTrackIdxRel = self.track_idx_rel(_nTrackIdxAbs)
            sName   = self.to_ascii(_oTrack.name, 20)
            sColor  = self.to_color(_oTrack.color)
            sAttrs  = '{"label": "%s", "css": "background-color: %s"}' % (sName, sColor)
            self.send('/EDIT', ['track_cmd_select_%d' % (nTrackIdxRel), sAttrs])


    def remove_listeners(self):
        if (self.song().tracks_has_listener(self.on_tracks_changed)):
            self.song().remove_tracks_listener(self.on_tracks_changed)
        if (self.song().view.selected_track_has_listener(self.on_sel_track_changed)):
            self.song().view.remove_selected_track_listener(self.on_sel_track_changed)

        for oTrack in self.m_hTrackListeners:
            if (not oTrack in self.m_hTrackListeners):
                continue # the key exists but the hash cannot recover the value!!!

            aListeners = self.m_hTrackListeners[oTrack]
            fStateCallback = aListeners[0]
            fViewCallback  = aListeners[1]

            if (oTrack != None):
                if (oTrack.mute_has_listener(fStateCallback)):
                    oTrack.remove_mute_listener(fStateCallback)
                if (oTrack.solo_has_listener(fStateCallback)):
                    oTrack.remove_solo_listener(fStateCallback)
                if (oTrack.arm_has_listener(fStateCallback)):
                    oTrack.remove_arm_listener(fStateCallback)
                if (oTrack.mixer_device.crossfade_assign_has_listener(fStateCallback)):
                    oTrack.mixer_device.remove_crossfade_assign_listener(fStateCallback)
                if (oTrack.name_has_listener(fViewCallback)):
                    oTrack.remove_name_listener(fViewCallback)
                if (oTrack.color_has_listener(fViewCallback)):
                    oTrack.remove_color_listener(fViewCallback)

        self.m_hTrackListeners = {}


