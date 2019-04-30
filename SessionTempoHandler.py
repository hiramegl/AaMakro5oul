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
# Session Tempo commands handler
# ******************************************************************************

class SessionTempoHandler(BaseHandler):

    def __init__(self, _oCtrlInstance, _oOscServer, _hConfig):
        BaseHandler.__init__(self, _oCtrlInstance, _oOscServer, _hConfig)

        bIgnoreRelease = True
        bLogRxMsgs     = False
        self.config('/session/tempo', bIgnoreRelease, bLogRxMsgs)

        self.add_callbacks(['reset', 'minus', 'plus', 'div', 'mult'])


    def handle(self, _aMessages):
        if (self.m_sCmd == 'reset'):
            oClip = self.song().view.highlighted_clip_slot.clip
            try:
                oId3 = self.read_id3(oClip.file_path)
                if oId3.tag_exists():
                    for frame in oId3.frames:
                        if frame.fid == 'TBPM':
                            self.log('  => TBPM: {0}'.format(frame.strings[0]))
                            self.tempo(int(frame.strings[0]))
            except Exception as e:
                self.log('   => Could not read id3 tags for "{0}": {1}'.format(oClip.file_path, str(e)))
            return

        nValue = _aMessages[2]
        nTempo = self.tempo()

        if (self.m_sCmd == 'minus'):
            nTempo -= nValue

        elif (self.m_sCmd == 'plus'):
            nTempo += nValue

        elif (self.m_sCmd == 'div'):
            nTempo /= nValue

        elif (self.m_sCmd == 'mult'):
            nTempo *= nValue

        self.tempo(nTempo)


