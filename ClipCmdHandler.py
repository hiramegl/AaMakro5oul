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
# Clip commands handler
# ******************************************************************************

class ClipCmdHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/clip/cmd', bIgnoreRelease, bLogRxMsgs)
        self.add_callbacks(['left','right','up','down','fire','stop','follow','warp','duplicate','legato','seek','cut','copy','paste'])
        self.add_callbacks_pref('sel', ['left','right','up','down']) # managed by a ruby script

        self.update_audio_info() # not need to reset, just update audio info


    def disconnect(self):
        self.reset_audio_info()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'new_track_sel' or # TrackCmdHandler
            _sEvent == 'new_scene_sel'):  # SceneCmdHandler
            self.update_audio_info()


    def reset_audio_info(self):
        aAudioInfoMsgs = [
            ['/clip/info/artist', '-'],
            ['/clip/info/title' , '-'],
            ['/clip/info/bpm'   , '-'],
            ['/clip/info/key'   , '-'],
            ['/clip/info/genre' , '-'],
            ['/clip/info/length', '-'],
            ['/clip/cmd/seek'   , 0.0],
        ]
        sMsg = 'ClipCmdHandler, reset_audio_info, clip/info, reset'
        self.send_bundle(sMsg, aAudioInfoMsgs)


    def update_audio_info(self):
        # clear the audio info view
        aAudioInfoMsgs = [
            ['/clip/info/artist', '-'],
            ['/clip/info/title' , '-'],
            ['/clip/info/bpm'   , '-'],
            ['/clip/info/key'   , '-'],
            ['/clip/info/genre' , '-'],
            ['/clip/cmd/seek'   , 0.0],
        ]
        oSelTrack = self.sel_track()

        bReturn = False
        if (self.is_return_track(oSelTrack)):
            aAudioInfoMsgs.append(['/clip/info/latest/title', '-'])
            bReturn = True # is a return-track, return

        else:
            oClipSlot = self.sel_clip_slot()
            if (oClipSlot.has_clip == False):
                aAudioInfoMsgs.append(['/clip/info/latest/title', '-'])
                bReturn = True # empty clip slot, return
            else:
                oClip = oClipSlot.clip
                if (oClip.is_midi_clip == True):
                    sName = self.to_ascii(oClip.name)
                    aAudioInfoMsgs.append(['/clip/info/title', sName])
                    aAudioInfoMsgs.append(['/clip/info/latest/title', sName])
                    bReturn = True # midi clip, return

        if (bReturn == True):
            aAudioInfoMsgs.append(['/clip/info/length', '-'])
            sMsg = 'ClipCmdHandler, update_audio_info, clip/info, no_audio_track_info'
            self.send_bundle(sMsg, aAudioInfoMsgs)
            return # nothing else to do here!

        # if the highlighted clip is AUDIO then update the audio info ----------
        aAudioInfoMsgs.append(['/clip/info/length', oClip.length])

        # refresh latest title
        aAudioInfoMsgs.append(['/clip/info/latest/title', self.to_ascii(oClip.name)])

        try:
            oId3 = self.read_id3(oClip.file_path)
            if (oId3.tag_exists()):
                for frame in oId3.frames:
                    if (frame.fid == 'TPE1'):
                        aAudioInfoMsgs.append(['/clip/info/artist', frame.strings[0]])
                    elif (frame.fid == 'TIT2'):
                        aAudioInfoMsgs.append(['/clip/info/title' , frame.strings[0]])
                    elif (frame.fid == 'TBPM'):
                        aAudioInfoMsgs.append(['/clip/info/bpm'   , frame.strings[0]])
                    elif (frame.fid == 'TKEY'):
                        aAudioInfoMsgs.append(['/clip/info/key'   , frame.strings[0]])
                    elif (frame.fid == 'TCON'):
                        aAudioInfoMsgs.append(['/clip/info/genre' , frame.strings[0]])

        except Exception as e:
            self.log("   => Could not read id3 tags for '%s': %s" % (oClip.file_path, str(e)))

        sMsg = 'ClipCmdHandler, update_audio_info, clip/info, audio_track_info'
        self.send_bundle(sMsg, aAudioInfoMsgs)


    def log_info(self, _oClip):
        self.log('  => selected    : %s' % (_oClip.file_path))
        self.log('  => color       : %s' % (_oClip.color))
        self.log('  => color index : %s' % (_oClip.color_index))
        self.log('  => length      : %s' % (_oClip.length))
        self.log('  => name        : %s' % (_oClip.name))
        self.log('  => warp mode   : %s' % (_oClip.warp_mode))
        self.log('  => start lopp  : %s' % (_oClip.loop_start))
        self.log('  => end loop    : %s' % (_oClip.loop_end))
        self.log('  => start marker: %s' % (_oClip.start_marker))
        self.log('  => end marker  : %s' % (_oClip.end_marker))
        self.log('  => playing pos : %s' % (_oClip.playing_position))
        self.log('  => loop pos    : %s' % (_oClip.position))
        self.log('  => looping     : %s' % (_oClip.looping))


    def handle(self, _aMessage):
        aAllTracks      = self.tracks_and_returns()
        nSelTrackIdxAbs = self.sel_track_idx_abs()

        aAllScenes      = self.scenes()
        nSelSceneIdxAbs = self.sel_scene_idx_abs()

        if (self.m_sCmd == 'left'):
            if (nSelTrackIdxAbs > 0):
                self.sel_track(aAllTracks[nSelTrackIdxAbs - 1])
                self.update_clip_state(nSelTrackIdxAbs - 1, nSelSceneIdxAbs)

        elif (self.m_sCmd == 'right'):
            if (nSelTrackIdxAbs < len(aAllTracks) - 1):
                self.sel_track(aAllTracks[nSelTrackIdxAbs + 1])
                self.update_clip_state(nSelTrackIdxAbs + 1, nSelSceneIdxAbs)

        elif (self.m_sCmd == 'up'):
            if (nSelSceneIdxAbs > 0):
                self.sel_scene(aAllScenes[nSelSceneIdxAbs - 1])
                self.update_clip_state(nSelTrackIdxAbs, nSelSceneIdxAbs - 1)

        elif (self.m_sCmd == 'down'):
            if (nSelSceneIdxAbs < len(aAllScenes) - 1):
                self.sel_scene(aAllScenes[nSelSceneIdxAbs + 1])
                self.update_clip_state(nSelTrackIdxAbs, nSelSceneIdxAbs + 1)

        elif (self.m_sCmd == 'fire'):
            if (self.sel_clip_slot() != None):
                self.sel_clip_slot().fire()

        elif (self.m_sCmd == 'stop'):
            if (self.sel_clip_slot() != None):
                self.sel_clip_slot().stop()

        elif (self.m_sCmd == 'follow'):
            bFollow = self.song().view.follow_song
            self.song().view.follow_song = not bFollow

        elif (self.m_sCmd == 'warp'):
            bWarp = self.sel_clip_slot().clip.warping
            self.sel_clip_slot().clip.warping = not bWarp

        elif (self.m_sCmd == 'duplicate'):
            self.sel_track().duplicate_clip_slot(nSelSceneIdxAbs)
            # not necessary to send a message to update GUi since it is already
            # done with slot event listeners in TrackClipHandler

        elif (self.m_sCmd == 'seek'):
            nValue  = _aMessage[2]
            oClip   = self.sel_clip_slot().clip
            nLength = oClip.length
            nNewPos = nValue * nLength

            self.log('> Seeking: %f, length: %f, beat/time: %f' % (nValue, nLength, nNewPos))
            oClip.scrub(nNewPos)
            oClip.stop_scrub()

        # elif (self.m_sCmd == 'sel/*')
        # mark-select the contiguous clipslot
        # (actually managed by a ruby script)

        # elif (self.m_sCmd == 'cut | copy | paste')
        # cut or copy or paste
        # (actually managed by a ruby script)


        def update_clip_state(self, _nTrackIdxAbs, _nSceneIdxAbs):
            # TrackCmdHandler: update loop toggle button for track
            hArgs = { 'nTrackIdxAbs': _nTrackIdxAbs, 'nSceneIdxAbs': _nSceneIdxAbs }
            self.update_observers('clip_state_updated', hArgs)


