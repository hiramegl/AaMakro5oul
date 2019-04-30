# Copyright (c) 2004, Alastair Tse
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are
# met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# Redistributions in binary form must reproduce the above copyright
# notice, this list of conditions and the following disclaimer in the
# documentation and/or other materials provided with the distribution.
#
# Neither the name of Alastair Tse nor the names of its
# contributors may be used to endorse or promote products derived from
# this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
# A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
# OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
# LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
# DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# __author__ = "Alastair Tse <alastair@tse.id.au>"
# __license = "BSD"
# __url__ = "http://www.liquidx.net/pytagger/"
# __version__ = "0.4"
# __copyright__ = "Copyright (c) 2005, Alastair Tse"

import os, struct, sys, types, tempfile, math

from encodings import normalize_encoding

# constants --------------------------------------

ID3_FILE_READ = 0
ID3_FILE_MODIFY = 1
ID3_FILE_NEW = 2

ID3V2_FILE_HEADER_LENGTH = 10
ID3V2_FILE_EXTHEADER_LENGTH = 5
ID3V2_FILE_FOOTER_LENGTH = 10
ID3V2_FILE_DEFAULT_PADDING = 512

ID3V2_DEFAULT_VERSION = '2.4'

ID3V2_FIELD_ENC_ISO8859_1 = 0
ID3V2_FIELD_ENC_UTF16 = 1
ID3V2_FIELD_ENC_UTF16BE = 2
ID3V2_FIELD_ENC_UTF8 = 3

# ID3v2 2.2 Variables

ID3V2_2_FRAME_HEADER_LENGTH = 6

ID3V2_2_TAG_HEADER_FLAGS = [('compression', 6),
                                                        ('unsync', 7)]

ID3V2_2_FRAME_SUPPORTED_IDS = {
        'UFI':('bin','Unique File Identifier'), # FIXME
        'BUF':('bin','Recommended buffer size'), # FIXME
        'CNT':('pcnt','Play counter'),
        'COM':('comm','Comments'),
        'CRA':('bin','Audio Encryption'), # FIXME
        'CRM':('bin','Encrypted meta frame'), # FIXME
        'EQU':('bin','Equalisation'), # FIXME
        'ETC':('bin','Event timing codes'),
        'GEO':('geob','General Encapsulated Object'),
        'IPL':('bin','Involved People List'), # null term list FIXME
        'LNK':('bin','Linked Information'), # FIXME
        'MCI':('bin','Music CD Identifier'), # FIXME
        'MLL':('bin','MPEG Location Lookup Table'), # FIXME
        'PIC':('apic','Attached Picture'),
        'POP':('bin','Popularimeter'), # FIXME
        'REV':('bin','Reverb'), # FIXME
        'RVA':('bin','Relative volume adjustment'), # FIXME
        'STC':('bin','Synced Tempo Codes'), # FIXME
        'SLT':('bin','Synced Lyrics/Text'), # FIXME
        'TAL':('text','Album/Movie/Show'),
        'TBP':('text','Beats per Minute'),
        'TCM':('text','Composer'),
        'TCO':('text','Content Type'),
        'TCR':('text','Copyright message'),
        'TDA':('text','Date'),
        'TDY':('text','Playlist delay (ms)'),
        'TEN':('text','Encoded by'),
        'TIM':('text','Time'),
        'TKE':('text','Initial key'),
        'TLA':('text','Language(s)'),
        'TLE':('text','Length'),
        'TMT':('text','Media Type'),
        'TP1':('text','Lead artist(s)/Lead performer(s)/Performing group'),
        'TP2':('text','Band/Orchestra/Accompaniment'),
        'TP3':('text','Conductor'),
        'TP4':('text','Interpreted, remixed by'),
        'TPA':('text','Part of a set'),
        'TPB':('text','Publisher'),
        'TOA':('text','Original artist(s)/performer(s)'),
        'TOF':('text','Original Filename'),
        'TOL':('text','Original Lyricist(s)/text writer(s)'),
        'TOR':('text','Original Release Year'),
        'TOT':('text','Original album/Movie/Show title'),
        'TRC':('text','International Standard Recording Code (ISRC'),
        'TRD':('text','Recording dates'),
        'TRK':('text','Track number/Position in set'),
        'TSI':('text','Size'),
        'TSS':('text','Software/hardware and settings used for encoding'),
        'TT1':('text','Content Group Description'),
        'TT2':('text','Title/Songname/Content Description'),
        'TT3':('text','Subtitle/Description refinement'),
        'TXT':('text','Lyricist(s)/Text Writer(s)'),
        'TYE':('text','Year'),
        'TXX':('wxxx','User defined text information'),
        'ULT':('bin','Unsynced Lyrics/Text'),
        'WAF':('url','Official audio file webpage'),
        'WAR':('url','Official artist/performer webpage'),
        'WAS':('url','Official audio source webpage'),
        'WCM':('url','Commercial information'),
        'WCP':('url','Copyright/Legal Information'),
        'WPM':('url','Official Publisher webpage'),
        'WXX':('wxxx','User defined URL link frame')
        }


ID3V2_2_FRAME_IMAGE_FORMAT_TO_MIME_TYPE = {
    'JPG':'image/jpeg',
    'PNG':'image/png',
    'GIF':'image/gif'
}

ID3V2_2_FRAME_MIME_TYPE_TO_IMAGE_FORMAT = {
    'image/jpeg':'JPG',
    'image/png':'PNG',
    'image/gif':'GIF'
}

# ID3v2 2.3 and above support

ID3V2_3_TAG_HEADER_FLAGS = [("ext", 6),
                                                        ("exp", 5),
                                                        ("footer", 4),
                                                        ("unsync", 7)]

ID3V2_3_FRAME_HEADER_LENGTH = 10
ID3V2_4_FRAME_HEADER_LENGTH = ID3V2_3_FRAME_HEADER_LENGTH

ID3V2_3_FRAME_TEXT_ID_TYPE = ['TIT1', 'TIT2', 'TIT3', 'TALB', 'TOAL', \
                                                          'TRCK', 'TPOS', 'TSST', 'TSRC']
ID3V2_3_FRAME_TEXT_PERSON_TYPE = ['TPE1', 'TPE2', 'TPE3', 'TPE4', 'TOPE', \
                                                                  'TEXT', 'TOLY', 'TCOM', 'TMCL', 'TIPL', \
                                                                  'TENC']
ID3V2_3_FRAME_TEXT_PROP_TYPE = ['TBPM', 'TLEN', 'TKEY', 'TLAN', 'TCON', \
                                                                'TFLT', 'TMED']
ID3V2_3_FRAME_TEXT_RIGHTS_TYPE = ['TCOP', 'TPRO', 'TPUB', 'TOWN', 'TRSN', \
                                                                  'TRSO']
ID3V2_3_FRAME_TEXT_OTHERS_TYPE = ['TOFN', 'TDLY', 'TDEN', 'TDOR', 'TDRC', \
                                                                  'TDRL', 'TDTG', 'TSSE', 'TSOA', 'TSOP', \
                                                                  'TSOT']
ID3V2_3_FRAME_IS_URL_TYPE = ['WCOM', 'WCOP', 'WOAF', 'WOAR', 'WOAS', \
                                                         'WORS', 'WPAY', 'WPUB']

ID3V2_3_FRAME_ONLY_FOR_2_3 = ['EQUA', 'IPLS', 'RVAD', 'TDAT', 'TIME', \
                                                          'TORY', 'TRDA', 'TSIZ', 'TYER']

ID3V2_4_FRAME_NEW_FOR_2_4 = ['ASPI', 'EQU2', 'RVA2', 'SEEK', 'SIGN', 'TDEN', \
                                                         'TDOR', 'TDRC', 'TDRL', 'TDTG', 'TIPL', 'TMCL', \
                                                         'TMOO', 'TPRO', 'TSOA', 'TSOP', 'TSOT', 'TSST']

ID3V2_3_FRAME_FLAGS = ['status', 'format', 'length', 'tagpreserve', \
                                           'filepreserve', 'readonly', 'groupinfo', \
                                           'compression', 'encryption', 'sync', 'datalength']

ID3V2_3_FRAME_STATUS_FLAGS = [('tagpreserve', 6),
                                                          ('filepreserve', 5),
                                                          ('readonly', 4)]

ID3V2_3_FRAME_FORMAT_FLAGS = [('groupinfo', 6),
                                                          ('compression', 3),
                                                          ('encryption', 2),
                                                          ('sync', 1),
                                                          ('datalength', 0)]

ID3V2_3_ABOVE_SUPPORTED_IDS = {
        'AENC':('bin','Audio Encryption'), # FIXME
        'APIC':('apic','Attached Picture'),
        'ASPI':('bin','Seek Point Index'), # FIXME
        'COMM':('comm','Comments'),
        'COMR':('bin','Commerical Frame'), # FIXME
        'EQU2':('bin','Equalisation'), # FIXME
        'ENCR':('bin','Encryption method registration'), # FIXME
        'ETCO':('bin','Event timing codes'), # FIXME
        'GEOB':('geob','General Encapsulated Object'),
        'GRID':('bin','Group ID Registration'), # FIXME
        'LINK':('bin','Linked Information'), # FIXME
        'MCDI':('bin','Music CD Identifier'),
        'MLLT':('bin','Location lookup table'), # FIXME
        'OWNE':('bin','Ownership frame'), # FIXME
        'PCNT':('pcnt','Play Counter'),
        'PRIV':('bin','Private frame'), # FIXME
        'POPM':('bin','Popularimeter'), # FIXME
        'POSS':('bin','Position Synchronisation frame'), # FIXME
        'RBUF':('bin','Recommended buffer size'), # FIXME
        'RVA2':('bin','Relative volume adjustment'), #FIXME
        'RVRB':('bin','Reverb'), # FIXME
        'SIGN':('bin','Signature'), # FIXME
        'SEEK':('pcnt','Seek'),
        'SYTC':('bin','Synchronised tempo codes'), # FIXME
        'SYLT':('bin','Synchronised lyrics/text'), # FIXME
        'TALB':('text','Album/Movie/Show Title'),
        'TBPM':('text','BPM'),
        'TCOM':('text','Composer'),
        'TCON':('text','Content type'),
        'TCOP':('text','Copyright'),
        'TDEN':('text','Encoding time'),
        'TDLY':('text','Playlist delay'),
        'TDOR':('text','Original release time'),
        'TDRC':('text','Recording time'),
        'TDRL':('text','Release time'),
        'TDTG':('text','Tagging time'),
        'TENC':('text','Encoded by'),
        'TEXT':('text','Lyricist/Text writer'),
        'TFLT':('text','File type'),
        'TIPL':('text','Musicians credits list'),
        'TIT1':('text','Content group description'),
        'TIT2':('text','Title/Songname/Content Description'),
        'TIT3':('text','Subtitle/Description refinement'),
        'TKEY':('text','Initial Key'),
        'TLAN':('text','Language'),
        'TLEN':('text','Length'),
        'TMCL':('text','Musician credits list'),
        'TMED':('text','Media type'),
        'TMOO':('text','Mood type'),
        'TOAL':('text','Original album/movie/show title'),
        'TOFN':('text','Original Filename'),
        'TOPE':('text','Original artist/performer'),
        'TOLY':('text','Original lyricist/text writer'),
        'TOWN':('text','File owner/licensee'),
        'TPE1':('text','Lead Performer(s)/Soloist(s)'),
        'TPE2':('text','Band/Orchestra Accompaniment'),
        'TPE3':('text','Conductor'),
        'TPE4':('text','Interpreted, remixed by'),
        'TPOS':('text','Part of a set'), # [0-9/]
        'TPRO':('text','Produced notice'),
        'TPUB':('text','Publisher'),
        'TRCK':('text','Track'), # [0-9/]
        'TRSN':('text','Internet radio station name'),
        'TRSO':('text','Internet radio station owner'),
        'TSOA':('text','Album sort order'),
        'TSOP':('text','Performer sort order'),
        'TSOT':('text','Title sort order'),
        'TSSE':('text','Software/Hardware and settings used for encoding'),
        'TSST':('text','Set subtitle'),
        'TSRC':('text','International Standard Recording Code (ISRC)'), # 12 chars
        'TXXX':('wxxx','User defined text'),
        'UFID':('bin','Unique File Identifier'), # FIXME
        'USER':('bin','Terms of use frame'), # FIXME (similar to comment)
        'USLT':('comm','Unsynchronised lyris/text transcription'),
        'WCOM':('url','Commercial Information URL'),
        'WCOP':('url','Copyright/Legal Information'),
        'WOAF':('url','Official audio file webpage'),
        'WOAR':('url','Official artist performance webpage'),
        'WOAS':('url','Official audio source webpage'),
        'WORS':('url','Official internet radio station homepage'),
        'WPAY':('url','Payment URL'),
        'WPUB':('url','Official publisher webpage'),
        'WXXX':('wxxx','User defined URL link frame'),
        # ID3v2.3 only tags
        'EQUA':('bin','Equalization'),
        'IPLS':('bin','Invovled people list'),
        'RVAD':('bin','Relative volume adjustment'),
        'TDAT':('text','Date'),
        'TIME':('text','Time'),
        'TORY':('text','Original Release Year'),
        'TRDA':('text','Recording date'),
        'TSIZ':('text','Size'),
        'TYER':('text','Year')
}

ID3V2_3_APIC_PICT_TYPES = {
    0x00: 'Other',
    0x01: '32x32 PNG Icon',
    0x02: 'Other Icon',
    0x03: 'Cover (Front)',
    0x04: 'Cover (Back)',
    0x05: 'Leaflet Page',
    0x06: 'Media',
    0x07: 'Lead Artist/Lead Performer/Soloist',
    0x08: 'Artist/Performer',
    0x09: 'Conductor',
    0x0a: 'Band/Orchestra',
    0x0b: 'Composer',
    0x0c: 'Lyricist/text writer',
    0x0d: 'Recording Location',
    0x0e: 'During Recording',
    0x0f: 'During Performance',
    0x10: 'Movie/Video Screen Capture',
    0x11: 'A bright coloured fish',
    0x12: 'Illustration',
    0x13: 'Band/artist logotype',
    0x14: 'Publisher/Studio logotype'
}

# debug ------------------------------------------

ID3V2_DEBUG = 0

def debug(args):
        if ID3V2_DEBUG > 1: print args
def warn(args):
        if ID3V2_DEBUG > 0: print args
def error(args):
        print args

# encoding ---------------------------------------

ID3V2_FIELD_ENC_LATIN_1 = 0
ID3V2_FIELD_ENC_UTF16 = 1
ID3V2_FIELD_ENC_UTF16BE = 2
ID3V2_FIELD_ENC_UTF8 = 3

encodings = {'latin_1':ID3V2_FIELD_ENC_LATIN_1,
                         'utf_16':ID3V2_FIELD_ENC_UTF16,
                         'utf_16_be':ID3V2_FIELD_ENC_UTF16BE,
                         'utf_8':ID3V2_FIELD_ENC_UTF8,
                         ID3V2_FIELD_ENC_LATIN_1:'latin_1',
                         ID3V2_FIELD_ENC_UTF16:'utf_16',
                         ID3V2_FIELD_ENC_UTF16BE:'utf_16_be',
                         ID3V2_FIELD_ENC_UTF8:'utf_8'}



ID3V2_DOUBLE_BYTE_ENCODINGS = ["utf_16", "utf_16_be"]
ID3V2_SINGLE_BYTE_ENCODINGS = ["latin_1", "utf_8"]
ID3V2_VALID_ENCODINGS = ["latin_1", "utf_16", "utf_16_be", "utf_8"]

# exceptions -------------------------------------

class ID3Exception(Exception):
        """General ID3Exception"""
        pass

class ID3EncodingException(ID3Exception):
        """Encoding Exception"""
        pass

class ID3VersionMismatchException(ID3Exception):
        """Version Mismatch problems"""
        pass

class ID3HeaderInvalidException(ID3Exception):
        """Header is malformed or none existant"""
        pass

class ID3ParameterException(ID3Exception):
        """Parameters are missing or malformed"""
        pass

class ID3FrameException(ID3Exception):
        """Frame is malformed or missing"""
        pass

class ID3NotImplementedException(ID3Exception):
        """This function isn't implemented"""
        pass
# utility ----------------------------------------

ID3V2_HEADER_LEN = {'2.2': ID3V2_2_FRAME_HEADER_LENGTH,
                                        '2.3': ID3V2_3_FRAME_HEADER_LENGTH,
                                        '2.4': ID3V2_3_FRAME_HEADER_LENGTH}

def id3v2_2_get_size(header):
        return struct.unpack('!I', '\x00' + header[3:6])[0]
def id3v2_3_get_size(header):
        return struct.unpack('!4sIBB', header)[1]

ID3V2_DATA_LEN = {'2.2': id3v2_2_get_size,
                                  '2.3': id3v2_3_get_size,
                                  '2.4': id3v2_3_get_size}

def syncsafe(num, size):
        """        Given a number, sync safe it """
        result = ''
        for i in range(0,size):
                x = (num >> (i*7)) & 0x7f
                result = chr(x) + result
        return result

def nosyncsafe(data):
        return struct.unpack('!I', data)[0]

def unsyncsafe(data):
        """
        Given a byte string, it will assume it is big-endian and un-SyncSafe
        a number
        """
        bytes = len(data)
        bs = struct.unpack("!%dB" % bytes, data)
        total = 0
        for i in range(0,bytes-1):
                total += bs[bytes-1-i] * pow(128,i)
        return total

def null_terminate(enc, s):
        """
        checks if a string is null terminated already, if it is, then ignore
        it, otherwise, terminate it properly.

        @param enc: encoding (idv2 valid ones: iso8859-1, utf-8, utf-16, utf-16be)
        @type enc: string

        @param s: string to properly null-terminate
        @type s: string
        """
        if is_double_byte(enc):
                if len(s) > 1 and s[-2:] == '\x00\x00':
                        return s
                else:
                        return s + '\x00\x00'
        elif is_valid_encoding(enc):
                if len(s) > 0 and s[-1] == '\x00':
                        return s
                else:
                        return s + '\x00'
        else:
                return s

def is_double_byte(enc):
        if normalize_encoding(enc) in ID3V2_DOUBLE_BYTE_ENCODINGS:
                return 1
        else:
                return 0

def is_valid_encoding(encoding):
        if normalize_encoding(encoding) in ID3V2_VALID_ENCODINGS:
                return 1
        else:
                return 0

def seek_to_sync(self, fd):
    """
    Reads the file object until it reaches a sync frame of an MP3 file
    (FIXME - inefficient, and possibly useless)
    """
    buf = ''
    hit = -1
    read = 0

    while hit == -1:
        # keep on reading until we have 3 chars in the buffer
        while len(buf) < 3:
            buf += fd.read(1)
            read += 1
        # do pattern matching for a 11 bit on pattern in the first 2 bytes
        # (note: that it may extend to the third byte)
        b0,b1,b2 = struct.unpack('!3B',buf)
        if (b0 & 0xff) and (b1 & 0xe0):
            hit = 0
        elif (b0 & 0x7f) and (b1 & 0xf0):
            hit = 1
        elif (b0 & 0x3f) and (b1 & 0xf8):
            hit = 2
        elif (b0 & 0x1f) and (b1 & 0xfc):
            hit = 3
        elif (b0 & 0x0f) and (b1 & 0xfe):
            hit = 4
        elif (b0 & 0x07) and (b1 & 0xff):
            hit = 5
        elif (b0 & 0x03) and (b1 & 0xff) and (b2 & 0x80):
            hit = 6
        elif (b0 & 0x01) and (b1 & 0xff) and (b2 & 0xc0):
            hit = 7
        else:
            buf = buf[1:]

    return read + 0.1 * hit - 3

# id3v2frame -------------------------------------

class ID3v2BaseFrame:
    """ Base ID3v2 Frame for 2.2, 2.3 and 2.4

    Abstract class that defines basic functions that are common for
    2.2, 2.3 and 2.4.

    o_* functions means output_*, they output a bytestring encoding
    the given data

    x_* functions means extract_*, they extract data into accessible
    structures when given a suitable length bytestream

    @cvar header_length: header portion length
    @cvar supported: supported frame ids
    @cvar status_flags: status flags required
    @cvar format_flags: format flags required

    @ivar fid: frame id code
    @ivar rawdata: rawdata of the rest of the frame minus the header
    @ivar length: length of the frame in bytes
    @ivar flags: dictionary of flags for this frame

    @ivar encoding: optional - for text fields we have the encoding name
    @ivar strings: a list of strings for text fields

    @ivar shortcomment: set if this frame is a comment
    @ivar longcomment: set if this frame is a comment (optional)
    @ivar language: set if this frame is a comment (2 character code)


    @ivar mimetype: mimetype for GEOB, APIC
    @ivar filename: filename for GEOB
    @ivar obj: data for GEOB
    @ivar desc: for geob and URL
    @ivar url: for URL

    @ivar counter: for playcount (PCNT)
    """
    supported = {}
    header_length = 0
    status_flags = {}
    format_flags = {}

    fid = None
    rawdata = None
    length = 0
    flags = 0
    encoding = ''
    strings = []
    shortcomment = ''
    longcomment = ''
    language = ''
    mimetype = ''
    filename = ''
    obj = None
    desc = ''
    url = ''

    def __init__(self, frame=None, fid=None):
        """
        creates an ID3v2BaseFrame structure. If you specify frame,
        then it will go into parse mode. If you specify the fid,
        then it will create a new frame.

        @param frame: frame bytestring
        @param fid: frame id for creating a new frame
        """

        if fid and not frame and fid not in self.supported.keys():
            raise ID3ParameterException("Unsupported ID3v2 Field: %s" % fid)
        elif fid and not frame:
            self.fid = fid
            self.new_frame_header()
        elif frame:
            self.parse_frame_header(frame)
            self.parse_field()

    def parse_frame_header(self, frame):

        """
        Parse the frame header from a bytestring

        @param frame: bytestring of the frame
        @type frame: string

        @todo: apple's id3 tags doesn't seem to follow the unsync safe format
        """
        self.rawdata = ''
        self.length = 0
        raise ID3NotImplementedException("parse_frame_header")

    def new_frame_header(self):
        """
        creates a new frame header
        """
        self.flags = {}
        for flagname, bit in self.status_flags + self.format_flags:
            self.flags[flagname] = 0

    def output(self):
        """
        Create a bytestring representing the frame contents
        and the field

        @todo: no syncsafing
        @todo: no status format flags used
        """
        raise ID3NotImplementedException("output")

    def parse_field(self):
        if self.fid not in self.supported.keys():
            raise ID3FrameException("Unsupported ID3v2 Field: %s" % self.fid)
        parser = self.supported[self.fid][0]
        eval('self.x_' + parser + '()')

    def output_field(self):
        if self.fid not in self.supported.keys():
            raise ID3FrameException("Unsupported ID3v2 Field: %s" % self.fid)
        parser = self.supported[self.fid][0]
        return eval('self.o_' + parser + '()')

    def o_string(self, s, toenc, fromenc='latin_1'):
        """
        Converts a String or Unicode String to a byte string of specified encoding.

        @param toenc: Encoding which we wish to convert to. This can be either ID3V2_FIELD_ENC_* or the actual python encoding type
        @param fromenc: converting from encoding specified
        """

        # sanitise input - convert to string repr
        try:
            if type(encodings[toenc]) == types.StringType:
                toenc = encodings[toenc]
        except KeyError:
            toenc = 'latin_1'

        outstring = ''

        # make sure string is of a type we understand
        if type(s) not in [types.StringType, types.UnicodeType]:
            s = unicode(s)

        if type(s) == types.StringType:
            if  toenc == fromenc:
                # don't need any conversion here
                outstring = s
            else:
                try:
                    outstring = s.decode(fromenc).encode(toenc)
                except (UnicodeEncodeError, UnicodeDecodeError):
                    warn("o_string: frame conversion failed. leaving as is.")
                    outstring = s

        elif type(s) == types.UnicodeType:
            try:
                outstring = s.encode(toenc)
            except UnicodeEncodeError, err:
                warn("o_string: frame conversion failed - leaving empty. %s" %\
                     err)
                outstring = ''

        return outstring


    def o_text(self):
        """
        Output text bytestring
        """
        newstrings = []
        for s in self.strings:
            newstrings.append(self.o_string(s, self.encoding))

        output = chr(encodings[self.encoding])
        for s in newstrings:
            output += null_terminate(self.encoding, s)

        """
        # strip the last null terminator
        if is_double_byte(self.encoding) and len(output) > 1:
            output = output[:-2]
        elif not is_double_byte(self.encoding) and len(output) > 0:
            output = output[:-1]
        """

        return output

    def x_text(self):
        """
        Extract Text Fields

        @todo: handle multiple strings seperated by \x00

        sets: encoding, strings
        """
        data = self.rawdata
        self.encoding = encodings[ord(data[0])]
        rawtext = data[1:]

        if normalize_encoding(self.encoding) == 'latin_1':
            text = rawtext
            self.strings = text.split('\x00')
        else:
            text = rawtext.decode(self.encoding)
            if is_double_byte(self.encoding):
                self.strings = text.split('\x00\x00')
            else:
                self.strings = text.split('\x00')

        try:
            dummy = text.encode('utf_8')
            debug('Read Field: %s Len: %d Enc: %s Text: %s' %
                   (self.fid, self.length, self.encoding, str([text])))
        except UnicodeDecodeError:
            debug('Read Field: %s Len: %d Enc: %s Text: %s (Err)' %
                   (self.fid, self.length, self.encoding, str([text])))

    def set_text(self, s, encoding = 'utf_16'):
        self.strings = [s]
        self.encoding = encoding

    def o_comm(self):
        if is_double_byte(self.encoding):
            sep = '\x00\x00'
        else:
            sep = '\x00'

        return chr(encodings[self.encoding]) + self.language + \
               self.o_string(self.shortcomment, self.encoding) + sep + \
               self.o_string(self.longcomment, self.encoding) + sep

    def x_comm(self):
        """
        extract comment field

        sets: encoding, lang, shortcomment, longcomment
        """
        data = self.rawdata
        self.encoding = encodings[ord(data[0])]
        self.language = data[1:4]
        self.shortcomment = ''
        self.longcomment = ''

        if is_double_byte(self.encoding):
            for i in range(4,len(data)-1):
                if data[i:i+2] == '\x00\x00':
                    self.shortcomment = data[4:i].strip('\x00')
                    self.longcomment = data[i+2:].strip('\x00')
                    break
        else:
            for i in range(4,len(data)):
                if data[i] == '\x00':
                    self.shortcomment = data[4:i].strip('\x00')
                    self.longcomment = data[i+1:].strip('\x00')
                    break

        debug('Read Field: %s Len: %d Enc: %s Lang: %s Comm: %s' %
              (self.fid, self.length, self.encoding, self.language,
               str([self.shortcomment, self.longcomment])))


    def o_pcnt(self):
        counter = ''
        if self.length == 4:
            counter = struct.pack('!I', self.counter)
        else:
            for i in range(0, self.length):
                x = (self.counter >> (i*8) ) & 0xff
                counter = counter + struct.pack('!B',x)
        return counter

    def x_pcnt(self):
        """
        Extract Play Count

        sets: counter
        """
        data = self.rawdata
        bytes = self.length
        counter = 0
        if bytes == 4:
            counter = struct.unpack('!I',data)[0]
        else:
            for i in range(0,bytes):
                counter += struct.unpack('B',data[i]) * pow(256,i)

        debug('Read Field: %s Len: %d Count: %d' % (self.fid, bytes, counter))
        self.counter = counter

    def o_bin(self):
        return self.rawdata

    def x_bin(self):
        pass

    def o_wxxx(self):
        if is_double_byte(self.encoding):
            return chr(encodings[self.encoding]) + \
                   self.o_string(self.desc, self.encoding) + '\x00\x00' + \
                   self.o_string(self.url, self.encoding) + '\x00\x00'
        else:
            return chr(encodings[self.encoding]) + \
                   self.o_string(self.desc, self.encoding) + '\x00' + \
                   self.o_string(self.url, self.encoding) + '\x00'

    def x_wxxx(self):
        """
        Extract URL

        set: encoding, desc, url
        """
        data = self.rawdata
        self.encoding = encodings[ord(data[0])]
        if is_double_byte(self.encoding):
            for i in range(1,len(data)-1):
                if data[i:i+2] == '\x00\x00':
                    self.desc = data[1:i]
                    self.url = data[i+2:]
                    break
        else:
            for i in range(1,len(data)):
                if data[i] == '\x00':
                    self.desc = data[1:i]
                    self.url = data[i+1:]
                    break

        debug("Read field: %s Len: %s Enc: %s Desc: %s URL: %s" %
               (self.fid, self.length, self.encoding,
                self.desc, str([self.url])))

    def o_apic(self):
        enc = encodings[self.encoding]
        sep = '\x00'
        if is_double_byte(self.encoding):
            sep = '\x00\x00'
        return '%c%s\x00%c%s%s%s' % (enc, self.mimetype, self.picttype,
                                     self.o_string(self.desc, self.encoding),
                                     sep, self.pict)

    def x_apic(self):
        """
        Extract APIC

        set: encoding, mimetype, desc, pict, picttype
        """
        data = self.rawdata
        self.encoding = encodings[ord(data[0])]
        self.mimetype = ''
        self.desc = ''
        self.pict = ''
        self.picttype = 0

        # get mime type (must be latin-1)
        for i in range(1,len(data)):
            if data[i] == '\x00':
                self.mimetype = data[1:i]
                break

        if not self.mimetype:
            raise ID3FrameException("APIC extraction failed. Missing mimetype")

        picttype = ord(data[len(self.mimetype) + 2])

        # get picture description
        for i in range(len(self.mimetype) + 2, len(data)-1):
            if data[i] == '\x00':
                self.desc = data[len(self.mimetype)+2:i]
                if data[i+1] == '\x00':
                    self.pict = data[i+2:]
                else:
                    self.pict = data[i+1:]
                break

        debug('Read Field: %s Len: %d PicType: %d Mime: %s Desc: %s PicLen: %d' %
               (self.fid, self.length, self.picttype, self.mimetype,
                self.desc, len(self.pict)))

        # open("test.png","w").write(pictdata)

    def o_url(self):
        return self.rawdata

    def x_url(self):
        debug("Read Field: %s Len: %d Data: %s" %
               (self.fid, self.length, [self.rawdata]))
        return

    def o_geob(self):
        if is_double_byte(self.encoding):
            return chr(encodings[self.encoding]) + self.mimetype + '\x00' + \
                   self.filename + '\x00\x00' + self.desc + \
                   '\x00\x00' + self.obj
        else:
            return chr(encodings[self.encoding]) + self.mimetype + '\x00' + \
                   self.filename + '\x00' + self.desc + \
                   '\x00' + self.obj

    def x_geob(self):
        """
        Extract GEOB

        set: encoding, mimetype, filename, desc, obj
        """
        data = self.rawdata
        self.encoding = encodings[ord(data[0])]
        self.mimetype = ''
        self.filename = ''
        self.desc = ''
        self.obj = ''

        for i in range(1,len(data)):
            if data[i] == '\x00':
                self.mimetype = data[1:i]
                break

        if not self.mimetype:
            raise ID3FrameException("Unable to extract GEOB. Missing mimetype")

        # FIXME: because filename and desc are optional, we should be
        #        smarter about splitting
        if is_double_byte(self.encoding):
            for i in range(len(self.mimetype)+2,len(data)-1):
                if data[i:i+2] == '\x00\x00':
                    self.filename = data[len(self.mimetype)+2:i]
                    ptr = len(self.mimetype) + len(self.filename) + 4
                    break
        else:
            for i in range(len(self.mimetype)+2,len(data)-1):
                if data[i] == '\x00':
                    self.filename = data[len(self.mimetype)+2:i]
                    ptr = len(self.mimetype) + len(self.filename) + 3
                    break

        if is_double_byte(self.encoding):
            for i in range(ptr,len(data)-1):
                if data[i:i+2] == '\x00\x00':
                    self.desc = data[ptr:i]
                    self.obj = data[i+2:]
                    break
        else:
            for i in range(ptr,len(data)-1):
                if data[i] == '\x00':
                    self.desc = data[ptr:i]
                    self.obj = data[i+1:]
                    break

        debug("Read Field: %s Len: %d Enc: %s Mime: %s Filename: %s Desc: %s ObjLen: %d" %
               (self.fid, self.length, self.encoding, self.mimetype,
                self.filename, self.desc, len(self.obj)))


class ID3v2_2_Frame(ID3v2BaseFrame):
    supported = ID3V2_2_FRAME_SUPPORTED_IDS
    header_length = ID3V2_2_FRAME_HEADER_LENGTH
    version = '2.2'
    status_flags = []
    format_flags = []

    def parse_frame_header(self, frame):
        header = frame[:self.header_length]

        self.fid = header[0:3]
        self.rawdata = frame[self.header_length:]
        self.length = struct.unpack('!I', '\x00' + header[3:6])[0]

    def output(self):
        fieldstr = self.output_field()
        # FIXME: no syncsafe
        # NOTE: ID3v2 uses only 3 bytes for size, so we strip of MSB
        header = self.fid + struct.pack('!I', len(fieldstr))[1:]
        return header + fieldstr

    def o_text(self):
        """
        Output Text Field

        ID3v2.2 text fields do not support multiple fields
        """
        newstring = self.o_string(self.strings[0], self.encoding)
        enc = encodings[self.encoding]
        return chr(enc) + null_terminate(self.encoding, newstring)

    def o_apic(self):
        enc = encodings[self.encoding]
        if is_double_byte(self.encoding):
            sep = '\x00\x00'
        else:
            sep = '\x00'

        imgtype = self.mimetype
        if len(imgtype) != 3:
            #attempt conversion
            if imgtype in ID3V2_2_FRAME_MIME_TYPE_TO_IMAGE_FORMAT.keys():
                imgtype = ID3V2_2_FRAME_MIME_TYPE_TO_IMAGE_FORMAT[imgtype]
            else:
                raise ID3FrameException("ID3v2.2 picture format must be three characters")

        return '%c%s%c%s%s%s' % (enc, imgtype, self.picttype,
                                 self.o_string(self.desc, self.encoding),
                                 sep, self.pict)

    def x_apic(self):
        """
        Extract APIC

        set: encoding, mimetype, desc, pict, picttype
        """
        data = self.rawdata
        self.encoding = encodings[ord(data[0])]
        self.mimetype = ''
        self.desc = ''
        self.pict = ''
        self.picttype = 0

        # get mime type (must be latin-1)
        imgtype = data[1:4]
        if not imgtype:
            raise ID3FrameException("APIC extraction failed. Missing mimetype")

        if imgtype not in ID3V2_2_FRAME_IMAGE_FORMAT_TO_MIME_TYPE.keys():
            raise ID3FrameException("Unrecognised mime-type")
        else:
            self.mimetype = ID3V2_2_FRAME_IMAGE_FORMAT_TO_MIME_TYPE[imgtype]

        picttype = ord(data[len(imgtype) + 1])

        # get picture description
        for i in range(len(imgtype) + 2, len(data) - 1):
            print [data[i:i+3]]
            if data[i] == '\x00':
                self.desc = data[len(imgtype)+2:i]
                if data[i+1] == '\x00':
                    self.pict = data[i+2:]
                else:
                    self.pict = data[i+1:]
                break

        debug('Read Field: %s Len: %d PicType: %d Mime: %s Desc: %s PicLen: %d' %
               (self.fid, self.length, self.picttype, self.mimetype,
                self.desc, len(self.pict)))

        # open("test.png","w").write(pictdata)

class ID3v2_3_Frame(ID3v2BaseFrame):
    supported = ID3V2_3_ABOVE_SUPPORTED_IDS
    header_length = ID3V2_3_FRAME_HEADER_LENGTH
    status_flags = ID3V2_3_FRAME_STATUS_FLAGS
    format_flags = ID3V2_3_FRAME_FORMAT_FLAGS
    version = '2.3'

    def parse_frame_header(self, frame):

        frame_header = frame[:self.header_length]

        (fid, rawsize, status, format) = struct.unpack("!4sIBB", frame_header)

        self.fid = fid
        self.rawdata = frame[self.header_length:]
        self.length = rawsize
        self.flags = {}

        for flagname, bit in self.status_flags:
            self.flags[flagname] = (status >> bit) & 0x01

        for flagname, bit in self.format_flags:
            self.flags[flagname] = (format >> bit) & 0x01

    def output(self):
        fieldstr = self.output_field()
        header = self.fid + struct.pack('!IBB', len(fieldstr), \
                                        self.getstatus(), \
                                        self.getformat())
        return header + fieldstr

    def getstatus(self):
        status_word = 0
        if self.flags and self.status_flags:
            for flag, bit in self.status_flags:
                if self.flags.has_key(flag):
                    status_word = status_word & (0x01 << bit)
        return status_word


    def getformat(self):
        format_word = 0
        if self.flags and self.format_flags:
            for flag, bit in self.format_flags:
                if self.flags.has_key(flag):
                    format_word = format_word & (0x01 << bit)
        return format_word


class ID3v2_4_Frame(ID3v2_3_Frame):
    supported = ID3V2_3_ABOVE_SUPPORTED_IDS
    header_length = ID3V2_3_FRAME_HEADER_LENGTH
    flags = ID3V2_3_FRAME_FLAGS
    version = '2.4'


ID3v2Frame = ID3v2_4_Frame

# id3v1 ------------------------------------------

class ID3v1(object):
    """
    ID3v1 Class

    This class parses and writes ID3v1 tags using a very simplified
    interface.

    You can access the ID3v1 tag variables by directly accessing the
    object attributes. For example:

    id3v1 = ID3v1('some.mp3')
    id3v1.track = 1
    print id3v1.songname
    del id3v1

    @ivar songname: the songname in iso8859-1
    @type songname: string
    @ivar artist: the artist name in iso8859-1
    @type artist: string
    @ivar album: the album name in iso8859-1
    @type album: string
    @ivar year: the year of the track
    @type year: string
    @ivar comment: comment string. limited to 28 characters
    @type comment: string
    @ivar genre: genre number
    @type genre: int
    @ivar track: track number
    @type track: int


    @ivar read_only: file is read only
    """

    __f = None
    __tag = None
    __filename = None

    def __init__(self, filename):
        """
        constructor

        tries to load the id3v1 data from the filename given. if it succeeds it
        will set the tag_exists parameter.

        @param filename: filename
        @type filename: string
        @param mode: ID3_FILE_{NEW,READ,MODIFY}
        @type mode: constant
        """

        if not os.path.exists(filename):
            raise ID3ParameterException("File not found: %s" % filename)

        try:
            self.__f = open(filename, 'rb+')
            self.read_only = False
        except IOError, (errno, strerr):
            if errno == 13: # permission denied
                self.__f = open(filename, 'rb')
                self.read_only = True
            else:
                raise

        self.__filename = filename
        self.__tag = self.default_tags()

        if self.tag_exists():
            self.parse()

    def default_tags(self):
        return { 'songname':'', 'artist':'', 'album':'',
                 'year':'', 'comment':'', 'genre':0, 'track':0}

    def tag_exists(self):
        self.__f.seek(-128, 2)
        if self.__f.read(3) == 'TAG':
            return True
        return False

    def remove_and_commit(self):
        """ Remove ID3v1 Tag """
        if self.tag_exists() and not self.read_only:
            self.__f.seek(-128, 2)
            self.__f.truncate()
            self.__f.flush()
            self.__tag = self.default_tags()
            return True
        else:
            return False

    def commit(self):
        id3v1 = struct.pack("!3s30s30s30s4s30sb",
            'TAG',
            self.songname,
            self.artist,
            self.album,
            self.year,
            self.comment,
            self.genre)

        if self.tag_exists():
            self.__f.seek(-128, 2)
            self.__f.truncate()
        else:
            self.__f.seek(0, 2)

        self.__f.write(id3v1)
        self.__f.flush()

    def commit_to_file(self, filename):
        id3v1 = struct.pack("!3s30s30s30s4s30sb",
            'TAG',
            self.songname,
            self.artist,
            self.album,
            self.year,
            self.comment,
            self.genre)

        f = open(filename, 'wb+')
        self.__f.seek(0)
        buf = self.__f.read(4096)
        while buf:
            f.write(buf)
            buf = self.__f.read(4096)

        if self.tag_exists():
            f.seek(-128, 0)
            f.truncate()

        f.write(id3v1)
        f.close()


    def __getattr__(self, name):
        if self.__tag and self.__tag.has_key(name):
            return self.__tag[name]
        else:
            raise AttributeError, "%s not found" % name

    def __setattr__(self, name, value):
        if self.__tag and self.__tag.has_key(name):
            if name == 'genre' and type(value) != types.IntValue:
                raise TypeError, "genre should be an integer"
            if name == 'track' and type(value) != types.IntValue:
                raise TypeError, "track should be an integer"
            if name == 'year':
                self.__tag[name] = str(value)[:4]
            self.__tag[name] = value
        else:
            object.__setattr__(self, name, value)

    def __del__(self):
        if self.__f:
            self.__f.close()

    def parse(self):
        try:
            self.__f.seek(-128, 2)
        except IOError:
            raise ID3HeaderInvalidException("not enough bytes")

        id3v1 = self.__f.read(128)

        tag, songname, artist, album, year, comment, genre = \
             struct.unpack("!3s30s30s30s4s30sb", id3v1)

        if tag != "TAG":
            raise ID3HeaderInvalidException("ID3v1 TAG not found")
        else:
            if comment[28] == '\x00':
                track = ord(comment[29])
                comment = comment[0:27]
            else:
                track = 0


            self.__tag["songname"] = self.unpad(songname).strip()
            self.__tag["artist"] = self.unpad(artist).strip()
            self.__tag["album"] = self.unpad(album).strip()
            self.__tag["year"] = self.unpad(year).strip()
            self.__tag["comment"] = self.unpad(comment).strip()
            self.__tag["genre"] = genre
            self.__tag["track"] = track

    def unpad(self, field):
        length = 0
        for x in field:
            if x == '\x00':
                break
            else:
                length += 1
        return field[:length]

# id3v2 ------------------------------------------

class ID3v2:
    """
    ID3v2 Tag Parser/Writer for MP3 files

    @cvar supported: list of version that this parser supports
    @ivar tag: dictionary of parameters that the tag has
    @type tag: dictionary

    @note: tag has the following options

    size = size of the whole header, excluding header and footer
    ext = has extension header (2.3, 2.4 only)
    exp = is experimental (2.4, 2.3 only)
    footer = has footer (2.3, 2.4 only)
    compression = has compression enabled (2.2 only)
    unsync = uses unsynchronise method of encoding data

    @ivar frames: list of frames that is in the tag
    @type frames: dictionary of ID3v2*Frame(s)

    @ivar version: version this tag supports
    @type version: float (2.2, 2.3, 2.4)

    @todo: parse/write footers
    @todo: parse/write appended tags
    @todo: parse/write ext header

    """
    f = None
    supported = ('2.2', '2.3', '2.4')

    # ---------------------------------------------------------
    def __init__(self, filename, version=ID3V2_DEFAULT_VERSION):
        """
        @param filename: the file to open or write to.
        @type filename: string

        @param version: if header doesn't exists, we need this to tell us what version \
                        header to use
        @type version: float

        @raise ID3Exception: if file does not have an ID3v2 but is specified
        to be in read or modify mode.
        """

        if str(version) not in self.supported:
            raise ID3ParameterException("version %s not valid" % str(version))

        if not os.path.exists(filename):
            raise ID3ParameterException("filename %s not valid" % filename)

        try:
          self.f = open(filename, 'rb+')
          self.read_only = False
        except IOError, (errno, strerror):
            if errno == 13: # permission denied
                self.f = open(filename, 'rb')
                self.read_only = True

        self.filename = filename

        if self.tag_exists():
            self.parse_header()
            self.parse_frames()
        else:
            self.new_header(str(version))

    def __del__(self):
        if self.f:
            self.f.close()

    # ---------------------------------------------------------
    # query functions
    # ---------------------------------------------------------

    def mp3_data_offset(self):
        """ How many bytes into the file does MP3 data start? """
        if not self.tag_exists():
            return 0
        else:
            if str(self.version) in ('2.2', '2.3', '2.4'):
                if self.tag["footer"]:
                    return ID3V2_FILE_HEADER_LENGTH + \
                           ID3V2_FILE_FOOTER_LENGTH + \
                           self.tag["size"]
            return ID3V2_FILE_HEADER_LENGTH + self.tag["size"]

    # ---------------------------------------------------------
    def tag_exists(self):
        self.f.seek(0)
        if self.f.read(3) == 'ID3':
            return True
        return False

    # ---------------------------------------------------------
    def dump_header(self):
        """
        Debugging purposes, dump the whole header of the file.

        @todo: dump footer and extension header as well
        """
        old_pos = self.f.tell()
        output = ''
        if self.tag["size"]:
            self.f.seek(0)
            output = self.f.read(ID3V2_FILE_HEADER_LENGTH + self.tag["size"])
            self.f.seek(old_pos)

        return output


    # ---------------------------------------------------------
    def new_frame(self, fid=None, frame=None):
        """
        Return a new frame of the correct type for this tag

        @param fid: frame id
        @param frame: bytes in the frame
        """
        if self.version == '2.2':
            return ID3v2_2_Frame(frame=frame, fid=fid)
        elif self.version == '2.3':
            return ID3v2_3_Frame(frame=frame, fid=fid)
        elif self.version == '2.4':
            return ID3v2_4_Frame(frame=frame, fid=fid)
        else:
            raise ID3NotImplemented("version %s not supported." % self.version)

    # ---------------------------------------------------------
    def set_version(self, version):
        self.version = str(version)

    # ---------------------------------------------------------
    def _read_null_bytes(self):
        """
        Count the number of null bytes at the specified file pointer
        """
        nullbuffer = 0
        while 1:
            if self.f.read(1) == '\x00':
                nullbuffer += 1
            else:
                break
        return nullbuffer


    # ---------------------------------------------------------
    def new_header(self, version=ID3V2_DEFAULT_VERSION):
        """
        Create a new default ID3v2 tag data structure

        @param version: version of the tag to use. default is 2.4.
        @type version: float
        """

        if version not in self.supported:
            raise ID3ParameterException("version %s not supported" % str(version))

        self.tag = {}
        if str(version) in self.supported:
            self.version = str(version)
        else:
            raise ID3NotImplementedException("Version %s not supported", \
                                             str(version))

        if self.version in ('2.4', '2.3'):
            self.tag["ext"] = 0
            self.tag["exp"] = 0
            self.tag["footer"] = 0
        elif self.version == '2.2':
            self.tag["compression"] = 0

        self.tag["unsync"] = 0
        self.tag["size"] = 0
        self.frames = []

    # ---------------------------------------------------------
    def parse_header(self):
        """
        Parse Header of the file

        """
        self.f.seek(0)
        data = self.f.read(ID3V2_FILE_HEADER_LENGTH)
        if len(data) != ID3V2_FILE_HEADER_LENGTH:
            raise ID3HeaderInvalidException("ID3 tag header is incomplete")

        self.tag = {}
        self.frames = []
        id3, ver, flags, rawsize = struct.unpack("!3sHB4s", data)

        if id3 != "ID3":
            raise ID3HeaderInvalidException("ID3v2 header not found")

        self.tag["size"] = unsyncsafe(rawsize)
        # NOTE: size  = excluding header + footer
        version = '2.%d' % (ver >> 8)
        if version not in self.supported:
            raise ID3NotImplementedException("version %s not supported" % \
                                             version)
        else:
            self.version = version

        if self.version in ('2.4', '2.3'):
            for flagname, bit in ID3V2_3_TAG_HEADER_FLAGS:
                self.tag[flagname] = (flags >> bit) & 0x01
        elif self.version == '2.2':
            for flagname, bit in ID3V2_2_TAG_HEADER_FLAGS:
                self.tag[flagname] = (flags >> bit) & 0x01

        if self.tag.has_key("ext") and self.tag["ext"]:
            self.parse_ext_header()

        debug(self.tag)

    # ---------------------------------------------------------
    def parse_ext_header(self):
        """ Parse Extension Header """

        # seek to the extension header position
        self.f.seek(ID3V2_FILE_HEADER_LENGTH)
        data = self.f.read(ID3V2_FILE_EXTHEADER_LENGTH)
        extsize, flagbytes = struct.unpack("!4sB", data)
        extsize = unsyncsafe(extsize)
        readdata = 0
        if flagbytes == 1:
            flags = struct.unpack("!B",self.f.read(flagbytes))[0]
            self.tag["update"] = ( flags & 0x40 ) >> 6
            if ((flags & 0x20) >> 5):
                self.tag["crc"] = unsyncsafe(self.f.read(5))
                readdata += 5
            if ((flags & 0x10) >> 4):
                self.tag["restrictions"] = struct.unpack("!B", self.f.read(1))[0]
                # FIXME: store these restrictions properly
                readdata += 1

            # work around dodgy ext headers created by libid3tag
            if readdata < extsize - ID3V2_FILE_EXTHEADER_LENGTH - flagbytes:
                self.f.read(extsize - ID3V2_FILE_EXTHEADER_LENGTH - flagbytes - readdata)
        else:
            # ignoring unrecognised extension header
            self.f.read(extsize - ID3V2_FILE_EXTHEADER_LENGTH)
        return 1

    # ---------------------------------------------------------
    def parse_footer(self):
        """Parse Footer

        @todo: implement me
        """
        return 0 # FIXME

    # ---------------------------------------------------------
    def parse_frames(self):
        """ Recursively Parse Frames """
        read = 0
        readframes = 0

        while read < self.tag["size"]:
            framedata = self.get_next_frame(self.tag["size"] - read)
            if framedata:
                try:
                    read += len(framedata)
                    if self.version == '2.2':
                        frame = ID3v2_2_Frame(frame=framedata)
                    elif self.version == '2.3':
                        frame = ID3v2_3_Frame(frame=framedata)
                    elif self.version == '2.4':
                        frame = ID3v2_4_Frame(frame=framedata)
                    readframes += 1
                    self.frames.append(frame)
                except ID3Exception:
                    pass # ignore unrecognised frames
            else:
                self.tag["padding"] = self._read_null_bytes()
                debug("NULL Padding: %d" % self.tag["padding"])
                break

        # do a sanity check on the size/padding
        if not self.tag.has_key("padding"):
            self.tag["padding"] = 0

        if self.tag["size"] != read + self.tag["padding"]:
            self.tag["size"] = read + self.tag["padding"]

        return len(self.frames)

    # ---------------------------------------------------------
    def get_next_frame(self, search_length):

        # skip null frames
        c = self.f.read(1)
        self.f.seek(-1, 1)
        if c == '\x00':
            return '' # check for NULL frames

        hdr = self.f.read(ID3V2_HEADER_LEN[self.version])
        size = ID3V2_DATA_LEN[self.version](hdr)
        if size > self.tag["size"]:
            return '' # # we should actually just abort here...
        data = self.f.read(size)
        return hdr + data

    # ---------------------------------------------------------
    def construct_header(self, size):
        """
        Construct Header Bytestring to for tag

        @param size: size to encode into the bytestring. Note the size is the whole \
                      size of the tag minus the header and footer
        @type size: int
        """
        if self.version in ('2.3', '2.4'):
            flags = ID3V2_3_TAG_HEADER_FLAGS
        elif self.version == '2.2':
            flags = ID3V2_2_TAG_HEADER_FLAGS

        bytestring = 'ID3'
        flagbyte = 0
        for flagname, bit in flags:
            flagbyte = flagbyte | ((self.tag[flagname] & 0x01) << bit)

        bytestring += struct.pack('<H', int(self.version[-1]))
        bytestring += struct.pack('!B', flagbyte)
        bytestring += syncsafe(size, 4)
        return bytestring

    # ---------------------------------------------------------
    def construct_ext_header(self):
        """
        Construct an Extension Header (FIXME)
        """
        self.tag['ext'] = 0
        return '' # FIXME!

    # ---------------------------------------------------------
    def construct_footer(self):
        """
        Construct a Footer (FIXME)
        """
        return '' # FIXME!

    # ---------------------------------------------------------
    def commit_to_file(self, filename):
        newf = open(filename, 'wb+')
        framesstring = ''.join(map(lambda x: x.output(), self.frames))
        footerstring = ''
        extstring = ''

        # backup existing mp3 data
        self.f.seek(self.mp3_data_offset())
        t = tempfile.TemporaryFile()
        buf = self.f.read(1024)
        while buf:
            t.write(buf)
            buf = self.f.read(1024)

        tag_content_size = len(extstring) + len(framesstring)
        headerstring = self.construct_header(tag_content_size + \
                                              ID3V2_FILE_DEFAULT_PADDING)

        newf.write(headerstring)
        newf.write(extstring)
        newf.write(framesstring)
        newf.write('\x00' * ID3V2_FILE_DEFAULT_PADDING)
        newf.write(footerstring)
        t.seek(0)
        buf = t.read(1024)
        while buf:
            newf.write(buf)
            buf = t.read(1024)
        t.close()
        newf.close()

    # ---------------------------------------------------------
    def commit(self, pretend=False):
        """ Commit Changes to MP3. This means writing to file.
        Will fail if file is not writable

        @param pretend: boolean
        @type pretend: Do not actually write to file, but pretend to.
        """

        if self.read_only:
            return False # give up if it's readonly - don't bother!

        # construct frames, footers and extensions
        framesstring = ''.join(map(lambda x: x.output(), self.frames))
        footerstring = ''
        extstring = ''

        if self.tag.has_key("ext") and self.tag["ext"]:
            extstring = self.construct_ext_header()
        if self.tag.has_key("footer") and self.tag["footer"]:
            footerstring = self.construct_footer()



        # make sure there is enough space from start of file to
        # end of tag, otherwise realign tag
        tag_content_size = len(extstring) + len(framesstring)

        if self.tag["size"] < tag_content_size:
            headerstring = self.construct_header(tag_content_size + \
                                                  ID3V2_FILE_DEFAULT_PADDING)

            # backup existing mp3 data
            self.f.seek(self.mp3_data_offset())
            t = tempfile.TemporaryFile()
            buf = self.f.read(1024)
            while buf:
                t.write(buf)
                buf = self.f.read(1024)

            # write to a new file
            if not pretend:
                self.f.close()
                self.f = open(self.filename, 'wb+')
                self.f.write(headerstring)
                self.f.write(extstring)
                self.f.write(framesstring)
                self.f.write('\x00' * ID3V2_FILE_DEFAULT_PADDING)
                self.f.write(footerstring)

                # write mp3 data to new file
                t.seek(0)
                buf = t.read(1024)
                while buf:
                    self.f.write(buf)
                    buf = t.read(1024)
                t.close()
                self.f.close()

                self.f = open(self.filename, 'rb+')
                self.tag["size"] = len(headerstring) + len(extstring) + \
                                   ID3V2_FILE_DEFAULT_PADDING

        else:
            headerstring = self.construct_header(self.tag["size"])
            if not pretend:
                self.f.seek(0)
                self.f.write(headerstring)
                self.f.write(extstring)
                self.f.write(framesstring)
                written = len(extstring) + len(framesstring)
                warn("Written Bytes: %d" % written)
                # add padding
                self.f.write('\x00' * (self.tag["size"] - written))
                # add footerstring
                self.f.write(footerstring)
                self.f.flush()


