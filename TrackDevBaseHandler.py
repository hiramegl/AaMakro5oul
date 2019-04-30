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
# Track Device Base handler
# ******************************************************************************

class TrackDevBaseHandler(CoreHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        CoreHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        self.m_bIgnoreRelease  = False # Do not ignore relese events, we need to listen to toggle off messages
        self.m_bLogRxMsgs      = False # False -> do not log (fader messages overflow the log!), True for development
        self.m_bLogParamsVal   = False # log params possible values while creating the track device map, True for development
        self.m_hDevices        = { 'track': {}, 'return': {} }
        self.m_sDeviceClass    = 'DeviceClass'
        self.m_sDeviceNamePat  = None
        self.m_aCmds           = []
        self.m_sToggCmdPrm     = 'toggle/dev'
        self.m_sAutoCmdPrm     = 'fader/drywet'
        self.m_sAutoCmdTx      = 'fader/drywet'
        self.m_nAutoCmdMax     = None # max value
        self.m_nAutoCmdRst     = None # reset value
        self.m_nDevToggRst     = 1.0  # device toggle reset value
        self.m_nDefaultBars    = 24   # default bars delay for auto update
        self.m_sPresetsDir     = 'presets'
        self.m_sPresetsBase    = 'none'
        self.m_sRootId         = 'track_dev'
        self.m_hPresets        = {}

        self.config_device()

        self.m_aCmds.append('settings') # dummy listener, we will not manage it ever
        self.m_aCmds.append('auto/decr')
        self.m_aCmds.append('auto/incr')
        self.m_aCmds.append('select/bars')
        self.m_aCmds.append('select/preset')
        self.m_aCmds.append('toggle/avail')

        # register callbacks
        for sCmd in self.m_aCmds:
            self.add_callbacks_pref(sCmd, CoreHandler.m_aChannelsFx)

        self.clear_devices_controls()
        self.create_devices_map()
        self.update_devices_controls()
        self.load_presets()


    def config_device(self):
        pass # subclasses must override this method


    def disconnect(self):
        self.clear_devices_controls()


    def update(self, _sEvent, _hArgs = None):
        if (_sEvent == 'session_reset'):
            self.update_devices_controls()

        elif (_sEvent == 'device_values_clear'): # from TrackDevSelectHandler
            # used to clear the values of the device when the device
            # is re-selected in other channel than the current or when the user
            # wants to delete the current used channel
            sChannel = _hArgs['sChannel']
            self.log('> clear, device: %s, channel: %s' % (self.m_sDeviceClass, sChannel))
            self.clear_device_controls(sChannel)

        elif (_sEvent == 'device_values_clear_fx'): # from TrackDevSelectHandler
            # used to clear the values of the device when the user
            # wants to delete the current used fx channel
            self.log('> clear, device: %s, channel fx: x' % (self.m_sDeviceClass))
            self.clear_device_controls('x')

        elif (_sEvent == 'device_values_reset'): # from TrackDevSelectHandler
            # used for track reboot, we want to leave the values of the device
            # with their "default" value
            if ('sChannel' in _hArgs):
                sChannel = _hArgs['sChannel']
                self.log('> reset device: %s, channel: %s' % (self.m_sDeviceClass, sChannel))
                self.reset_device_controls_by_channel(sChannel)
            else:
                sTrackType = _hArgs['sTrackType']
                nIdxAbs    = _hArgs['nIdxAbs']
                self.log('> reset device: %s, type: %s, idx: %d' % (self.m_sDeviceClass, sTrackType, nIdxAbs))
                self.reset_device_controls_by_track(sTrackType, nIdxAbs)

        elif (_sEvent == 'device_values_reset_fx'): # from TrackDevSelectHandler
            # used when the user want to leave the values of the device
            # with their "default" value
            self.log('> reset device: %s, channel: x' % (self.m_sDeviceClass))
            self.reset_device_controls_by_channel_fx()

        elif (_sEvent == 'device_values_update'): # from TrackDevSelectHandler and TrackFxHandler
            sChannel   = _hArgs['sChannel']   # 'a', 'b', 'c' or 'd'
            sTrackType = _hArgs['sTrackType'] # 'track' or 'return'
            nIdxAbs    = _hArgs['nIdxAbs']    # absolut index

            self.log('> update, device: %s, channel: %s, track type: %s, idx abs: %d' % (self.m_sDeviceClass, sChannel, sTrackType, nIdxAbs))
            self.update_device_controls(sChannel, sTrackType, nIdxAbs)

        elif (_sEvent == 'device_values_update_fx'): # from TrackDevSelectHandler and TrackFxHandler
            sTrackType = _hArgs['sTrackType'] # 'track' or 'return'
            nIdxAbs    = _hArgs['nIdxAbs']    # absolut index

            self.log('> update, device fx: %s, channel: x, track type: %s, idx abs: %d' % (self.m_sDeviceClass, sTrackType, nIdxAbs))
            self.update_device_controls_fx(sTrackType, nIdxAbs)


    def clear_devices_controls(self):
        for sChannel in CoreHandler.m_aChannelsFx:
            self.clear_device_controls(sChannel)

        self.m_hAsyncAutoDevs  = {}    # async auto update devices hash
        self.m_bAsyncAutoOn    = False # async auto update on
        self.m_bAsyncUpdating  = False # flag used to prevent updating values while async auto update is on. Otherwise exceptions might occurr

        self.m_hBeatSchdDevs   = {}    # beat synced auto update schedule devices hash
        self.m_bBeatSchdOn     = False # beat synced auto update schedule on
        self.m_bBeatScheduling = False # flag used to prevent updating values while beat  scheduling update is on. Otherwise exceptions might occurr

        self.m_hProgSchdDevs   = {}    # async program scheduled devices hash
        self.m_bProgRunOn      = False # async program scheduled running
        self.m_bProgUpdating   = False # flag used to prevent updating values while beat  auto update is on. Otherwise exceptions might occurr

        self.m_nCount         = 0
        self.m_nMsgRate       = 5


    def clear_device_controls(self, _sChannel):
        aDevMsgs = []

        for sCmd in self.m_aCmds:
            self.append_idx_msg(sCmd, _sChannel, 0.0, aDevMsgs)
        self.clear_custom_gui_params(_sChannel, aDevMsgs)

        sMsg = 'TrackDevBaseHandler, [%s], clear_device_controls, track/dev/*, reset channel: %s' % (self.m_sDeviceClass, _sChannel)
        self.send_bundle(sMsg, aDevMsgs)


    # subclasses should override this method if necessary
    def clear_custom_gui_params(self, _sChannel, _aDevMsgs):
        pass


    def reset_device_controls_by_channel_fx(self):
        sChannel     = 'x'
        aTrackDevSel = self.sel_track_fx()
        sTrackType   = aTrackDevSel[0] # 'track' or 'return'
        nIdxAbs      = aTrackDevSel[1] # absolut index

        # check that there is actually a selected track in the specified channel
        if (sTrackType == 'none'):
            return # invalid track type, nothing else to do here!

        bHasDevice = (nIdxAbs in self.m_hDevices[sTrackType])

        # check that there is actually a device in the selected track
        if (bHasDevice == False):
            self.send_msg('toggle/avail/%s' % (sChannel), 0.0)
            self.log("> type: %s, abs idx: %d, has no '%s' device!" % (sTrackType, nIdxAbs, self.m_sDeviceClass))
            return # track has no device of this kind, nothing else to do here!

        self.send_msg('toggle/avail/%s' % (sChannel), 1.0)

        sDevKey = '%s-%d' % (sTrackType, nIdxAbs)
        hDevice = self.m_hDevices[sTrackType][nIdxAbs]

        # NO AUTOMATIZATION FOR FX CHANNEL!!!
        # stop automatization
        # self.m_bAsyncUpdating = True
        # if (sDevKey in self.m_hAsyncAutoDevs):
        #     self.log('> stopping auto updating and removing from hash of async auto update devices')
        #     del self.m_hAsyncAutoDevs[sDevKey]
        #     # turn autocmd toggle off
        #     self.send_msg('auto/%s/%s' % (hDevice['sAutoType'], hDevice['sChannel']), 0.0)
        # self.m_bAsyncUpdating = False

        # reset parameters to initial state (normally reset 'dry/wet' to 0.0)
        hParams = hDevice['hParams']
        self.reset_main_params(sChannel, hDevice, hParams)
        self.reset_custom_gui_params(sChannel, hDevice, hParams)

        # turn device on, we probably will use it later
        oToggParam       = hParams[self.m_sToggCmdPrm]
        oToggParam.value = self.m_nDevToggRst

        # reset the GUI control
        self.send_msg('%s/%s' % (self.m_sToggCmdPrm, sChannel), self.m_nDevToggRst)


    def reset_device_controls_by_channel(self, _sChannel):
        aTrackDevSel = self.sel_track_dev(_sChannel)
        sTrackType   = aTrackDevSel[0] # 'track' or 'return'
        nIdxAbs      = aTrackDevSel[1] # absolut index

        # check that there is actually a selected track in the specified channel
        if (sTrackType == 'none'):
            return # invalid track type, nothing else to do here!

        bHasDevice = (nIdxAbs in self.m_hDevices[sTrackType])

        # check that there is actually a device in the selected track
        if (bHasDevice == False):
            self.send_msg('toggle/avail/%s' % (_sChannel), 0.0)
            self.log("> type: %s, abs idx: %d, has no '%s' device!" % (sTrackType, nIdxAbs, self.m_sDeviceClass))
            return # track has no device of this kind, nothing else to do here!

        self.send_msg('toggle/avail/%s' % (_sChannel), 1.0)

        sDevKey = '%s-%d' % (sTrackType, nIdxAbs)
        hDevice = self.m_hDevices[sTrackType][nIdxAbs]

        # stop automatization
        self.m_bAsyncUpdating = True
        if (sDevKey in self.m_hAsyncAutoDevs):
            self.log('> stopping auto updating and removing from hash of async auto update devices')
            del self.m_hAsyncAutoDevs[sDevKey]
            # turn autocmd toggle off
            self.send_msg('auto/%s/%s' % (hDevice['sAutoType'], hDevice['sChannel']), 0.0)
        self.m_bAsyncUpdating = False

        # reset parameters to initial state (normally reset 'dry/wet' to 0.0)
        hParams = hDevice['hParams']
        self.reset_main_params(_sChannel, hDevice, hParams)
        self.reset_custom_gui_params(_sChannel, hDevice, hParams)

        # turn device on, we probably will use it later
        oToggParam       = hParams[self.m_sToggCmdPrm]
        oToggParam.value = self.m_nDevToggRst

        # reset the GUI control
        self.send_msg('%s/%s' % (self.m_sToggCmdPrm, _sChannel), self.m_nDevToggRst)


    def reset_device_controls_by_track(self, _sTrackType, _nIdxAbs):
        bHasDevice = (_nIdxAbs in self.m_hDevices[_sTrackType])

        # check that there is actually a device in the track
        if (bHasDevice == False):
            self.log("> type: %s, abs idx: %d, has no '%s' device!" % (_sTrackType, _nIdxAbs, self.m_sDeviceClass))
            return # track has no device of this kind, nothing else to do here!

        hDevice = self.m_hDevices[_sTrackType][_nIdxAbs]
        if ('sChannel' in hDevice):
            self.send_msg('toggle/avail/%s' % (hDevice['sChannel']), 1.0)
        if ('sChannelFx' in hDevice):
            self.send_msg('toggle/avail/%s' % (hDevice['sChannelFx']), 1.0)

        sDevKey = '%s-%d' % (_sTrackType, _nIdxAbs)

        # stop automatization
        self.m_bAsyncUpdating = True
        if (sDevKey in self.m_hAsyncAutoDevs):
            self.log('> stopping auto updating and removing from hash of async auto update devices')
            del self.m_hAsyncAutoDevs[sDevKey]
        self.m_bAsyncUpdating = False

        # reset parameters to initial state (normally reset 'dry/wet' to 0.0)
        hParams = hDevice['hParams']
        self.reset_main_params(None, hDevice, hParams)
        self.reset_custom_gui_params(None, hDevice, hParams)

        # turn device on, we probably will use it later
        oToggParam       = hParams[self.m_sToggCmdPrm]
        oToggParam.value = self.m_nDevToggRst


    # subclasses should override this method if necessary
    def reset_main_params(self, _sChannel, _hDevice, _hParams):
        # check what value should be used to reset the auto control
        nGuiValue = 0.0 if self.m_nAutoCmdRst == None else self.m_nAutoCmdRst

        # normally reset the 'fader/drywet' parameter
        oAutoParam       = _hParams[self.m_sAutoCmdPrm]
        oAutoParam.value = self.value_gui_to_param(nGuiValue, oAutoParam)

        # reset the GUI control (if necessary)
        if (_sChannel != None):
            self.send_msg('%s/%s' % (self.m_sAutoCmdTx, _sChannel), nGuiValue)


    # subclasses should override this method if necessary
    def reset_custom_gui_params(self, _sChannel, _hDevice, _hParams):
        pass


    def load_presets(self):
        # check if file exists
        sFileName = '%s_presets.txt' % (self.m_sPresetsBase)
        sFilePath = '%s/%s/%s' % (self.get_root_path(), self.m_sPresetsDir, sFileName)

        bFileExists = os.path.isfile(sFilePath)
        if (bFileExists == False):
            self.log('> presets file "%s" not found!' % (sFilePath))
            return # presets file does not exist, nothing else to do here!

        self.log('> reading: %s' % (sFilePath))
        # read presets file
        oFile = open(sFilePath, 'r')

        # parse preset lines
        for sLine in oFile:
            # ignore comment lines
            if (sLine[0] == '#'):
                continue

            aValues = sLine.split('|')
            aPreset = []

            # first value in line is the name of the preset
            sName = aValues[0].strip()
            self.log('> parsing preset: %s' % (sName))

            # parse the rest of values in the line
            for nIdx in range(1, len(aValues)):
                sCmd   = self.parse_preset_cmd(nIdx)
                oValue = self.parse_preset_val(nIdx, aValues[nIdx].strip())
                self.log('> parsing value: %s = %s' % (sCmd, aValues[nIdx].strip()))
                if (sCmd != None):
                    aPreset.append([sCmd, oValue])

            self.m_hPresets[sName] = aPreset
            self.log('> preset parsed: %s' % (sName))


    # subclasses should override this method
    def parse_preset_cmd(self, _nIdx):
        return 'none'


    # subclasses should override this method
    def parse_preset_val(self, _nIdx, sValue):
        return 0.0


    def apply_preset(self, _sTrackType, _nIdxAbs, _sPreset):
        self.log('> applying preset: %s, track: %s, idx: %d' % (_sPreset, _sTrackType, _nIdxAbs))

        hDevice = self.m_hDevices[_sTrackType][_nIdxAbs]
        hParams = hDevice['hParams']
        aPreset = self.m_hPresets[_sPreset]
        if ('sChannel' in hDevice):
            sChannel = hDevice['sChannel']
        else:
            sChannel = None

        self.log('> about to update %d params!' % (len(aPreset)))
        for aCmdValue in aPreset:
            sCmd    = aCmdValue[0]
            oValue  = aCmdValue[1]
            oParam  = hParams[sCmd]
            oPreset = self.get_preset_value(sCmd, oValue, oParam)
            self.log('> %s = %s (%s)' % (sCmd, str(oValue), str(oPreset)))

            # lets try to update the device parameter value
            try:
                oParam.value = oPreset

                # update the remote GUI with the new value
                nGuiValue = self.value_param_to_gui(oPreset, oParam)
                self.send_msg('%s/%s' % (sCmd, 'x'), nGuiValue)
                if (sChannel != None):
                    self.send_msg('%s/%s' % (sCmd, sChannel), nGuiValue)

            except Exception as e:
                self.log(">! could not update param '%s' with value %s: %s" % (sCmd, str(oPreset), str(e)))
                self.log(">! min: %s, max: %s" % (str(oParam.min), str(oParam.max)))
                if (oPreset > oParam.max):
                    oParam.value = oParam.max
                elif (oPreset < oParam.min):
                    oParam.value = oParam.min
                self.log(">! updating param '%s' with value %s" % (sCmd, str(oParam.value)))

                # update the remote GUI with the new value
                nGuiValue = self.value_param_to_gui(oParam.value, oParam)
                self.send_msg('%s/%s' % (sCmd, 'x'), nGuiValue)
                if (sChannel != None):
                    self.send_msg('%s/%s' % (sCmd, sChannel), nGuiValue)

    # subclasses should override this method
    def get_preset_value(self, _sCmd, _oValue, _oParam):
         return _oValue


    def value_preset_to_param_linear(self, _nValue, _nPresetMin, _nPresetMax, _nParamMin, _nParamMax):
        self.log('> %s, Preset (%s, %s), Param (%s, %s)' % (_nValue, str(_nPresetMin), str(_nPresetMax), str(_nParamMin), str(_nParamMax)))
        return _nParamMin + (_nValue - _nPresetMin) * (_nParamMax - _nParamMin) / (_nPresetMax - _nPresetMin)


    def create_devices_map(self):
        # m_hDevices:
        #    'track':
        #        <nTrackIdxAbs>: <- this is commonly referred as hDevice, since it contains all devices state variables
        #            'oDevice': <instance of a device>
        #            'hParams': <hash with params, key -> param cmd, value -> device param>
        #            'nBars'  : <number bars for automation>
        #    'return':
        #        <nTrackIdxAbs>: <- this is commonly referred as hDevice, since it contains all devices state variables
        #            'oDevice': <instance of a device>
        #            'hParams': <hash with params, key -> param cmd, value -> device param>
        #            'nBars'  : <number bars for automation>
        self.m_hDevices = { 'track': {}, 'return': {} }

        for nIdxAbs in self.tracks_range():
            if (self.is_track_available(nIdxAbs)):
                self.add_dev_to_map('track', nIdxAbs, self.get_track(nIdxAbs))

        for nIdxAbs in self.returns_range():
            if (self.is_return_available(nIdxAbs)):
                self.add_dev_to_map('return', nIdxAbs, self.get_return(nIdxAbs))


    def add_dev_to_map(self, _sTrackType, _nIdxAbs, _oTrack):
        sTrack   = self.to_ascii(_oTrack.name)
        aDevices = _oTrack.devices

        # try to find the device in the devices of this track
        for nDeviceIndex in range(len(aDevices)):
            oDevice  = aDevices[nDeviceIndex]
            aParams  = oDevice.parameters
            sDevice  = self.to_ascii(oDevice.name)
            sClass   = self.to_ascii(oDevice.class_name)
            sDisplay = self.to_ascii(oDevice.class_display_name)

            bMatch   = False
            if (self.m_sDeviceNamePat != None):
                bMatch = ((sClass == self.m_sDeviceClass) and (self.m_sDeviceNamePat in sDevice))
            else:
                bMatch = (sClass == self.m_sDeviceClass)

            if (bMatch or self.m_bLogParamsVal):
                self.log('> track: %s, device: %s, class: %s, display: %s' % (sTrack, sDevice, sClass, sDisplay))

            if (bMatch):
                hDevice = {
                    'oDevice': oDevice,
                    'hParams': {},
                    'nBars'  : self.m_nDefaultBars
                }
                self.m_hDevices[_sTrackType][_nIdxAbs] = hDevice

            if (bMatch or self.m_bLogParamsVal):
                for nParamIdx in range(len(aParams)):
                    oParam    = aParams[nParamIdx]
                    sParam    = self.to_ascii(oParam.name)
                    sOriginal = self.to_ascii(oParam.original_name)

                    if (bMatch):
                        self.register_param(_sTrackType, _nIdxAbs, sParam, sOriginal, oParam)

                    if (self.m_bLogParamsVal):
                        if (oParam.is_quantized):
                            for oValue in oParam.value_items:
                                lLog = (sParam, sOriginal, str(oParam.value), str(oValue))
                                self.log('>   param: %s, orig: %s, value: %s, item: %s' % lLog)
                        else:
                            lLog = (sParam, sOriginal, oParam.value, oParam.min, oParam.max)
                            self.log('>   param: %s, orig: %s, value: %f, min: %f, max: %f' % lLog)


    def register_param(self, _nIdxAbs, _sParam, _sOriginal, _oParam):
        pass # subclasses must override this method


    def update_devices_controls(self):
        for sChannel in CoreHandler.m_aChannels:
            aTrackDevSel = self.sel_track_dev(sChannel)
            self.update_device_controls(sChannel, aTrackDevSel[0], aTrackDevSel[1])

        aTrackFxSel = self.sel_track_fx()
        self.update_device_controls_fx(aTrackFxSel[0], aTrackFxSel[1])


    def update_device_controls(self, _sChannel, _sTrackType, _nIdxAbs):
        if (_sTrackType == 'none'):
            self.clear_device_controls(_sChannel)
            return # invalid track type, nothing else to do here

        bHasDevice = (_nIdxAbs in self.m_hDevices[_sTrackType])
        if (bHasDevice == False):
            self.send_msg('toggle/avail/%s' % (_sChannel), 0.0)
            return # the track has no device, nothing else to do here

        self.send_msg('toggle/avail/%s' % (_sChannel), 1.0)

        aDevMsgs = []
        hDevice  = self.m_hDevices[_sTrackType][_nIdxAbs]
        hParams  = hDevice['hParams']
        hDevice['sChannel'] = _sChannel
        self.add_param_messages(hParams, _sChannel, aDevMsgs)
        self.update_custom_params(hParams, _sChannel, aDevMsgs)
        self.append_idx_msg('select/bars', _sChannel, hDevice['nBars'], aDevMsgs)

        if (len(self.m_hPresets) > 0):
            aPresets = []
            aKeys = self.m_hPresets.keys()
            aKeys.sort()
            for sPreset in aKeys:
                aPresets.append('"%s":"%s"' % (sPreset, sPreset))
            sId    = '%s_select_preset_%s' % (self.m_sRootId, _sChannel)
            sAttrs = "{'values': {%s}}" % (','.join(aPresets))
            self.send('/EDIT', [sId, sAttrs])

        sMsg = 'TrackDevBaseHandler, [%s], update_device_controls, track/dev/*, update' % (self.m_sDeviceClass)
        self.send_bundle(sMsg, aDevMsgs)


    def update_device_controls_fx(self, _sTrackType, _nIdxAbs):
        sChannel = 'x'

        if (_sTrackType == 'none'):
            self.clear_device_controls(sChannel)
            return # invalid track type, nothing else to do here

        bHasDevice = (_nIdxAbs in self.m_hDevices[_sTrackType])
        if (bHasDevice == False):
            self.send_msg('toggle/avail/%s' % (sChannel), 0.0)
            return # the track has no device, nothing else to do here

        self.send_msg('toggle/avail/%s' % (sChannel), 1.0)

        aDevMsgs = []
        hDevice  = self.m_hDevices[_sTrackType][_nIdxAbs]
        hParams  = hDevice['hParams']
        hDevice['sChannelFx'] = sChannel
        self.add_param_messages(hParams, sChannel, aDevMsgs)
        self.update_custom_params(hParams, sChannel, aDevMsgs)

        # no automation for effects channel!
        #self.append_idx_msg('select/bars', _sChannel, hDevice['nBars'], aDevMsgs)

        if (len(self.m_hPresets) > 0):
            aPresets = []
            aKeys = self.m_hPresets.keys()
            aKeys.sort()
            for sPreset in aKeys:
                aPresets.append('"%s":"%s"' % (sPreset, sPreset))
            sId    = '%s_select_preset_%s' % (self.m_sRootId, sChannel)
            sAttrs = "{'values': {%s}}" % (','.join(aPresets))
            self.send('/EDIT', [sId, sAttrs])

        sMsg = 'TrackDevBaseHandler, [%s], update_device_controls_fx, track/dev/*, update' % (self.m_sDeviceClass)
        self.send_bundle(sMsg, aDevMsgs)


    def add_param_messages(self, _hParams, _sChannel, _aTrackMsgs):
        for sCmd in _hParams:
            oParam = _hParams[sCmd]

            if (oParam != None):
                nParamValue = oParam.value
                nGuiValue = self.value_param_to_gui(nParamValue, oParam)
                self.append_idx_msg(sCmd, _sChannel, nGuiValue, _aTrackMsgs)


    def update_custom_params(self, _hParams, _sChannel, _aTrackMsgs):
        pass # subclasses must override this method


    def handle(self, _aMessage):
        sCmd      = self.m_aParts[0] # 'toggle', 'fader', 'auto', ...
        sType     = self.m_aParts[1] # 'low', 'mid', 'hi', 'incr', 'decr', ...
        sChannel  = self.m_aParts[2] # 'a', 'b', 'c' or 'd'
        nGuiValue = _aMessage[2]     # param value in the GUI (from 0 to 1 for continuous values, i.e. faders)

        if (sChannel == 'x'):
            aTrackDevSel = self.sel_track_fx()
        else:
            aTrackDevSel = self.sel_track_dev(sChannel)

        sTrackType = aTrackDevSel[0]   # 'track' or 'return'
        nIdxAbs    = aTrackDevSel[1]   # absolut index
        bActive    = (nGuiValue > 0.5) # is the toggle active?

        # check that there is actually a selected track in the specified channel
        if (sTrackType == 'none'):
            self.send_msg('%s/%s/%s' % (sCmd, sType, sChannel), 0.0) # turn off toggle immediately since there is no track assigned to that channel
            self.log("> ERROR: Channel '%s' nas not been assigned any track yet!" % (sChannel))
            self.alert("> ERROR: Channel '%s' nas not been assigned any track yet!" % (sChannel))
            return # invalid track type, nothing else to do here!

        bHasDevice = (nIdxAbs in self.m_hDevices[sTrackType])

        # check that there is actually a device in the selected track
        if (bHasDevice == False):
            self.send_msg('%s/%s/%s' % (sCmd, sType, sChannel), 0.0) # turn off toggle immediately since there is no track assigned to that channel
            lLog = (sTrackType, nIdxAbs, self.m_sDeviceClass)
            self.log("> type: %s, abs idx: %d, has no '%s' device!" % lLog)
            self.alert("> Type: %s, abs idx: %d, has no '%s' device!" % lLog)
            return # track has no device of this kind, nothing else to do here!

        if (sCmd == 'toggle' and sType == 'avail'):
            self.send_msg('toggle/avail/%s' % (sChannel), 1.0)
            return

        if (sCmd == 'auto'):
            sDevKey = '%s-%d' % (sTrackType, nIdxAbs)
            self.log('> [%s] device auto fade: %s' % (self.m_sDeviceClass, sDevKey))

            self.m_bAsyncUpdating = True
            hDevice = self.m_hDevices[sTrackType][nIdxAbs]

            if (bActive == True):
                # the user is activating the automatic update!

                hDevice['sAutoType'] = sType

                # initialize end value for automatization and update incr/decr toggles
                if (sType == 'decr'):
                    hDevice['nValueEnd'] = 0.0
                    self.send_msg('auto/decr/%s' % (hDevice['sChannel']), 1.0)
                    self.send_msg('auto/incr/%s' % (hDevice['sChannel']), 0.0)

                elif (sType == 'incr'):
                    if (self.m_nAutoCmdMax != None):
                        hDevice['nValueEnd'] = self.m_nAutoCmdMax
                    else:
                        hDevice['nValueEnd'] = hDevice['hParams'][self.m_sAutoCmdPrm].max
                    self.send_msg('auto/decr/%s' % (hDevice['sChannel']), 0.0)
                    self.send_msg('auto/incr/%s' % (hDevice['sChannel']), 1.0)
                self.log('> device will fade to: %f' % (hDevice['nValueEnd']))

                self.m_hAsyncAutoDevs[sDevKey] = [sTrackType, nIdxAbs]
                self.compute_params(sTrackType, nIdxAbs)
                self.m_bAsyncAutoOn = True

            else:
                # the user is deactivating the automatic update!
                if (sDevKey in self.m_hAsyncAutoDevs):
                    self.log('> stopping auto updating and removing from hash of async auto update devices')
                    del self.m_hAsyncAutoDevs[sDevKey]
                    self.send_msg('auto/%s/%s' % (sType, hDevice['sChannel']), nGuiValue)

                else:
                    self.log('> device not found in hash! doing nothing!')
                    hDevice = self.m_hDevices[sTrackType][nIdxAbs]

            # check if is necessary to turn automatic control update off
            if (len(self.m_hAsyncAutoDevs) == 0):
                self.m_bAsyncAutoOn = False

            self.log('> auto: %d, num auto devs: %d' % (self.m_bAsyncAutoOn, len(self.m_hAsyncAutoDevs)))
            self.m_bAsyncUpdating = False

            return # nothing else to do here

        elif (sCmd == 'select' and sType == 'bars'):
            self.m_bAsyncUpdating = True
            self.m_hDevices[sTrackType][nIdxAbs]['nBars'] = nGuiValue
            self.log('> new bars for track type: %s, idx: %d, bars: %f' % (sTrackType, nIdxAbs, nGuiValue))
            self.compute_params(sTrackType, nIdxAbs)
            self.m_bAsyncUpdating = False

            return # nothing else to do here

        elif (sCmd == 'select' and sType == 'preset'):
            self.apply_preset(sTrackType, nIdxAbs, nGuiValue)
            return # nothing else to do here

        elif (sCmd == 'bprog'):
            self.m_bBeatScheduling = True

            sDevKey = '%s-%d' % (sTrackType, nIdxAbs)

            # check if there is already a beat program scheduled,
            # in such a case remove it since the user is canceling
            # the program
            if (sDevKey in self.m_hBeatSchdDevs):
                del self.m_hBeatSchdDevs[sDevKey]
                if (len(self.m_hBeatSchdDevs) == 0):
                    self.m_bBeatSchdOn = False

                lLog = (self.m_sDeviceClass, sDevKey, sType)
                self.log('> Program canceled [%s][%s] => type: %s' % lLog)
                self.alert('> Program canceled [%s][%s] => type: %s' % lLog)
                return # nothing else to do here

            (nFireProgTime, nFireProgBar, nFireProgBeat) = self.current_song_time_bar_beat()

            self.log('> [%s] BeatProg starting @ bar: %d, beat: %d' % (sDevKey, nFireProgBar, nFireProgBeat))
            hBeatSchdDev = {} # program event attributes
            hBeatSchdDev['hDevice']       = self.m_hDevices[sTrackType][nIdxAbs]
            hBeatSchdDev['sTrackType']    = sTrackType
            hBeatSchdDev['nIdxAbs']       = nIdxAbs
            hBeatSchdDev['sType']         = sType
            hBeatSchdDev['nFireProgTime'] = nFireProgTime
            hBeatSchdDev['nFireProgBar']  = nFireProgBar
            hBeatSchdDev['nFireProgBeat'] = nFireProgBeat
            self.m_hBeatSchdDevs[sDevKey] = hBeatSchdDev
            self.m_bBeatSchdOn = True

            sChannel = hBeatSchdDev['hDevice']['sChannel']
            self.send_msg('bprog/%s/%s' % (sType, sChannel), 1.0) # turn the toggle button on

            lLog = (self.m_sDeviceClass, sDevKey, sType, nFireProgTime, nFireProgBar, nFireProgBeat)
            self.log('> TrackDevBaseHandler, program fired [%s][%s] => type: %s, song time: %d, song bar: %d, song beat: %d' % lLog)
            self.alert('> Program fired [%s][%s] => type: %s, song time: %d, song bar: %d, song beat: %d' % lLog)

            self.m_bBeatScheduling = False

            return # nothing else to do here

        oParam = self.handle_param_msg(sChannel, sTrackType, nIdxAbs, sCmd, sType, nGuiValue, bActive)

        if (sCmd != 'fader'):
            sParam = self.to_ascii(oParam.name) if (oParam != None) else 'PARAM'
            lLog   = (self.m_sDeviceClass, sChannel, sTrackType, nIdxAbs, sCmd, sType, sParam, str(nGuiValue))
            self.log('> TrackDevBaseHandler, [%s], channel: %s, track type: %s, abs idx: %d, cmd: %s, type: %s, param: %s, value: %s' % lLog)


    # this method should be override by subclasses if necessary
    def handle_param_msg(self, _sChannel, _sTrackType, _nIdxAbs, _sCmd, _sType, _nGuiValue, _bActive):
        hParams = self.m_hDevices[_sTrackType][_nIdxAbs]['hParams']
        oParam  = hParams['%s/%s' % (_sCmd, _sType)]
        oParam.value = self.value_gui_to_param(_nGuiValue, oParam)

        return oParam


    def compute_params(self, _sTrackType, _nIdxAbs):
        hDevice      = self.m_hDevices[_sTrackType][_nIdxAbs]
        oParam       = hDevice['hParams'][self.m_sAutoCmdPrm]

        nBeatsInABar = 4.0
        nTempo       = self.song().tempo
        nTimeStart   = time.time()
        nTimeDelta   = 60.0 / nTempo * nBeatsInABar * hDevice['nBars']

        hDevice['nTimeStart']  = nTimeStart
        hDevice['nTimeEnd']    = nTimeStart + nTimeDelta
        hDevice['nValueStart'] = oParam.value
        nValueDelta            = hDevice['nValueEnd'] - hDevice['nValueStart']
        hDevice['nSlope']      = nValueDelta / nTimeDelta


    # this function is run approx every 100ms
    def update_prog_async_scheduled_tasks(self):
        if (self.m_bProgRunOn == False or self.m_bProgUpdating):
            return # nothing else to do here

        aDevsToDelete = []
        #self.log('> update_prog_async_scheduled_tasks: time: %f' % (time.time()))

        for sDevKey in self.m_hProgSchdDevs.keys():
            hProgSchdDev = self.m_hProgSchdDevs[sDevKey]
            hSchedule    = hProgSchdDev['hSchedule']

            bDone = False
            aStepsToRemove = []
            for sStepName in hSchedule.keys():
                aStep = hSchedule[sStepName]
                nExecTime = aStep[0]
                nExecIdx  = aStep[1]
                nTime     = time.time()

                if (nTime > nExecTime):
                    aStepsToRemove.append(sStepName)
                    self.log('> update_prog_async_scheduled_tasks: exec: nTime: %f, nExecTime: %f, nExecIdx: %d, step name: %s' % (nTime, nExecTime, nExecIdx, sStepName))
                    bDone = self.execute_beat_program_step(nExecIdx, sDevKey)

            # remove the steps from the schedule hash after iterating
            for sStepName in aStepsToRemove:
                if (sStepName in hSchedule):
                    del hSchedule[sStepName]

            if (bDone == True):
                aDevsToDelete.append(sDevKey)

        # remove the devices from the hash after iterating
        for sDevKey in aDevsToDelete:
            if (sDevKey in self.m_hProgSchdDevs):
                del self.m_hProgSchdDevs[sDevKey]

        # check if there is any device with a schedule in the hash, if empty then turn beat auto update off
        if (len(self.m_hProgSchdDevs) == 0):
            self.m_bProgRunOn = False


    def execute_beat_program_step(self, _nExecIdx, _sDevKey):
        pass # this method should be override by subclasses


    # this function is run approx every 100ms
    def update_async_scheduled_tasks(self):
        if (self.m_bAsyncAutoOn == False or self.m_bAsyncUpdating):
            return # nothing else to do here

        nTime = time.time()
        self.m_nCount += 1
        aDevsToDelete = []

        for sDevKey in self.m_hAsyncAutoDevs.keys():
            aDevAttrs  = self.m_hAsyncAutoDevs[sDevKey]
            sTrackType = aDevAttrs[0]
            nIdxAbs    = aDevAttrs[1]
            hDevice    = self.m_hDevices[sTrackType][nIdxAbs]

            # check if the time has already reached end time
            if (nTime > hDevice['nTimeEnd']):
                nNewValue = self.final_value_reached(sDevKey, hDevice, aDevsToDelete)
            else:
                # the time has not reached end time, compute the new param value
                nNewValue = hDevice['nValueStart'] + hDevice['nSlope'] * (nTime - hDevice['nTimeStart'])

            # check if the new param value has already reached end value
            if (hDevice['nSlope'] < 0):
                # for negative slope check if the value is less than the final value
                if (nNewValue < hDevice['nValueEnd']):
                    nNewValue = self.final_value_reached(sDevKey, hDevice, aDevsToDelete)
            else:
                # for positive slope check if the value is greater than the final value
                if (nNewValue > hDevice['nValueEnd']):
                    nNewValue = self.final_value_reached(sDevKey, hDevice, aDevsToDelete)

            oParam = hDevice['hParams'][self.m_sAutoCmdPrm]

            try:
                oParam.value = nNewValue
                nGuiValue    = self.value_param_to_gui(nNewValue, oParam)

                if (self.m_nCount % self.m_nMsgRate == 0):
                    self.send_msg('%s/%s' % (self.m_sAutoCmdTx, hDevice['sChannel']), nGuiValue)

            except Exception as e:
                self.log("   ====> Could not update param '%s' with value %f: %s" % (oParam.name, nNewValue, str(e)))

        # remove the devices from the hash after iterating
        for sDevKey in aDevsToDelete:
            if (sDevKey in self.m_hAsyncAutoDevs):
                del self.m_hAsyncAutoDevs[sDevKey]

        # check if there is any device to autocontrol, if empty then turn auto update off
        if (len(self.m_hAsyncAutoDevs) == 0):
            self.m_bAsyncAutoOn = False


    def final_value_reached(self, _sDevKey, _hDevice, _aDevsToDelete):
        nNewValue = _hDevice['nValueEnd']
        sChannel  = _hDevice['sChannel']
        self.send_msg('%s/%s' % (self.m_sAutoCmdTx, sChannel), nNewValue)
        self.send_msg('auto/decr/%s' % (sChannel), 0.0)
        self.send_msg('auto/incr/%s' % (sChannel), 0.0)
        _aDevsToDelete.append(_sDevKey)
        return nNewValue


    # this method is executed for every registered device and is actually not very accurate,
    # it will be invoked as soon as the beat changes but not exactly in the beat transition
    def schedule_beat_tasks(self, _nCurrSongTime, _nCurrSongBar, _nCurrSongBeat):
        if (self.m_bBeatSchdOn == False or self.m_bBeatScheduling):
            return # nothing else to do here

        aDevsToDelete = []
        nTempo        = self.song().tempo

        for sDevKey in self.m_hBeatSchdDevs.keys():
            bDone = self.schedule_beat_sync_task(sDevKey, nTempo, _nCurrSongTime, _nCurrSongBar, _nCurrSongBeat)

            if (bDone == True):
                aDevsToDelete.append(sDevKey)
                hBeatSchdDev = self.m_hBeatSchdDevs[sDevKey]
                sType        = hBeatSchdDev['sType']
                sChannel     = hBeatSchdDev['hDevice']['sChannel']
                self.send_msg('bprog/%s/%s' % (sType, sChannel), 0.0) # turn the toggle button off

        # remove the devices from the hash after iterating
        for sDevKey in aDevsToDelete:
            if (sDevKey in self.m_hBeatSchdDevs):
                del self.m_hBeatSchdDevs[sDevKey]

        # check if there is any device to autocontrol, if empty then turn auto update off
        if (len(self.m_hBeatSchdDevs) == 0):
            self.m_bBeatSchdOn = False


    # called when a beat occurs in ableton and the user has queued a beat program
    # NOTE! unfortunately we cannot make any change to the devices parameters in
    #       this callback method since Ableton Live refuses to change them. Therefore,
    #       we only schedule changes to be done and the parameters will actually change
    #       when calling 'update_prog_async_scheduled_tasks'
    def schedule_beat_sync_task(self, _sDevKey, _nTempo, _nCurrSongTime, _nCurrSongBar, _nCurrSongBeat):
        return True # this method should be override by subclasses


"""
hDevice = {
    'oDevice': oDevice,
    'hParams': {},
    'nBars'  : self.m_nDefaultBars
}
self.m_hDevices[_sTrackType][_nIdxAbs] = hDevice
hDevice['hParams'][sCmd] = oParam

hBeatSchdDev['hDevice']       = self.m_hDevices[sTrackType][nIdxAbs]
hBeatSchdDev['sTrackType']    = sTrackType
hBeatSchdDev['nIdxAbs']       = nIdxAbs
hBeatSchdDev['sType']         = sType
hBeatSchdDev['nFireProgTime'] = nFireProgTime
hBeatSchdDev['nFireProgBar']  = nFireProgBar
hBeatSchdDev['nFireProgBeat'] = nFireProgBeat

nBeatsInABar = 4.0
nTempo       = self.song().tempo
nTimeStart   = time.time()
nTimeDelta   = 60.0 / nTempo * nBeatsInABar * hDevice['nBars']

hDevice['sAutoType']   = 'incr' or 'decr'
hDevice['nTimeStart']  = nTimeStart
hDevice['nTimeEnd']    = nTimeStart + nTimeDelta
hDevice['nValueStart'] = oParam.value
nValueDelta            = hDevice['nValueEnd'] - hDevice['nValueStart']
hDevice['nSlope']      = nValueDelta / nTimeDelta

               nBeatDelta
             |<--------->|

Beat        Beat        Beat        Beat <=== schedule_beat_tasks() [depends on song tempo]
 |           |           |           |
 V           V           V           V
---------------X-------X-------X---X--------> execute_beat_program_step() [every component implements this]
   ^   ^   ^ : ^   ^   ^   ^   ^   ^
   |   |   | : |   |   |   |   |   |     <=== update_prog_async_scheduled_tasks() [~ every 100 ms]
             :
     ^       ^
     |       |                           <=== schedule_beat_sync_task() [every component implements this]
     |
     |                                   <=== async rx event that the user dispatches
"""


