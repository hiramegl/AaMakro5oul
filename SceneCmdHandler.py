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
# Scene commands handler
# ******************************************************************************

class SceneCmdHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/scene/cmd', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks(['duplicate/selected'])
        self.add_callbacks_pref('fire', self.scene_indeces_list())

        self.m_hSceneListeners = {}

        # not necessary to reset scenes now, just update
        self.update_scenes()
        self.add_listeners()


    def disconnect(self):
        self.remove_listeners()
        self.reset_scenes()


    def update(self, _sEvent, _oArgs = None):
        if (_sEvent == 'new_scenes_sel' or # SessionCmdHandler
            _sEvent == 'session_reset'):   # SessionCmdHandler
            self.update_scenes()


    def reset_scenes(self):
        aSceneMsgs = []

        # iterate through the visible scenes in the GUI by using the relative indices (0, 1, 2, ...)
        for nSceneIdxRel in self.gui_visible_scenes_rel_range():
            sAttrs = '{"label": "^play %d", "css": "background-color: var(--color-raised)"}' % (nSceneIdxRel)
            aSceneMsgs.append(['/EDIT' , ['scene_cmd_fire_%d' % (nSceneIdxRel), sAttrs]])

        sMsg = 'SceneCmdHandler, reset_scenes, edit/scene/cmd/fire, reset_scenes'
        self.send_bundle(sMsg, aSceneMsgs)


    def update_scenes(self):
        aSceneMsgs = []

        # iterate through the visible scenes in GUI using the absolute indices
        for nSceneIdxAbs in self.gui_visible_scenes_abs_range():
            nSceneIdxRel = self.scene_idx_rel(nSceneIdxAbs)

            if (self.is_scene_available(nSceneIdxAbs)):
                oScene = self.get_scene(nSceneIdxAbs)
                sName  = self.to_ascii(oScene.name, 3)
                if (oScene.color == 0):
                    sColor = 'var(--color-raised)'
                else:
                    sColor = self.to_color(oScene.color)
                sAttrs = '{"label": "^play %s", "css": "background-color: %s"}' % (sName, sColor)

            else:
                sAttrs = '{"label": "-", "css": "background-color: var(--color-raised)"}'

            aSceneMsgs.append(['/EDIT', ['scene_cmd_fire_%d' % (nSceneIdxRel), sAttrs]])

        sMsg = 'SceneCmdHandler, update_scenes, edit/scene/cmd/fire, update_scenes'
        self.send_bundle(sMsg, aSceneMsgs)


    def handle(self, _aMessage):
        sCmd         = self.m_aParts[0]
        sSceneIdxRel = self.m_aParts[1]

        aAllScenes   = self.song().scenes

        # find out which scene is operated (selected, 0-7)
        if (sSceneIdxRel == 'selected'):
            oScene       = self.sel_scene()
            nSceneIdxAbs = self.sel_scene_idx_abs()

        else:
            nSceneIdxAbs = self.scene_idx_abs(int(sSceneIdxRel))
            if (self.is_scene_available(nSceneIdxAbs) == False):
                return # unavailable scene, nothing else to do here!
            oScene = self.get_scene(nSceneIdxAbs)

        sName = self.to_ascii(oScene.name)
        if (sCmd == 'fire'):
            oScene.fire()
            self.alert('> Playing scene %d: %s' % (nSceneIdxAbs + 1, sName))

        elif (sCmd == 'duplicate'):
            self.log('> Duplicating selected scene %d: %s' % (nSceneIdxAbs, sName))
            self.song().duplicate_scene(nSceneIdxAbs)


    # Ableton Live events management *******************************************

    def add_listeners(self):
        self.remove_listeners()

        if (self.song().scenes_has_listener(self.on_scenes_change) != 1):
            self.song().add_scenes_listener(self.on_scenes_change)
        if (self.song().view.selected_scene_has_listener(self.on_sel_scene_change) != 1):
            self.song().view.add_selected_scene_listener(self.on_sel_scene_change)

        for nSceneIdxAbs in self.available_scenes():
            oScene = self.get_scene(nSceneIdxAbs)
            self.add_scene_listeners(nSceneIdxAbs, oScene)


    def on_scenes_change(self):
        self.log('> SceneCmdHandler: scenes changed, updating listeners and GUI')
        self.add_listeners()
        self.update_scenes()

        # TrackClipHandler: reload track clips
        self.update_observers('scenes_changed')


    def on_sel_scene_change(self):
        # ClipCmdHandler: update selected clip info
        self.update_observers('new_scene_sel')


    def add_scene_listeners(self, _nSceneIdxAbs, _oScene):
        fViewCallback  = lambda :self.on_scene_view_changed(_oScene, _nSceneIdxAbs)

        if (self.m_hSceneListeners.has_key(_oScene) != 1):
            _oScene.add_name_listener(fViewCallback)
            _oScene.add_color_listener(fViewCallback)
            self.m_hSceneListeners[_oScene] = fViewCallback


    def on_scene_view_changed(self, _oScene, _nSceneIdxAbs):
        if (self.is_scene_visible(_nSceneIdxAbs)):
            nSceneIdxRel = self.scene_idx_rel(_nSceneIdxAbs)
            sName   = self.to_ascii(_oScene.name, 3)
            sColor  = self.to_color(_oScene.color)
            sAttrs  = '{"label": "^play %s", "css": "background-color: %s"}' % (sName, sColor)
            self.send('/EDIT', ['scene_cmd_fire_%d' % (nSceneIdxRel), sAttrs])


    def remove_listeners(self):
        if (self.song().scenes_has_listener(self.on_scenes_change)):
            self.song().remove_scenes_listener(self.on_scenes_change)
        if (self.song().view.selected_scene_has_listener(self.on_sel_scene_change)):
            self.song().view.remove_selected_scene_listener(self.on_sel_scene_change)

        for oScene in self.m_hSceneListeners:
            if (not oScene in self.m_hSceneListeners):
                continue # the key exists but the hash cannot recover the value!!!

            fViewCallback = self.m_hSceneListeners[oScene]

            if (oScene != None):
                if (oScene.name_has_listener(fViewCallback)):
                    oScene.remove_name_listener(fViewCallback)
                if (oScene.color_has_listener(fViewCallback)):
                    oScene.remove_color_listener(fViewCallback)

        self.m_hSceneListeners = {}


