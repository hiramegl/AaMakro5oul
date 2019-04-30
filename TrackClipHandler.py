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

import os
import time
import datetime

from CoreHandler import CoreHandler

# ******************************************************************************
# Track Clip commands handler
# ******************************************************************************

class TrackClipHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = False # we need to listen to release of next-select toggle button
        bLogRxMsgs     = False
        self.config('/track/clip', bIgnoreRelease, bLogRxMsgs)

        for sTrackIndex in self.track_indeces_list():
            self.add_callbacks_pref(sTrackIndex, self.scene_indeces_list())
        self.add_callbacks_pref('next', ['select', 'clear'])
        self.add_callbacks(['next/list/modal', 'navigate', 'locknavigate'])

        self.m_hTrackClipOffMsgs = {} # to toggle off the current playing clip or all clips when session region moves
        self.m_aTrackClipAttMsgs = [] # to remove all track clip attributes when session region moves

        self.m_aTrackClipHistory = [] # to navigate back and forward in the played track clip history

        self.m_hClipListeners = {}
        self.m_hSlotListeners = {}

        self.reset_track_clips()
        self.clear_next_clips()
        self.update_track_clips()
        self.add_listeners()
        self.open_clip_logger()


    def disconnect(self):
        self.close_clip_logger()
        self.remove_listeners()
        self.reset_track_clips()
        self.clear_next_clips()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'new_tracks_sel' or # SessionCmdHandler
            _sEvent == 'new_scenes_sel' or # SessionCmdHandler
            _sEvent == 'session_reset'):   # SessionCmdHandler
            self.update_track_clips()


        elif (_sEvent == 'tracks_changed' or # TrackCmdHandler
            _sEvent == 'scenes_changed'):    # SceneCmdHandler
            self.add_listeners()
            self.update_track_clips()

        elif (_sEvent == 'next_clips_clear'):
            self.clear_next_clips()


    def reset_track_clips(self):
        self.m_bNavigate = False
        self.send_msg('navigate', 0.0)
        self.m_bLockNavigate = True
        self.send_msg('locknavigate', 1.0)

        aTrackClipMsgs = []

        for nTrackIdxRel in range(self.gui_num_tracks()):
            for nSceneIdxRel in range(self.gui_num_scenes()):
                sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
                sId    = 'track_clip_%d_%d'  % (nTrackIdxRel, nSceneIdxRel)
                sAddr  = '/track/clip/%d/%d' % (nTrackIdxRel, nSceneIdxRel)
                aTrackClipMsgs.append(['/EDIT' , [sId, sAttrs]])
                aTrackClipMsgs.append([sAddr, 0.0]) # turn off toggle

        aTrackClipMsgs.append(['/clip/info/latest/title', '-'])

        sMsg = 'TrackClipHandler, reset_track_clips, reset'
        self.send_bundle(sMsg, aTrackClipMsgs)


    def clear_next_clips(self):
        self.next_clips_clear()
        self.send_msg('next/select', 0.0)
        self.send_msg('next/count' , 0)
        self.send_msg('next/list'  , '-')


    def update_track_clips(self):
        # if there were clips available then clear the labels
        if (len(self.m_aTrackClipAttMsgs) > 0):
            sMsg = 'TrackClipHandler, update_track_clips, clearing_old_clips_attrs'
            self.send_bundle(sMsg, self.m_aTrackClipAttMsgs)
            self.m_aTrackClipAttMsgs = []

        # if there were clips playing then clear the toggles
        if (len(self.m_hTrackClipOffMsgs) > 0):
            sMsg = 'TrackClipHandler, update_track_clips, clearing_old_clips_toggl'
            self.send_bundle(sMsg, self.m_hTrackClipOffMsgs.values())
            self.m_hTrackClipOffMsgs = {}

        aTrackClipMsgs = []

        # iterate through the visible tracks in GUI by using the absolute indeces of the track
        for nTrackIdxAbs in self.gui_visible_tracks_abs_range():
            if (self.is_track_available(nTrackIdxAbs) == False):
                continue # unavailable track, nothing else to do for this track

            oTrack        = self.get_track(nTrackIdxAbs)
            aAllClipSlots = oTrack.clip_slots

            # iterate through the visible scenes in GUI by using the absolute indices of the scene
            for nSceneIdxAbs in self.gui_visible_scenes_abs_range():
                if (self.is_scene_available(nSceneIdxAbs) == False):
                    continue # unavailable scene, nothing else to do for this clip

                oClipSlot = aAllClipSlots[nSceneIdxAbs]
                if (oClipSlot.has_clip == False):
                    continue # empty clip, continue with the next scene index

                oClip = oClipSlot.clip
                self.update_track_clip_label(nTrackIdxAbs, nSceneIdxAbs, oClip, aTrackClipMsgs)

                # if the clip is playing then add a message to toggle the clip on and
                # save a message to toggle the clip off later
                if (oClip.is_playing):
                    nTrackIdxRel = self.track_idx_rel(nTrackIdxAbs)
                    nSceneIdxRel = self.scene_idx_rel(nSceneIdxAbs)
                    sAddr = '/track/clip/%d/%d' % (nTrackIdxRel, nSceneIdxRel)
                    aTrackClipMsgs.append([sAddr, 1.0]) # toggle clip on

                    sTrackClipKey = '%d,%d' % (nTrackIdxRel, nSceneIdxRel)
                    self.m_hTrackClipOffMsgs[sTrackClipKey] = [sAddr, 0.0]

        sMsg = 'TrackClipHandler, update_track_clips, update_clip_labels_and_toggles'
        self.send_bundle(sMsg, aTrackClipMsgs)


    def handle(self, _aMessage):
        # parse command parts
        sTrackIdxRel = self.m_aParts[0]

        # track clip navigation (not firing the clip) ------------------------------------

        if (sTrackIdxRel == 'locknavigate'):
            self.m_bLockNavigate = _aMessage[2] > 0.5
            return # lock navigation command processed, nothing else to do here!

        if (sTrackIdxRel == 'navigate'):
            self.m_bNavigate = _aMessage[2] > 0.5
            self.send_msg('navigate', _aMessage[2])
            if (_aMessage[2] > 0.5):
                self.alert('> Navigation ON')
            else:
                self.alert('> Navigation OFF')
            return # navigation command processed, nothing else to do here!

        sSceneIdxRel = self.m_aParts[1]

        # next-clip selection toggle (used for build-ups and drop-downs) -----------------

        if (sTrackIdxRel == 'next'):
            if (sSceneIdxRel == 'select'):
                self.next_selection_on(_aMessage[2] > 0.5)
                self.send_msg('next/select', _aMessage[2])
                if (_aMessage[2] > 0.5):
                    self.alert('> Next clip selection ON')
                else:
                    self.alert('> Next clip selection OFF')

            elif (sSceneIdxRel == 'clear'):
                self.clear_next_clips()

            return # next-song selection command processed (for build-ups or break-downs), nothing else to do here!

        # parse track and scene indeces and verify clip is available ---------------------

        sAddr        = '%s/%s' % (sTrackIdxRel, sSceneIdxRel)
        nTrackIdxAbs = self.track_idx_abs(int(sTrackIdxRel))
        nSceneIdxAbs = self.scene_idx_abs(int(sSceneIdxRel))

        if (self.is_clip_available(nTrackIdxAbs, nSceneIdxAbs) == False):
            self.send('/clip/info/latest/title', '-')
            self.send_msg(sAddr, 0.0) # turn off the toggle since the clip is not available
            return # unavailable track or scene, nothing else to do here!

        # next-clip selection addition ---------------------------------------------------

        # if the user pressed a valid clip and we are in selection mode
        # then add the clip to the list, update count and list and return
        if (self.next_selection_on() == True):
            self.add_next_clip(nTrackIdxAbs, nSceneIdxAbs, '/track/clip/%s' % (sAddr))
            return # nothing else to do here

        # normal clip fire processing (or navigation!) -----------------------------------

        # fire the clip slot, the remote GUI will be updated through
        # the event listener handlers
        oTrack        = self.get_track(nTrackIdxAbs)
        aAllClipSlots = oTrack.clip_slots
        oClipSlot     = aAllClipSlots[nSceneIdxAbs]

        if (self.m_bNavigate == True):
            # if the track is actually playing then turn the clip button on,
            # otherwise turn the clip button off since the clip is not playing now
            if (oClipSlot.is_playing == True):
                self.send_msg(sAddr, 1.0)
            else:
                self.send_msg(sAddr, 0.0)

            # turn navigation off immediately (is easy to forget that we are in navigation mode)
            self.m_bNavigate = False
            self.send_msg('navigate', 0.0)

            # navigate to the clip
            self.sel_track(oTrack)
            self.sel_scene(self.get_scene(nSceneIdxAbs))

            # TrackCmdHandler: update loop toggle button for track
            hArgs = { 'nTrackIdxAbs': nTrackIdxAbs, 'nSceneIdxAbs': nSceneIdxAbs }
            self.update_observers('clip_state_updated', hArgs)

        else:
            oClipSlot.fire()

            # immediately select the fired clip slot (if lock navigation is enabled)
            if (self.m_bLockNavigate == True):
                self.sel_track(oTrack)
                self.sel_scene(self.get_scene(nSceneIdxAbs))

        # if the clip slot did not have a clip, toggle the
        # clip off in the remote GUI immediately
        if (oClipSlot.has_clip == False):
            self.send('/clip/info/latest/title', '-')
            self.send_msg(sAddr, 0.0)


    def add_next_clip(self, _nTrackIdxAbs, _nSceneIdxAbs, _sAddr):
        # turn clip button off since it will actually not playing now
        # but until a build-up or a break-down is launched
        self.send(_sAddr, 0.0)

        oTrack        = self.get_track(_nTrackIdxAbs)
        aAllClipSlots = oTrack.clip_slots
        oClipSlot     = aAllClipSlots[_nSceneIdxAbs]

        self.next_clips_add(_nTrackIdxAbs, _nSceneIdxAbs)

        if (oClipSlot.has_clip == True):
            oClip  = oClipSlot.clip
            sTitle = self.to_ascii(oClip.name)
        else:
            sTitle = 'Empty'

        self.alert('> Next clip selected (%d|%d): %s' % (_nTrackIdxAbs, _nSceneIdxAbs, sTitle))

        aList = []
        aNextClips = self.next_clips()
        for aNextClip in aNextClips:
            oTrack        = self.get_track(aNextClip[0])
            aAllClipSlots = oTrack.clip_slots
            oClipSlot     = aAllClipSlots[aNextClip[1]]
            if (oClipSlot.has_clip == True):
                oClip  = oClipSlot.clip
                sTitle = self.to_ascii(oClip.name)
            else:
                sTitle = 'Empty'
            aList.append('%d|%d: %s' % (aNextClip[0], aNextClip[1], sTitle))

        # update count and list
        self.send_msg('next/count', len(aNextClips))
        self.send_msg('next/list' , '<br>'.join(aList))


    # Ableton Live events management *******************************************

    def add_listeners(self):
        self.remove_listeners()

        for nTrackIdxAbs in self.tracks_range():
            oTrack = self.get_track(nTrackIdxAbs)
            aAllClipSlots = oTrack.clip_slots

            for nSceneIdxAbs in self.available_scenes():
                oClipSlot = aAllClipSlots[nSceneIdxAbs]

                self.add_slot_listener(oClipSlot, nTrackIdxAbs, nSceneIdxAbs)
                if (oClipSlot.has_clip):
                    self.add_clip_listener(oClipSlot.clip, nTrackIdxAbs, nSceneIdxAbs)


    def add_clip_listener(self, _oClip, _nTrackIdxAbs, _nSceneIdxAbs):
        fPlayCallback = lambda :self.on_clip_play_changed(_oClip, _nTrackIdxAbs, _nSceneIdxAbs)
        fViewCallback = lambda :self.on_clip_view_changed(_oClip, _nTrackIdxAbs, _nSceneIdxAbs)

        if (not self.m_hClipListeners.has_key(_oClip)):
            _oClip.add_playing_status_listener(fPlayCallback)
            _oClip.add_name_listener(fViewCallback)
            _oClip.add_color_listener(fViewCallback)
            self.m_hClipListeners[_oClip] = [fPlayCallback, fViewCallback]


    def on_clip_play_changed(self, _oClip, _nTrackIdxAbs, _nSceneIdxAbs):
        if (_oClip.is_playing):
            self.toggle_clip_on(_nTrackIdxAbs, _nSceneIdxAbs)
        else:
            self.toggle_clip_off(_nTrackIdxAbs, _nSceneIdxAbs)


    def on_clip_view_changed(self, _oClip, _nTrackIdxAbs, _nSceneIdxAbs):
        self.update_track_clip_label(_nTrackIdxAbs, _nSceneIdxAbs, _oClip)


    def add_slot_listener(self, _oClipSlot, _nTrackIdxAbs, _nSceneIdxAbs):
        fViewCallback = lambda :self.on_slot_clip_changed(_oClipSlot, _nTrackIdxAbs, _nSceneIdxAbs)

        if (not self.m_hSlotListeners.has_key(_oClipSlot)):
            _oClipSlot.add_has_clip_listener(fViewCallback)
            self.m_hSlotListeners[_oClipSlot] = [fViewCallback]


    def on_slot_clip_changed(self, _oClipSlot, _nTrackIdxAbs, _nSceneIdxAbs):
        # TODO: TDMA: Solve this since the oClip will not be removed if the clipslot has no clip
        oClip = _oClipSlot.clip if (_oClipSlot.has_clip) else None

        if (_oClipSlot.has_clip):
            self.add_clip_listener(oClip, _nTrackIdxAbs, _nSceneIdxAbs) # clip added to the clip-slot

        else:
            self.remove_clip_listener(oClip) # clip removed from the clip-slot

        # update the GUI if visible
        self.update_track_clip_label(_nTrackIdxAbs, _nSceneIdxAbs, oClip)


    def remove_listeners(self):
        for oClip in self.m_hClipListeners:
            self.remove_clip_listener(oClip)

        for oClipSlot in self.m_hSlotListeners:
            if (not oClipSlot in self.m_hSlotListeners):
                continue # the key exists but the hash cannot recover the value!!!

            aListeners = self.m_hSlotListeners[oClipSlot]
            fViewCallback = aListeners[0]

            if (oClipSlot != None):
                if (oClipSlot.has_clip_has_listener(fViewCallback)):
                    oClipSlot.remove_has_clip_listener(fViewCallback)

        self.m_hClipListeners = {}
        self.m_hSlotListeners = {}


    def remove_clip_listener(self, _oClip):
        if (_oClip == None):
            return

        if (_oClip in self.m_hClipListeners):
            aListeners = self.m_hClipListeners[_oClip]
            fPlayCallback = aListeners[0]
            fViewCallback = aListeners[1]

            if (_oClip.playing_status_has_listener(fPlayCallback)):
                _oClip.remove_playing_status_listener(fPlayCallback)
            if (_oClip.name_has_listener(fViewCallback)):
                _oClip.remove_name_listener(fViewCallback)
            if (_oClip.color_has_listener(fViewCallback)):
                _oClip.remove_color_listener(fViewCallback)


    def toggle_clip_on(self, _nTrackIdxAbs, _nSceneIdxAbs):
        self.log('> adding clip to history, track: %d, scene: %d' % (_nTrackIdxAbs, _nSceneIdxAbs))
        self.m_aTrackClipHistory.append([_nTrackIdxAbs, _nSceneIdxAbs])

        if (self.is_clip_visible(_nTrackIdxAbs, _nSceneIdxAbs) == False):
            return # non-visible clip, nothing else to do here

        oTrack        = self.get_track(_nTrackIdxAbs)
        aAllClipSlots = oTrack.clip_slots
        oClipSlot     = aAllClipSlots[_nSceneIdxAbs]

        if (oClipSlot.has_clip):
            nTrackIdxRel = self.track_idx_rel(_nTrackIdxAbs)
            nSceneIdxRel = self.scene_idx_rel(_nSceneIdxAbs)
            sAddr = '/track/clip/%d/%d' % (nTrackIdxRel, nSceneIdxRel)

            # toggle on the new playing clip in the gui
            self.send(sAddr, 1.0)

            # save a message to toggle off the clip later
            sTrackClipKey = '%d,%d' % (nTrackIdxRel, nSceneIdxRel)
            self.m_hTrackClipOffMsgs[sTrackClipKey] = [sAddr, 0.0]

            # update the title of this latest clip
            oClip  = oClipSlot.clip
            sTitle = self.to_ascii(oClip.name)
            sTrack = self.to_ascii(oTrack.name)

            self.send('/clip/info/latest/title', sTitle)

            # update local gui
            lAlert = (_nTrackIdxAbs + 1, sTrack, _nSceneIdxAbs + 1, sTitle)
            self.alert('> Playing clip [%d|%s, %d]: %s' % lAlert)

            # log
            lLog = (
                _nTrackIdxAbs + 1,
                sTrack,
                _nSceneIdxAbs + 1,
                sTitle,
                oClip.start_marker,
                oClip.loop_start,
                oClip.loop_end
            )
            sLog = '> Playing [%d|%s, %d]: %s @ %f [%f, %f]' % lLog
            self.log(sLog)
            self.log_clip_msg(sLog)

            # TrackCmdHandler: update loop toggle button for track
            hArgs = { 'nTrackIdxAbs': _nTrackIdxAbs, 'nSceneIdxAbs': _nSceneIdxAbs }
            self.update_observers('clip_state_updated', hArgs)


    def toggle_clip_off(self, _nTrackIdxAbs, _nSceneIdxAbs):

        if (self.is_track_visible(_nTrackIdxAbs) == False):
            return # non-visible track, nothing else to do here!

        # track is remote GUI visible, send a toggle off message if there was a
        # playing clip for the track and remove the toggle off message
        nTrackIdxRel = self.track_idx_rel(_nTrackIdxAbs)
        nSceneIdxRel = self.scene_idx_rel(_nSceneIdxAbs)
        sTrackClipKey = '%d,%d' % (nTrackIdxRel, nSceneIdxRel)
        if (sTrackClipKey in self.m_hTrackClipOffMsgs):
            aOffMsg = self.m_hTrackClipOffMsgs[sTrackClipKey]
            self.send(aOffMsg[0], aOffMsg[1])
            del self.m_hTrackClipOffMsgs[sTrackClipKey]

        # ON CLIP OFF we do not update clip states since this event comes after
        # dispatching a CLIP ON and thus making that the newly launched clip loses focus


    # TODO: merge "off" messages and "on" messages to send in order not to do double work
    # TDAM: by turning off first and the turning on ...
    def update_track_clip_label(self, _nTrackIdxAbs, _nSceneIdxAbs, _oClip = None, _aMsgs = None):
        if (self.is_clip_visible(_nTrackIdxAbs, _nSceneIdxAbs) == False):
            return # track_clip is not visible, nothing else to do here

        if (_oClip != None):
            sName  = self.to_ascii(_oClip.name, 20)
            sColor = self.to_color(_oClip.color)
        else:
            sName  = '-'
            sColor = 'var(--color-raised)'

        nTrackIdxRel = self.track_idx_rel(_nTrackIdxAbs)
        nSceneIdxRel = self.scene_idx_rel(_nSceneIdxAbs)
        sLedAttr     = '.toggle.on:after {left: 0; top: 5; right: 0; height: 32px !important; opacity: 0.3; background-color: red}'
        sId          = 'track_clip_%d_%d' % (nTrackIdxRel, nSceneIdxRel)
        sAttrs       = '{"label": "%s", "css": "background-color: %s; %s"}' % (sName, sColor, sLedAttr)

        # add to a bundle of messages to send or send message immediately
        if (_aMsgs != None):
            _aMsgs.append(['/EDIT', [sId, sAttrs]])
        else:
            self.send('/EDIT', [sId, sAttrs])

        if (_oClip != None):
            # save message to clear the clip GUI label when scrolling session region
            sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'
            self.m_aTrackClipAttMsgs.append(['/EDIT', [sId, sAttrs]])


    def open_clip_logger(self):
        nTime = time.time()
        sTime = datetime.datetime.fromtimestamp(nTime).strftime('%Y_%m_%d__%H_%M_%S')
        sPath = '%s/session_%s.txt' % (self.get_root_path(), sTime)

        self.log('>  cwd: %s, root: %s, clip log: %s' % (self.get_cwd(), self.get_root_path(), sPath))
        self.m_oFile = open(sPath, 'w+')
        self.log_clip_msg('Opening %s session' % (self.m_sProductName))


    def log_clip_msg(self, _sMessage):
        nTime = time.time()
        sTime = datetime.datetime.fromtimestamp(nTime).strftime('%Y-%m-%d %H:%M:%S.%f')
        self.m_oFile.write('%s: %s\r\n' % (sTime, _sMessage))


    def close_clip_logger(self):
        self.log_clip_msg('Closing %s session' % (self.m_sProductName))
        self.m_oFile.close()


