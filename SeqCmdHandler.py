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
# Sequencer commands handler
# ******************************************************************************

class SeqCmdHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = False # False -> do not ignore release!
        bLogRxMsgs     = False
        self.config('/seq/cmd', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks(['left', 'right', 'up', 'down'])

        self.seq_offset(0) # reset sequence offset to the beggining
        self.update_beatgrid_label()


    def disconnect(self):
        self.reset_beatgrid_label()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'session_reset' or # from SessionCmdHandler
            _sEvent == 'new_track_sel' or # from TrackCmdHandler
            _sEvent == 'new_scene_sel'):  # from SceneCmdHandler
            self.update_beatgrid_label()
            self.seq_offset(0) # reset sequence offset to the beggining


    def reset_beatgrid_label(self):
        self.send_msg('beatgrid', '-:-')
        #self.seq_offset(0) # reset sequence offset to the beggining


    def update_beatgrid_label(self):
        oSelectedTrack = self.sel_track()
        if (oSelectedTrack.can_be_armed == False):
            self.reset_beatgrid_label()
            return # is a return-track, nothing else to do here

        oClipSlot = self.sel_clip_slot()
        if (oClipSlot.has_clip == False):
            self.reset_beatgrid_label()
            return # Empty clip slot, nothing else to do here

        oClip = oClipSlot.clip
        if (oClip.is_midi_clip == False):
            self.reset_beatgrid_label()
            return # Non-MIDI clip, nothing else to do here

        self.send_msg('beatgrid', '%d:%d' % (self.current_octave(), self.seq_offset()))


    def handle(self, _aMessage):
        oSelectedTrack = self.sel_track()
        if (oSelectedTrack.can_be_armed == False):
            return # is a return-track, nothing else to do here

        oClipSlot = self.sel_clip_slot()
        if (oClipSlot.has_clip == False):
            return # Empty clip slot, nothing else to do here

        oClip = oClipSlot.clip
        if (oClip.is_midi_clip == False):
            return # Non-MIDI clip, nothing else to do here

        if (self.m_sCmd == 'left'):
            nSeqOffset = self.seq_offset()
            if (nSeqOffset - self.gui_vis_beats() >= 0):
                self.seq_offset(nSeqOffset - self.gui_vis_beats())
            else:
                self.alert('> Min time reached: %f' % (nSeqOffset))
                return # nothing else to do here!

        elif (self.m_sCmd == 'right'):
            nClipLen     = int(oClip.length)
            nGuiVisBeats = self.gui_vis_beats()
            nSeqOffset   = self.seq_offset()

            # round the clip length to a multiple of gui_vis_beat (if necessary)
            nLength = (nClipLen / nGuiVisBeats) * nGuiVisBeats
            if (nClipLen % nGuiVisBeats != 0):
                nLength += nGuiVisBeats

            if (nSeqOffset + self.gui_vis_beats() < nLength):
                self.seq_offset(nSeqOffset + self.gui_vis_beats())
            else:
                self.alert('> Max length reached: %f' % (nLength))
                return # nothing else to do here!

        elif (self.m_sCmd == 'up'):
            nNoteOffset = self.note_offset()
            if (nNoteOffset + self.m_nNumNotesInOct <= self.m_nMaxNoteOffset):
                self.note_offset(nNoteOffset + self.m_nNumNotesInOct)
            else:
                self.alert('> Max octave reached: %d' % (self.current_octave()))
                return # nothing else to do here!

        elif (self.m_sCmd == 'down'):
            nNoteOffset = self.note_offset()
            if (nNoteOffset - self.m_nNumNotesInOct >= self.m_nMinNoteOffset):
                self.note_offset(nNoteOffset - self.m_nNumNotesInOct)
            else:
                self.alert('> Min octave reached: %d' % (self.current_octave()))
                return # nothing else to do here!

        # SeqBeatHandler: forward event to update notes and velocities
        self.update_observers('beatgrid_changed')
        self.alert('> Octave: %d, Time: %f' % (self.current_octave(), self.seq_offset()))
        self.update_beatgrid_label()


