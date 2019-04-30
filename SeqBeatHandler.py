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
# Sequencer Beat commands handler
# ******************************************************************************

class SeqBeatHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = False # False -> do not ignore release!
        bLogRxMsgs     = False
        self.config('/seq/beat', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks_pref('bit', self.beats_indeces_list())
        self.add_callbacks_pref('vel', self.beats_indeces_list() + [8])
        self.add_callbacks(['tools'])

        self.note_offset(self.m_nDefNoteOffset) # start in Octave 1

        self.m_nMaxVelocity     = 127.0
        self.m_nDefaultVelocity = 127.0

        self.m_nBitDuration     = 1.0 / self.m_nNumBitsInBeat
        self.m_nBarsInGrid      = self.gui_vis_beats() / self.m_nNumBeatsInBar

        self.m_aNoteOffMsgs = []
        self.m_aVelOffMsgs  = []

        self.reset_beat_grid()
        self.update_beat_grid()


    def disconnect(self):
        self.reset_beat_grid()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'session_reset'    or # from SessionCmdHandler
            _sEvent == 'new_track_sel'    or # from TrackCmdHandler
            _sEvent == 'new_scene_sel'    or # from SceneCmdHandler
            _sEvent == 'beatgrid_changed' or # from SeqCmdHandler
            _sEvent == 'duplicate_loop'):    # from ClipLoopHandler
            self.update_beat_grid()

        elif (_sEvent == 'beat_note_selected'): # from SeqBeatNoteHandler
            if (len(self.m_aVelOffMsgs) > 0):
                sMsg = 'SeqBeatHandler, update, vel_off'
                self.send_bundle(sMsg, self.m_aVelOffMsgs)
                self.m_aVelOffMsgs = []

            oClipSlot = self.sel_clip_slot()
            oClip     = oClipSlot.clip

            oClip.select_all_notes()
            aNotes = oClip.get_selected_notes()
            oClip.deselect_all_notes()

            aNoteVelMsgs = []

            for oNote in aNotes:
                # oNote format: [Note, Time, Length, Velocity, Mute]
                nNoteAbs = oNote[0] # Note value, between 0 and 127
                nTimeAbs = oNote[1] # Time

                if (self.is_note_visible(nNoteAbs, nTimeAbs) == False):
                    continue # nothing else to do for this note since is not visible in remote GUI

                nNoteRel = self.note_idx_rel(nNoteAbs) # C1 (36 -> 11), B1 (47 -> 0)
                nTimeRel = self.note_time_rel(nTimeAbs)

                # if this note is selected note index then send the velocity value to the gui
                if (nNoteRel == self.sel_note_rel_idx()):
                    nVel  = oNote[3]                     # Velocity
                    nBeat = int(nTimeRel)                # floor(time)
                    nBit  = nTimeRel - float(nBeat)      # 0.0, 0.25, 0.5 or 0.75
                    nCol  = nBit * self.m_nNumBitsInBeat # 0,   1,    2   or 3

                    sVelAddress = '/seq/beat/vel/{0}'.format(nBeat)
                    aNoteVelMsgs.append([sVelAddress, [nCol, nVel / 100.0]])
                    self.m_aVelOffMsgs.append([sVelAddress, [nCol, 0.0]]) # to clean gui later

            sMsg = 'SeqBeatHandler, update, seq/beat/vel'
            self.send_bundle(sMsg, aNoteVelMsgs)


    def reset_beat_grid(self):
        for nBeat in range(0, self.gui_vis_beats()):
            aBeatMsgs = []
            for nCol in range (0, self.m_nNumBitsInBeat):
                aBeatMsgs.append(['/seq/beat/vel/{0}'.format(nBeat), [nCol, 0.0]])
            aBeatMsgs.append(['/seq/beat/vel/8', [0.0]])
            for nButton in range(0, self.m_nNumBitsInBeat * CoreHandler.m_nGuiVisNotes):
                aBeatMsgs.append(['/seq/beat/bit/{0}'.format(nBeat), [nButton, 0.0]])
            sMsg = 'SeqBeatHandler, reset_beat_grid, seq/beat, resetting'
            self.send_bundle(sMsg, aBeatMsgs)


    def update_beat_grid(self):
        self.log('SeqBeatHandler, update_beat_grid, updating_gui');

        # clear old notes
        if (len(self.m_aNoteOffMsgs) > 0):
            sMsg = 'SeqBeatHandler, update_beat_grid, note_off'
            self.send_bundle(sMsg, self.m_aNoteOffMsgs)
            self.m_aNoteOffMsgs = []

        if (len(self.m_aVelOffMsgs) > 0):
            sMsg = 'SeqBeatHandler, update_beat_grid, vel_off'
            self.send_bundle(sMsg, self.m_aVelOffMsgs)
            self.m_aVelOffMsgs = []

        oSelectedTrack = self.sel_track()
        if (oSelectedTrack.can_be_armed == False):
            return # is a return-track, nothing else to do here

        oClipSlot = self.sel_clip_slot()
        if (oClipSlot.has_clip == False):
            return # Empty clip slot, nothing else to do here

        oClip = oClipSlot.clip
        if (oClip.is_midi_clip == False):
            return # Non-MIDI clip, nothing else to do here

        # in case the highlighted clip is MIDI update the beat grid

        # read all notes
        oClip.select_all_notes()
        aNotes = oClip.get_selected_notes()
        oClip.deselect_all_notes()

        # select highest note of the current octave by default
        self.sel_note_rel_idx(0)

        aNoteInfoMsgs = [] # to toggle beat-note buttons

        for oNote in aNotes:
            # oNote format: [Note, Time, Length, Velocity, Mute]
            nNoteAbs = oNote[0] # Note value, between 0 and 127
            nTimeAbs = oNote[1] # Time
            nVel     = oNote[3] # Velocity 

            if (self.is_note_visible(nNoteAbs, nTimeAbs) == False):
                continue # nothing else to do for this note since is not visible in remote GUI

            nNoteRel = self.note_idx_rel(nNoteAbs)         # C1 (36 -> 11), B1 (47 -> 0)
            nRow     = nNoteRel

            nTimeRel = self.note_time_rel(nTimeAbs)
            nBeat    = int(nTimeRel)                       # floor(nTimeAbs)
            nBit     = nTimeRel - float(nBeat)             # 0.0, 0.25, 0.5 or 0.75
            nCol     = nBit * self.m_nNumBitsInBeat        # 0,   1,    2   or 3

            nButton  = nRow * self.m_nNumBitsInBeat + nCol # button index in gui (from 0 to 47)

            # send a note message to the gui to confirm that the bit has been added
            sNoteAddress = '/seq/beat/bit/{0}'.format(nBeat)
            aNoteInfoMsgs.append([sNoteAddress, [nButton, 1.0]])
            self.m_aNoteOffMsgs.append([sNoteAddress, [nButton, 0.0]]) # to clean gui later

            # if this note is selected note index then send the velocity value to the gui
            if (nRow == self.sel_note_rel_idx()):
                sVelAddress = '/seq/beat/vel/{0}'.format(nBeat)
                aNoteInfoMsgs.append([sVelAddress, [nCol, nVel / 127.0]])
                self.m_aVelOffMsgs.append([sVelAddress, [nCol, 0.0]]) # to clean gui later

        sMsg = 'SeqBeatHandler, update_beat_grid_view, seq/beat'
        self.send_bundle(sMsg, aNoteInfoMsgs)


    def handle(self, _aMessage):
        # get the selected clip slot
        oClipSlot = self.sel_clip_slot()
        if (oClipSlot.has_clip == False):
            return # Empty clip slot, nothing else to do here!

        oClip = oClipSlot.clip
        if (oClip.is_midi_clip == False):
            return # Non-MIDI clip, nothing else to do here!

        sCmd  = self.m_aParts[0] # cmd: 'bit', 'vel'
        sBeat = self.m_aParts[1] # beat (string)
        nBeat = int(sBeat)       # beat column number (beat 0 -> 0, beat 1 -> 1, ...)

        # handle velocity commands
        if (self.m_aParts[0] == 'vel'):
            if (nBeat == 8):
                nVel = _aMessage[2] # velocity, a value between 0.0 and 1.0 (float)
                self.update_velocity(0, 0, nVel, self.gui_vis_beats())
                return # nothing else to do here

            nBit = _aMessage[2] # a value between 0 and 3 (number of bit in the beat)
            nVel = _aMessage[3] # velocity, a value between 0.0 and 1.0 (float)
            self.update_velocity(nBeat, nBit, nVel, self.m_nBitDuration)
            return # nothing else to do here

        # handle bit toggle on/off
        elif (self.m_aParts[0] == 'bit'):
            # read button index and status
            nButton    = _aMessage[2] # a value between 0 and 47 (number of the button)
            nButStatus = _aMessage[3] # 0 if beat is off and 1 if beat is on
            nButtonInt = int(nButton)

            # relative values
            nRow     = nButtonInt / self.m_nNumBitsInBeat # button row: 0 -> higher tone note, 11 -> lower tone note
            nCol     = nButtonInt % self.m_nNumBitsInBeat # button col: 0 -> first  beat bit ,  3 -> last  beat bit

            nNoteRel = nRow
            nTimeRel = float(nBeat) + (float(nCol) / float(self.m_nNumBitsInBeat))

            # absolute values
            nNoteAbs = self.note_idx_abs(nNoteRel)
            nTimeAbs = self.note_time_abs(nTimeRel)
            nLen     = self.m_nBitDuration
            nVel     = self.m_nDefaultVelocity

            #self.log('Beat: {0}, Button: {1}, Status: {2}, Note: {3}, Time: {4}'.format(nBeat, nButton, nButStatus, nNoteAbs, nTimeAbs))

            if (nButStatus < 0.5):
                # (from_time [double], from_pitch [int], time_span [double], pitch_span [int])
                oClip.remove_notes(nTimeAbs, nNoteAbs, nLen, 1)
                nVel = 0.0
            else:
                # (pitch [int], time [float], length [float], velocity [int], muted [boolean])
                aNotes = list([])
                aNotes.append([nNoteAbs, nTimeAbs, nLen, nVel, False])
                oClip.replace_selected_notes(tuple(aNotes))

            oClip.deselect_all_notes()

            sAddress = '/seq/beat/bit/{0}'.format(nBeat)
            self.send(sAddress, [nButton, nVel / self.m_nMaxVelocity])

            if (nRow == self.sel_note_rel_idx()):
                sVelAddress = '/seq/beat/vel/{0}'.format(nBeat)
                self.send(sVelAddress, [nCol, nVel])

            # if the note is getting on then save a message to turn it off later
            # if the note is getting off then remove the message from the list of note-off messages
            if (nVel > 0.0):
                self.add_note_off_msg([sAddress, [nButton, 0.0]], nRow, nCol, nBeat, nVel)
            else:
                self.del_note_off_msg(sAddress, nButton, nRow, nCol, nBeat)


    # _nBeat: a value between 0 and 7 (number of beats in a bar)
    # _nBit : a value between 0 and 3 (number of bits in a beat)
    def update_velocity(self, _nBeat, _nBit, _nVel, _nLen):

        # retrieve the note or notes
        nNoteRel = self.sel_note_rel_idx()
        nTimeRel = float(_nBeat) + (float(_nBit) / float(self.m_nNumBitsInBeat))

        nNoteAbs = self.note_idx_abs(nNoteRel)
        nTimeAbs = self.note_time_abs(nTimeRel)
        nSpan    = 1 # notes span

        oClip    = self.sel_clip_slot().clip
        aNotes   = oClip.get_notes(nTimeAbs, nNoteAbs, _nLen, nSpan)
        oClip.deselect_all_notes()

        # update value
        for oNote in aNotes:
            nNoteAbs = oNote[0] # Note value, between 0 and 127
            nTimeAbs = oNote[1] # Time
            nLen     = oNote[2] # Length
            bMute    = oNote[4] # Mute

            # oNote format: Note, Time, Length, Velocity, Mute
            nMaxVel = 127
            aNotes  = list([])
            aNotes.append([nNoteAbs, nTimeAbs, nLen, _nVel * nMaxVel, bMute])
            oClip.replace_selected_notes(tuple(aNotes))
            oClip.deselect_all_notes()

            # update remote GUI
            nTimeRel = self.note_time_rel(nTimeAbs)
            nBeat    = int(nTimeRel)                       # floor(nTimeAbs)
            nBit     = nTimeRel - float(nBeat)             # 0.0, 0.25, 0.5 or 0.75
            nCol     = nBit * self.m_nNumBitsInBeat        # 0,   1,    2   or 3
            sVelAddress = '/seq/beat/vel/%d' % (nBeat)
            self.send(sVelAddress, [nCol, _nVel])

        oClip.deselect_all_notes()


    def add_note_off_msg(self, _aNoteOffMsg, _nRow, _nCol, _nBeat, _nVel):
        self.log('> add note off msg: {0}, {1}'.format(_aNoteOffMsg[0], _aNoteOffMsg[1][0]))

        self.m_aNoteOffMsgs.append(_aNoteOffMsg)

        # if the note is in the selected index note then
        # add a velocity off message
        if (_nRow == self.sel_note_rel_idx()):
            sVelAddress = '/seq/beat/vel/{0}'.format(_nBeat)
            self.m_aVelOffMsgs.append([sVelAddress, [_nCol, 0.0]]) # to clean gui later


    def del_note_off_msg(self, _sAddress, _nButton, _nRow, _nCol, _nBeat):
        self.log('> del note off msg: {0}, {1}'.format(_sAddress, _nButton))

        # search the note off message index
        nIndex = 0
        for aNoteOffMsg in self.m_aNoteOffMsgs:
            if (aNoteOffMsg[0] == _sAddress and aNoteOffMsg[1][0] == _nButton):
                break;
            nIndex += 1

        if (nIndex < len(self.m_aNoteOffMsgs)):
            self.log('> note found at index: {0}'.format(nIndex))
            self.m_aNoteOffMsgs.pop(nIndex)

        # if the note is in the selected index note then
        # remove the velocity off message
        if (_nRow == self.sel_note_rel_idx()):
            sVelAddress = '/seq/beat/vel/{0}'.format(_nBeat)

            # search the velocity off message index
            nIndex = 0
            for aVelOffMsg in self.m_aVelOffMsgs:
                if (aVelOffMsg[0] == sVelAddress and aVelOffMsg[1][0] == _nCol):
                    break;
                nIndex += 1

            if (nIndex < len(self.m_aVelOffMsgs)):
                self.log('> vel found at index: {0}'.format(nIndex))
                self.m_aVelOffMsgs.pop(nIndex)


