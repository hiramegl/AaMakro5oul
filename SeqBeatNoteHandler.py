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
# Sequencer Beat Notes commands handler
# ******************************************************************************

class SeqBeatNoteHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = False # False -> do not ignore release!
        bLogRxMsgs     = False
        self.config('/seq/beat/note', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks(['mute', 'solo', 'sel'])

        self.m_aMuteOffMsgs = []
        self.m_aSelOffMsgs  = []

        self.reset_note_states()
        self.update_note_states()


    def disconnect(self):
        self.reset_note_states()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'session_reset' or   # SessionCmdHandler
            _sEvent == 'new_track_sel' or   # TrackCmdHandler
            _sEvent == 'new_scene_sel' or   # SceneCmdHandler
            _sEvent == 'beatgrid_changed'): # from SeqCmdHandler
            self.update_note_states()


    def reset_note_states(self):
        aNoteStateMsgs = []
        for nButton in range(0, self.m_nNumNotesInOct):
            aNoteStateMsgs.append(['/seq/beat/note/mute', [nButton, 0.0]])
            aNoteStateMsgs.append(['/seq/beat/note/solo', [nButton, 0.0]])
            aNoteStateMsgs.append(['/seq/beat/note/sel' , [nButton, 0.0]])
        sMsg = 'SeqBeatNoteHandler, reset_note_states, seq/beat/note, resetting'
        self.send_bundle(sMsg, aNoteStateMsgs)


    def update_note_states(self):
        self.log('SeqBeatNoteHandler, update_note_states, updating_gui');

        if (len(self.m_aMuteOffMsgs) > 0):
            sMsg = 'SeqBeatNoteHandler, update_note_states, mute_off'
            self.send_bundle(sMsg, self.m_aMuteOffMsgs)
            self.m_aMuteOffMsgs = []

        if (len(self.m_aSelOffMsgs) > 0):
            sMsg = 'SeqBeatNoteHandler, update_note_states, sel_off'
            self.send_bundle(sMsg, self.m_aSelOffMsgs)
            self.m_aSelOffMsgs = []

        oSelectedTrack = self.sel_track()
        if (oSelectedTrack.can_be_armed == False):
            return # is a return-track, nothing else to do here

        oClipSlot = self.sel_clip_slot()
        if (oClipSlot.has_clip == False):
            return # Empty clip slot, nothing else to do here

        oClip = oClipSlot.clip
        if (oClip.is_midi_clip == False):
            return # Non-MIDI clip, nothing else to do here

        # in case the highlighted clip is MIDI update the note buttons

        oClip.select_all_notes()
        aNotes = oClip.get_selected_notes()
        oClip.deselect_all_notes()

        aMuteNotes = [] # to update mute buttons

        for oNote in aNotes:
            # oNote format: Note, Time, Length, Velocity, Mute
            nNote = oNote[0] # Note value, between 0 and 127
            nTime = oNote[1] # Time

            if (self.is_note_visible(nNote, nTime) == False):
                continue # nothing else to do for this note since is not visible in remote GUI

            nLen  = oNote[2] # Lenght
            nVel  = oNote[3] # Velocity
            bMute = oNote[4] # Mute

            nRow  = self.note_idx_rel(nNote) # C1 (36 -> 11), B1 (47 -> 0)

            # if this note is muted then save it in order to update the note muted state buttons
            if (bMute == True):
                aMuteNotes.append(nRow)

        aNoteStateMsgs = [] # to toggle mute and select buttons

        # update note mute buttons (in case there is any muted note detected)
        zMuteNotes = set(aMuteNotes)
        for nMuteNote in zMuteNotes:
            aNoteStateMsgs.append(['/seq/beat/note/mute', [nMuteNote, 0.0]])
            self.m_aMuteOffMsgs.append(['/seq/beat/note/mute', [nMuteNote, 0.0]]) # to clean gui later

        # send note selected message (C1 by default after updating)
        aNoteStateMsgs.append(['/seq/beat/note/sel', [self.sel_note_rel_idx(), 1.0]])
        self.m_aSelOffMsgs.append(['/seq/beat/note/sel', [self.sel_note_rel_idx(), 0.0]]) # to clean gui later

        sMsg = 'SeqBeatNoteHandler, update_note_states, seq/beat/note'
        self.send_bundle(sMsg, aNoteStateMsgs)


    def handle(self, _aMessage):
        # get the selected track
        oSelectedTrack = self.sel_track()
        if (oSelectedTrack.can_be_armed == False):
            self.send(self.m_sAddr, [_aMessage[2], 0.0]) # turn toggle button off
            return # is a return-track, nothing else to do here

        # get the selected clip slot
        oClipSlot = self.sel_clip_slot()
        if (oClipSlot.has_clip == False):
            self.send(self.m_sAddr, [_aMessage[2], 0.0]) # turn toggle button off
            return # empty clip slot, nothing else to do here!

        oClip = oClipSlot.clip
        if (oClip.is_midi_clip == False):
            self.send(self.m_sAddr, [_aMessage[2], 0.0]) # turn toggle button off
            return # non-MIDI clip, nothing else to do here!

        # read button index and status
        nButton    = _aMessage[2] # a value between 0 and 11 (number of the button)
        nButStatus = _aMessage[3] # 0 if toggle off and 1 if toggle is on
        nButtonInt = int(nButton)
        nNote      = self.note_idx_abs(nButtonInt)

        # read all notes
        oClip.select_all_notes()
        aSelNotes = list(oClip.get_selected_notes())
        oClip.deselect_all_notes()

        if (self.m_sCmd == 'mute'):
            for oNote in aSelNotes:
                if oNote[0] == nNote:
                    self.toggle_note_mute(oClip, oNote, nButStatus)

        elif (self.m_sCmd == 'solo'):
            for oNote in aSelNotes:
                if oNote[0] != nNote:
                    self.toggle_note_mute(oClip, oNote, nButStatus)

        elif (self.m_sCmd == 'sel'):
            # if a new note has been selected then update the new selected index
            # and deactivate the old selected note in the gui
            if (nButtonInt != self.sel_note_rel_idx() and nButStatus > 0.5):
                self.sel_note_rel_idx(nButtonInt)
                sMsg = 'SeqBeatNoteHandler, handle, seq/beat/note/sel, toggle_old_note_off'
                self.send_bundle(sMsg, self.m_aSelOffMsgs)
                self.update_observers('beat_note_selected') # forward event to update velocity values

            self.send(self.m_sAddr, [nButton, 1.0]) # toggle the new note on immediately
            self.m_aSelOffMsgs.append(['/seq/beat/note/sel', [self.sel_note_rel_idx(), 0.0]]) # to clean gui later

    def toggle_note_mute(self, _oClip, _oNote, _nStatus):
        # Note format: [0]Note, [1]Time, [2]Length, [3]Velocity, [4]Mute

        # remove notes:
        # (from_time [double], from_pitch [int], time_span [double], pitch_span [int])
        _oClip.remove_notes(_oNote[1], _oNote[0], _oNote[2], 1)

        # add it as muted/unmuted:
        # (pitch [int], time [float], length [float], velocity [int], muted [boolean])
        aNotes = list([])
        aNotes.append([_oNote[0], _oNote[1], _oNote[2], _oNote[3], _nStatus > 0.5])
        _oClip.replace_selected_notes(tuple(aNotes))
        _oClip.deselect_all_notes()


