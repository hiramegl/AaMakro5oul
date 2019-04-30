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

from BaseHandler import BaseHandler

# ******************************************************************************
# Core Handler: gives advanced control of Ableton Live features
# and keeps track of static variables shared by several modules
# ******************************************************************************

class CoreHandler(BaseHandler):

    # session state static variables
    m_nGuiTrackOffset = 0 # remote GUI track offset
    m_nGuiVisTracks   = 8 # remote GUI visible tracks in the screen
    m_nGuiSceneOffset = 0 # remove GUI scene offset
    m_nGuiVisScenes   = 8 # remove GUI visible scenes in the screen

    m_nGuiVisSends    = 8 # max num sends in remote GUI that we manage in session (tools modal) and sequence tabs
    m_nGuiVisReturns  = 8 # max num returns in remote GUI that we manage in session tab (tools modal)

    # beat sequence static variables
    m_nGuiVisBeats   = 8  # number of visible beats in beat grid
    m_nGuiVisNotes   = 12 # number of visible notes in beat grid
    m_nSeqOffset     = -1 # sequence offset for beat grid (in beats, time axis)
    m_nNoteOffset    = -1 # note offset for beat grid (idx abs, note axis)
    m_nSelNoteRelIdx = -1 # selected note index

    # track clip static variables (for build-ups and drop-downs)
    m_bNextSelectionOn = False
    m_aNextClips       = []

    m_aTrackIndeces = [str(i) for i in xrange(m_nGuiVisTracks)] + ['master', 'selected']
    m_aSceneIndeces = [str(i) for i in xrange(m_nGuiVisScenes)] + ['selected']
    m_aBeatsIndeces = [str(i) for i in xrange(m_nGuiVisBeats)]
    m_hBeats = {
        "3200": 32.0,
        "1600": 16.0,
        "0800": 8.0,
        "0400": 4.0,
        "0200": 2.0,
        "0100": 1.0,
        "0050": 0.5,
        "0025": 0.25,
        "0012": 0.125,
        "0006": 0.0625,
        "0003": 0.03125,
        "0001": 0.015625
    }

    # track selection for device control
    m_hDevTrackSel = {
        'a': ['none', -1],
        'b': ['none', -1],
        'c': ['none', -1],
        'd': ['none', -1]
    }
    m_nMaxTrackSels  = 8
    m_nMaxReturnSels = 8
    m_aChannels      = ['a', 'b', 'c', 'd']
    m_aChannelsFx    = ['a', 'b', 'c', 'd', 'x']

    # track selection for effects channel
    m_aFxTrackSel = ['none', -1]

    """
    Note-offset explanation diagram:

          Start Note C1 ---+         +--- Middle C
                           |         |
                           V         V                            | Button |
    Octave |-2   -1   0    1    2    3    4    5    6    7    8   |  row   | Off  Rel  Abs | Off  Rel  Abs | Off   Rel  Abs |
    Note   +------------------------------------------------------+--------+---------------+---------------+----------------+
     B     | 11  23   35   47   59   71   83   95   107 [119]     |   0    | 11 - 0 = 11   | 47 - 0  = 47  | 119 - 0 = 119  |
     A#    | 10  22   34   46   58   70   82   94   106  118      |   1    |               |               | ---       ---  |
     A     | 9   21   33   45   57   69   81   93   105  117      |   2    |               |               | Max       Max  |
     G#    | 8   20   32   44   56   68   80   92   104  116      |   3    |               |               | offset    val  |
     G     | 7   19   31   43   55   67   79   91   103  115  127 |   4    |               |               |                |
     F#    | 6   18   30   42   54   66   78   90   102  114  126 |   5    |               |               |                |
     F     | 5   17   29   41   53   65   77   89   101  113  125 |   6    |               |               |                |
     E     | 4   16   28   40   52   64   76   88   100  112  124 |   7    |               | [Octave 1]    |                |
     D#    | 3   15   27   39   51   63   75   87   99   111  123 |   8    | offset   val  | C1            |                |
     D     | 2   14   26   38   50   62   74   86   98   110  122 |   9    | Min      Min  | Default       |                |
     C#    | 1   13   25   37   49   61   73   85   97   109  121 |   10   | --       ---  | --        --  |                |
     C     |[0]  12   24  (36)  48  _60_  72   84   96   108  120 |   11   | 11 - 11 = 0   | 47 - 11 = 36  | 119 - 11 = 108 |
           +------------------------------------------------------+--------+---------------+---------------+----------------+
    """

    # constructor

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        BaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        # CONSTANTS
        self.m_nNumBeatsInBar = 4   # number of beats in a bar (4 for 4/4 notation)
        self.m_nNumBitsInBeat = 4   # number of bits in a beat (the divisions within a beat)
        self.m_nNumNotesInOct = 12  # number of notes per octave

        self.m_nDefNoteOffset = 47  # default note offset for Octave 1 (C1 note)
        self.m_nMinNoteOffset = 11  # minimum note offset
        self.m_nMaxNoteOffset = 119 # maximum note offset


    # beat note accessors ********************************************

    def gui_vis_beats(self, _nGuiVisBeats = -1):
        if (_nGuiVisBeats == -1):
            return CoreHandler.m_nGuiVisBeats
        CoreHandler.m_nGuiVisBeats = _nGuiVisBeats


    def seq_offset(self, _nSeqOffset = -1):
        if (_nSeqOffset == -1):
            return CoreHandler.m_nSeqOffset
        CoreHandler.m_nSeqOffset = _nSeqOffset


    def note_offset(self, _nNoteOffset = -1):
        if (_nNoteOffset == -1):
            return CoreHandler.m_nNoteOffset
        CoreHandler.m_nNoteOffset = _nNoteOffset


    # input:  value between 0 and 11
    # output: value between 0 and 119 (should be 127 in the future)
    def note_idx_abs(self, _nNoteIdxRel):
        return CoreHandler.m_nNoteOffset - _nNoteIdxRel


    # input:  value between 0 and 119 (should be 127 in the future)
    # output: value between 0 and 11
    def note_idx_rel(self, _nNoteIdxAbs):
        return CoreHandler.m_nNoteOffset - _nNoteIdxAbs


    def note_time_abs(self, _nNoteTimeRel):
        return _nNoteTimeRel + CoreHandler.m_nSeqOffset


    def note_time_rel(self, _nNoteTimeAbs):
        return _nNoteTimeAbs - CoreHandler.m_nSeqOffset


    # input:  value between 0 and 127
    def is_note_visible(self, _nNoteIdxAbs, _nNoteTimeAbs):
        nNoteIdxRel  = self.note_idx_rel(_nNoteIdxAbs)
        nNoteTimeRel = self.note_time_rel(_nNoteTimeAbs)
        return (nNoteIdxRel  >= 0 and nNoteIdxRel  < CoreHandler.m_nGuiVisNotes
            and nNoteTimeRel >= 0 and nNoteTimeRel < CoreHandler.m_nGuiVisBeats)


    def current_octave(self):
        return (CoreHandler.m_nNoteOffset / self.m_nNumNotesInOct) - 2 # MIDI Standard starts in octave -2


    # selected note, relative index: from 0 to 11
    def sel_note_rel_idx(self, _nSelNodeRelIdx = -1):
        if (_nSelNodeRelIdx == -1):
            return CoreHandler.m_nSelNoteRelIdx
        CoreHandler.m_nSelNoteRelIdx = _nSelNodeRelIdx


    # track and returns accessors ************************************

    def tracks(self):
        return self.song().visible_tracks


    def returns(self):
        return self.song().return_tracks


    def master(self):
        return self.song().master_track


    def tracks_and_returns(self):
        return tuple(self.tracks()) + tuple(self.returns())


    def get_track_or_return(self, _nTrackIdxAbs):
        aTracksAndReturns = self.tracks_and_returns()
        return aTracksAndReturns[_nTrackIdxAbs]


    def get_track(self, _nTrackIdxAbs):
        aTracks = self.tracks()
        return aTracks[_nTrackIdxAbs]


    def get_return(self, _nTrackIdxAbs):
        aReturns = self.returns()
        return aReturns[_nTrackIdxAbs]


    def sel_track(self, _oTrack = None):
        if (_oTrack != None):
            self.song().view.selected_track = _oTrack
        return self.song().view.selected_track


    def sel_track_idx_abs(self):
        aAllTracks = self.tracks_and_returns()
        oSelTrack  = self.sel_track()
        return list(aAllTracks).index(oSelTrack)


    def is_track_available(self, _nTrackIdxAbs):
        return (_nTrackIdxAbs < len(self.tracks()))


    def is_return_available(self, _nReturnIdxAbs):
        return (_nReturnIdxAbs < len(self.returns()))


    def is_return_track(self, _oTrack):
        return (_oTrack in self.returns())


    # only audio tracks (0 ... num audio tracks - 1)
    def tracks_range(self):
        return range(len(self.tracks()))


    # only return tracks (0 ... num return tracks - 1)
    def returns_range(self):
        return range(len(self.returns()))


    # both audio tracks and return tracks (0 ... num tracks + num returns - 1)
    def tracks_and_returns_range(self):
        return range(len(self.tracks_and_returns()))


    # scene accessors ************************************************

    def scenes(self):
        return self.song().scenes


    def get_scene(self, _nSceneIdxAbs):
        aAllScenes = self.scenes()
        return aAllScenes[_nSceneIdxAbs]


    def sel_scene(self, _oScene = None):
        if (_oScene != None):
            self.song().view.selected_scene = _oScene
        return self.song().view.selected_scene


    def sel_scene_idx_abs(self):
        aAllScenes = self.scenes()
        oSelScene  = self.sel_scene()
        return list(aAllScenes).index(oSelScene)


    def is_scene_available(self, _nSceneIdxAbs):
        return (_nSceneIdxAbs < len(self.scenes()))


    def available_scenes(self):
        return range(len(self.scenes()))


    # clip accessors *************************************************

    def sel_clip_slot(self):
        return self.song().view.highlighted_clip_slot


    def is_clip_available(self, _nTrackIdxAbs, _nSceneIdxAbs):
        return self.is_track_available(_nTrackIdxAbs) and self.is_scene_available(_nSceneIdxAbs)


    # next clips accessors *********************************

    def next_selection_on(self, _bNextSelectionOn = None):
        if (_bNextSelectionOn != None):
            CoreHandler.m_bNextSelectionOn = _bNextSelectionOn
        return CoreHandler.m_bNextSelectionOn


    def next_clips_add(self, _nTrackIdxAbs, _nSceneIdxAbs):
        CoreHandler.m_aNextClips.append([_nTrackIdxAbs, _nSceneIdxAbs])


    def next_clips_clear(self):
        CoreHandler.m_aNextClips = []


    def next_clips(self):
        return CoreHandler.m_aNextClips


    # gui track accessors **********************************

    def gui_track_offset(self, _nGuiTrackOffset = -1):
        if (_nGuiTrackOffset == -1):
            return CoreHandler.m_nGuiTrackOffset
        CoreHandler.m_nGuiTrackOffset = _nGuiTrackOffset


    def gui_num_tracks(self, _nGuiNumTracks = -1):
        if (_nGuiNumTracks == -1):
            return CoreHandler.m_nGuiVisTracks
        CoreHandler.m_nGuiVisTracks = _nGuiNumTracks


    def gui_visible_tracks_abs_range(self):
        return range(CoreHandler.m_nGuiTrackOffset, CoreHandler.m_nGuiTrackOffset + CoreHandler.m_nGuiVisTracks)


    def gui_visible_tracks_rel_range(self, _aExtra = None):
        aTracks = list(range(CoreHandler.m_nGuiVisTracks)) # using a list to be able to add _aExtra elements
        return aTracks if (_aExtra == None) else aTracks + _aExtra


    def track_idx_rel(self, _nTrackIdxAbs):
        return (_nTrackIdxAbs - CoreHandler.m_nGuiTrackOffset) % CoreHandler.m_nGuiVisTracks


    def track_idx_abs(self, _nTrackIdxRel):
        return _nTrackIdxRel + CoreHandler.m_nGuiTrackOffset


    def is_track_visible(self, _nTrackIdxAbs):
        nTrackIdxRel = _nTrackIdxAbs - CoreHandler.m_nGuiTrackOffset

        return (nTrackIdxRel >= 0
            and nTrackIdxRel < CoreHandler.m_nGuiVisTracks)


    # gui scene accessors **********************************

    def gui_scene_offset(self, _nGuiSceneOffset = -1):
        if (_nGuiSceneOffset == -1):
            return CoreHandler.m_nGuiSceneOffset
        CoreHandler.m_nGuiSceneOffset = _nGuiSceneOffset


    def gui_num_scenes(self, _nGuiNumScenes = -1):
        if (_nGuiNumScenes == -1):
            return CoreHandler.m_nGuiVisScenes
        CoreHandler.m_nGuiVisScenes = _nGuiNumScenes


    def gui_visible_scenes_abs_range(self):
        return range(CoreHandler.m_nGuiSceneOffset, CoreHandler.m_nGuiSceneOffset + CoreHandler.m_nGuiVisScenes)


    def gui_visible_scenes_rel_range(self, _aExtra = None):
        aScenes = list(range(CoreHandler.m_nGuiVisScenes)) # using a list to be able to add _aExtra elements
        return aScenes if (_aExtra == None) else aScenes + _aExtra


    def scene_idx_rel(self, _nSceneIdxAbs):
        return (_nSceneIdxAbs - CoreHandler.m_nGuiSceneOffset) % CoreHandler.m_nGuiVisScenes


    def scene_idx_abs(self, _nSceneIdxRel):
        return _nSceneIdxRel + CoreHandler.m_nGuiSceneOffset


    def is_scene_visible(self, _nSceneIdxAbs):
        nSceneIdxRel = _nSceneIdxAbs - CoreHandler.m_nGuiSceneOffset

        return (nSceneIdxRel >= 0
            and nSceneIdxRel < CoreHandler.m_nGuiVisScenes)


    # clip, sends and returns accessors ********************

    def is_clip_visible(self, _nTrackIdxAbs, _nSceneIdxAbs):
        nTrackIdxRel = _nTrackIdxAbs - CoreHandler.m_nGuiTrackOffset
        nSceneIdxRel = _nSceneIdxAbs - CoreHandler.m_nGuiSceneOffset

        return (nTrackIdxRel >= 0
            and nTrackIdxRel < CoreHandler.m_nGuiVisTracks
            and nSceneIdxRel >= 0
            and nSceneIdxRel < CoreHandler.m_nGuiVisScenes)


    def gui_num_vis_sends(self):
        return CoreHandler.m_nGuiVisSends


    def gui_vis_sends_range(self):
        return range(CoreHandler.m_nGuiVisSends)


    def gui_num_vis_returns(self):
        return CoreHandler.m_nGuiVisReturns


    def gui_vis_returns_range(self):
        return range(CoreHandler.m_nGuiVisReturns)


    # ******************************************************

    def track_indeces_list(self):
        return list(CoreHandler.m_aTrackIndeces)


    def scene_indeces_list(self):
        return list(CoreHandler.m_aSceneIndeces)


    def beats_indeces_list(self):
        return list(CoreHandler.m_aBeatsIndeces)


    def beats_list(self):
        return list(CoreHandler.m_hBeats.keys())


    def beat_value(self, _sBeat):
        return CoreHandler.m_hBeats.get(_sBeat, 0.0)


    # ******************************************************

    # selected track to handle device control events
    def sel_track_dev(self, _sChannel, _sTrackType = None, _nIdxAbs = -1):
        if (_nIdxAbs == -1):
            # check if is in remover mode
            if (_sTrackType == 'none'):
                CoreHandler.m_hDevTrackSel[_sChannel] = ['none', -1]

            # is in getter mode
            elif (_sTrackType == None):
                return CoreHandler.m_hDevTrackSel[_sChannel]

        # is in setter mode
        else:
            CoreHandler.m_hDevTrackSel[_sChannel] = [_sTrackType, _nIdxAbs]


    def max_track_sels(self):
        return CoreHandler.m_nMaxTrackSels


    def max_return_sels(self):
        return CoreHandler.m_nMaxReturnSels


    # ******************************************************

    def sel_track_fx(self, _sTrackType = None, _nIdxAbs = -1):
        if (_nIdxAbs == -1):
            # check if is in remover mode
            if (_sTrackType == 'none'):
                CoreHandler.m_aFxTrackSel = ['none', -1]

            # is in getter mode
            elif (_sTrackType == None):
                return CoreHandler.m_aFxTrackSel

        # is in setter mode
        else:
            CoreHandler.m_aFxTrackSel = [_sTrackType, _nIdxAbs]

    # ******************************************************

    def value_gui_to_param(self, _nGuiValue, _oParam):
        if (_oParam.is_quantized == True):
            # just copy the value for quantized params
            nParamValue = _nGuiValue

        else:
            # adjust the value in case is continuous (not discrete)
            nParamMin = _oParam.min
            nParamMax = _oParam.max
            nParamValue  = (_nGuiValue * (nParamMax - nParamMin)) + nParamMin

        return nParamValue # value between min and max


    def value_param_to_gui(self, _nParamValue, _oParam):
        if (_oParam.is_quantized == True):
            # just copy the value for quantized params
            nGuiValue = _nParamValue

        else:
            # adjust the value in case is continuous (not discrete)
            nParamMin = _oParam.min
            nParamMax = _oParam.max
            nGuiValue = (_nParamValue - nParamMin) / (nParamMax - nParamMin)

        return nGuiValue # value between 0 and 1


