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
# Session commands handler
# ******************************************************************************

class SessionCmdHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/session/cmd', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks(['reset','up','down','left','right', 'stop', 'arrange', 'toggle', 'pause', 'cueing','record','trackincr','sceneincr'])

        self.reset_session_increments()
        self.highlight_session()


    def disconnect(self):
        self.reset_session_increments()


    def reset_session_increments(self):
        self.m_nTrackIncr = 2 #self.gui_num_tracks()
        self.m_nSceneIncr = 4 #self.gui_num_scenes()
        self.send_msg('trackincr', self.m_nTrackIncr)
        self.send_msg('sceneincr', self.m_nSceneIncr)


    def handle(self, _aMessage):
        if (self.m_sCmd == 'trackincr'):
            self.m_nTrackIncr = int(_aMessage[2])
            self.log('> new track increment: %d' % (self.m_nTrackIncr))
            self.alert('> new track increment: %d' % (self.m_nTrackIncr))
            return # nothing else to do here

        elif (self.m_sCmd == 'sceneincr'):
            self.m_nSceneIncr = int(_aMessage[2])
            self.log('> new scene increment: %d' % (self.m_nSceneIncr))
            self.alert('> new scene increment: %d' % (self.m_nSceneIncr))
            return # nothing else to do here

        elif (self.m_sCmd == 'reset'):
            self.alert('Resetting %s' % (self.m_sProductName))
            # TrackClipHandler: update track clips
            # TrackCmdHandler : update track buttons
            # TrackVolHandler : update track volumes
            # SceneClipHandler: update scene launch buttons
            self.alert('> %s reset' % (self.m_sProductName))
            self.update_observers('session_reset')

        elif (self.m_sCmd == 'left'):
            if (self.gui_track_offset() - self.m_nTrackIncr >= 0):
                self.gui_track_offset(self.gui_track_offset() - self.m_nTrackIncr)
            else:
                self.gui_track_offset(0)
            self.highlight_session()
            # TrackClipHandler: update track clips
            # TrackCmdHandler : update track buttons
            # TrackVolHandler : update track volumes
            self.update_observers('new_tracks_sel')

        elif (self.m_sCmd == 'right'):
            if (self.gui_track_offset() + self.m_nTrackIncr < len(self.tracks())):
                self.gui_track_offset(self.gui_track_offset() + self.m_nTrackIncr)
                self.highlight_session()
                # TrackClipHandler: update track clips
                # TrackCmdHandler : update track buttons
                # TrackVolHandler : update track volumes
                self.update_observers('new_tracks_sel')

        elif (self.m_sCmd == 'up'):
            if (self.gui_scene_offset() - self.m_nSceneIncr >= 0):
                self.gui_scene_offset(self.gui_scene_offset() - self.m_nSceneIncr)
            else:
                self.gui_scene_offset(0)
            self.highlight_session()
            # SceneClipHandler: update scene launch buttons
            self.update_observers('new_scenes_sel')

        elif (self.m_sCmd == 'down'):
            if (self.gui_scene_offset() + self.m_nSceneIncr < len(self.scenes())):
                self.gui_scene_offset(self.gui_scene_offset() + self.m_nSceneIncr)
                self.highlight_session()
                # SceneClipHandler: update scene launch buttons
                self.update_observers('new_scenes_sel')

        elif (self.m_sCmd == 'stop'):
            self.song().stop_all_clips()
            self.song().stop_playing()
            self.alert('> %s stopping' % (self.m_sProductName))

        elif (self.m_sCmd == 'record'):
            bSessionRec                = self.song().session_record
            self.song().session_record = not bSessionRec

        elif (self.m_sCmd == 'pause'):
            return # handled by a ruby script

        elif (self.m_sCmd == 'arrange'):
            return # handled by a ruby script

        elif (self.m_sCmd == 'toggle'):
            return # handled by a ruby script

        elif (self.m_sCmd == 'cueing'):
            return # handled by a ruby script


    def highlight_session(self):
        bIncludeReturnTracks = False
        self.m_oCtrlInstance.set_session_highlight(self.gui_track_offset(), self.gui_scene_offset(), self.gui_num_tracks(), self.gui_num_scenes(), bIncludeReturnTracks)


    # Ableton Live events management *******************************************

    def add_listeners(self):
        self.remove_listeners()

        if (self.song().session_record_has_listener(self.on_session_record_change) != 1):
            self.song().add_session_record_listener(self.on_session_record_change)

    def on_session_record_change(self):
        bSessionRec  = self.song().session_record
        nRecord      = 1.0 if (bSessionRec) else 0.0

        self.send_msg('record', nRecord)


    def remove_listeners(self):
        if (self.song().session_record_has_listener(self.on_session_record_change) == 1):
            self.song().remove_session_record_listener(self.on_session_record_change)


