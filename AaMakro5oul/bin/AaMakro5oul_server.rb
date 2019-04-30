#!/usr/bin/ruby

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

# ******************************************************************************
# This script is used to convert OSC messages to mouse and keyboard events in
# order to control some features in Ableton Live that are not possible to be
# activated through the Python API interface.
# ******************************************************************************

require 'socket';
require 'mouse'; # gem install mouse

require "#{File.dirname(__FILE__)}/OscDecode";
require "#{File.dirname(__FILE__)}/OscEncode";

sProduct    = 'AaMakro5oul';
sRoot       = ENV['HOME'] || '/';
sConfigPath = "#{sRoot}/#{sProduct}/config.txt";

# define default values ******************************************************************

# udp port where this script will be listening
nRxPort = 2729;

# variable to control ratio of vertical and horizontal mouse scroll
nScrollBase = 2;

# variables to control mouse position
nMouseBorder = 10.0;
nMouseMaxX   = 1920.0;
nMouseMaxY   = 1200.0;

# screen position of buttons
# (these functions cannot be activated through the Python API)
nSongPosX    = 1200
nSongPosY    = 1050
nCuePosX     = 1814
nCuePosY     = 810
nLegatoPosX  = 328
nLegatoPosY  = 992

# parse config file (if found) ***********************************************************

begin
    sConfig = File.read(sConfigPath);

    nRxPort      = $1.to_i if (sConfig =~ /^\s*ruby_rx_port\s*\|\s*(\d+)\s*$/);

    nScrollBase  = $1.to_i if (sConfig =~ /^\s*scroll_base\s*\|\s*(\d+)\s*$/);

    nMouseBorder = $1.to_f if (sConfig =~ /^\s*mouse_border\s*\|\s*(\d+)\s*$/);
    nMouseMaxX   = $1.to_f if (sConfig =~ /^\s*mouse_max_x\s*\|\s*(\d+)\s*$/);
    nMouseMaxY   = $1.to_f if (sConfig =~ /^\s*mouse_max_y\s*\|\s*(\d+)\s*$/);

    nSongPosX    = $1.to_i if (sConfig =~ /^\s*song_pos_x\s*\|\s*(\d+)\s*$/);
    nSongPosY    = $1.to_i if (sConfig =~ /^\s*song_pos_y\s*\|\s*(\d+)\s*$/);
    nCuePosX     = $1.to_i if (sConfig =~ /^\s*cue_pos_x\s*\|\s*(\d+)\s*$/);
    nCuePosY     = $1.to_i if (sConfig =~ /^\s*cue_pos_y\s*\|\s*(\d+)\s*$/);
    nLegatoPosX  = $1.to_i if (sConfig =~ /^\s*legato_pos_x\s*\|\s*(\d+)\s*$/);
    nLegatoPosY  = $1.to_i if (sConfig =~ /^\s*legato_pos_y\s*\|\s*(\d+)\s*$/);

rescue Exception => e
    puts("! Error: attempting to open configuration file '#{sConfigPath}' failed.");
    puts("         #{e.to_s}");
    puts("Using default config values.");
end

puts('Configuration: ');
puts(" > Rx port     : #{nRxPort}");
puts(" > Scroll base : #{nScrollBase}");
puts(" > Mouse border: #{nMouseBorder}");
puts(" > Mouse max x : #{nMouseMaxX}");
puts(" > Mouse max y : #{nMouseMaxY}");
puts(" > Song pos x  : #{nSongPosX}");
puts(" > Song pos y  : #{nSongPosY}");
puts(" > Cue pos x   : #{nCuePosX}");
puts(" > Cue pos y   : #{nCuePosY}");
puts(" > Legato pos x: #{nLegatoPosX}");
puts(" > Legato pos y: #{nLegatoPosY}");

# state variables to control continuous mouse pointer position update
nMaxX       = nMouseMaxX - nMouseBorder * 2.0;
nMaxY       = nMouseMaxY - nMouseBorder * 2.0;
nMouseXCurr = 0;
nMouseYCurr = 0;
nMouseXNew  = 0;
nMouseYNew  = 0;

# main loop ******************************************************************************

puts("* Starting UDP server in port #{nRxPort}");

Socket.udp_server_loop(nRxPort) { |sMsg, oMsgSrc|
    oPublAddr = oMsgSrc.remote_address;
    sPublAddr = "#{oPublAddr.ip_address}:#{oPublAddr.ip_port}";

    sAddr, aArgs = OscDecode.new.decode_single_message(sMsg)

    # do not print touch events (its a lot of them)
    puts(" > #{sAddr}: #{aArgs.join(' | ')}") if (sAddr != '/pad/mouse/pos/touch');

    bKeyEvent    = false;
    bMouseScroll = false;
    sMouseKey    = nil;

    case (sAddr)
        # arrange window toggle
        when '/session/cmd/arrange'
            bKeyEvent = true; sCode = '48'; sMod = '';

        # waveform window toggle
        when '/session/cmd/toggle'
            bKeyEvent = true; sCode = '48'; sMod = 'using shift down';

        # pause
        when '/session/cmd/pause'
            bKeyEvent = true; sCode = '49'; sMod = 'using shift down';

        # zoom
        when '/session/zoom/in'
            bKeyEvent = true; sKey = '+'; sMod = ''; # using {control down, shift down, option down, command down}
        when '/session/zoom/out'
            bKeyEvent = true; sKey = '-'; sMod = '';

        # clip slot mark-selection
        when '/clip/cmd/sel/left'
            bKeyEvent = true; sCode = '123'; sMod = 'using shift down';
        when '/clip/cmd/sel/right'
            bKeyEvent = true; sCode = '124'; sMod = 'using shift down';
        when '/clip/cmd/sel/down'
            bKeyEvent = true; sCode = '125'; sMod = 'using shift down';
        when '/clip/cmd/sel/up'
            bKeyEvent = true; sCode = '126'; sMod = 'using shift down';

        # copy-paste commands
        when '/clip/cmd/cut'
            bKeyEvent = true; sKey = 'x'; sMod = 'using command down';
        when '/clip/cmd/copy'
            bKeyEvent = true; sKey = 'c'; sMod = 'using command down';
        when '/clip/cmd/paste'
            bKeyEvent = true; sKey = 'v'; sMod = 'using command down';

        # mouse pos
        when '/pad/mouse/pos/touch'
            if (aArgs[0] == 1.0) # touching pad
                oPos = Mouse.current_position;
                puts(" -> Mouse start: [#{oPos.x}, #{oPos.y}]");
            else                 # releasing pad
                nMouseXCurr = (nMouseXCurr == nMouseXNew ? nMouseXNew + 1 : nMouseXNew)
                nMouseYCurr = (nMouseYCurr == nMouseYNew ? nMouseYNew + 1 : nMouseYNew)
                puts(" -> Mouse end: [#{nMouseXCurr}, #{nMouseYCurr}]")
                Mouse.move_to([nMouseXCurr, nMouseYCurr], 0.0)
            end

        when '/pad/mouse/pos/xy'
            nMouseXNew = (aArgs[0] * nMaxX + nMouseBorder)
            nMouseYNew = ((1.0 - aArgs[1]) * nMaxY + nMouseBorder)

        when '/pad/mouse/pos/center'
            # (0.0,    0.0)      (1920.0,    0.0)
            #
            # (0.0, 1200.0)      (1920.0, 1200.0)
            nMouseXNew = (0.5 * nMaxX + nMouseBorder)
            nMouseYNew = (0.5 * nMaxY + nMouseBorder)
            nMouseXCurr = (nMouseXCurr == nMouseXNew ? nMouseXNew + 1 : nMouseXNew)
            nMouseYCurr = (nMouseYCurr == nMouseYNew ? nMouseYNew + 1 : nMouseYNew)
            puts("> [#{nMouseXCurr}, #{nMouseYCurr}]")
            Mouse.move_to([nMouseXCurr, nMouseYCurr], 0.0)

        when '/pad/mouse/pos/song'
            Mouse.move_to([nSongPosX, nSongPosY], 0.0)
            Mouse.click

        when '/session/cmd/cueing'
            Mouse.move_to([nCuePosX, nCuePosY], 0.0)
            Mouse.click

        when '/clip/cmd/legato'
            Mouse.move_to([nLegatoPosX, nLegatoPosY], 0.0)
            Mouse.click

        # mouse click
        when '/pad/mouse/click/left/1'
            Mouse.click;
        when '/pad/mouse/click/left/2'
            Mouse.double_click;
        when '/pad/mouse/click/right/1'
            Mouse.right_click;
        when '/pad/mouse/click/right/2'
            puts('> No double right click'); # no double right click :-(

        # mouse horizontal scroll
        when '/pad/mouse/scroll/left/1'
            bMouseScroll = true; sMouseKey = 'shift'; nScrollAmount = nScrollBase;
        when '/pad/mouse/scroll/left/2'
            bMouseScroll = true; sMouseKey = 'shift'; nScrollAmount = nScrollBase * 4;
        when '/pad/mouse/scroll/left/3'
            bMouseScroll = true; sMouseKey = 'shift'; nScrollAmount = nScrollBase * 16;
        when '/pad/mouse/scroll/left/4'
            bMouseScroll = true; sMouseKey = 'shift'; nScrollAmount = nScrollBase * 64;
        when '/pad/mouse/scroll/right/1'
            bMouseScroll = true; sMouseKey = 'shift'; nScrollAmount = -nScrollBase;
        when '/pad/mouse/scroll/right/2'
            bMouseScroll = true; sMouseKey = 'shift'; nScrollAmount = -nScrollBase * 4;
        when '/pad/mouse/scroll/right/3'
            bMouseScroll = true; sMouseKey = 'shift'; nScrollAmount = -nScrollBase * 16;
        when '/pad/mouse/scroll/right/4'
            bMouseScroll = true; sMouseKey = 'shift'; nScrollAmount = -nScrollBase * 64;

        # mouse vertical scroll
        when '/pad/mouse/scroll/up/1'
            Mouse.scroll(nScrollBase);
        when '/pad/mouse/scroll/up/2'
            Mouse.scroll(nScrollBase * 4);
        when '/pad/mouse/scroll/up/3'
            Mouse.scroll(nScrollBase * 16);
        when '/pad/mouse/scroll/up/4'
            Mouse.scroll(nScrollBase * 64);
        when '/pad/mouse/scroll/down/1'
            Mouse.scroll(-nScrollBase);
        when '/pad/mouse/scroll/down/2'
            Mouse.scroll(-nScrollBase * 4);
        when '/pad/mouse/scroll/down/3'
            Mouse.scroll(-nScrollBase * 16);
        when '/pad/mouse/scroll/down/4'
            Mouse.scroll(-nScrollBase * 64);
    end

    if (bKeyEvent)
        sCmd = sKey ?
            "osascript -e 'tell application \"System Events\" to keystroke \"#{sKey}\" #{sMod}'" :
            "osascript -e 'tell application \"System Events\" to key code #{sCode} #{sMod}'";
        puts(" => #{sCmd}")
        system(sCmd);
    end

    if (bMouseScroll)
        system("osascript -e 'tell application \"System Events\" to key down #{sMouseKey}'") if (sMouseKey != nil);
        Mouse.scroll(nScrollAmount);
        system("osascript -e 'tell application \"System Events\" to key up #{sMouseKey}'") if (sMouseKey != nil);
    end
}

puts("- Done!");

=begin

A port of mouse.rb from AXElements, but cleaned up and rewritten in C to be more portable across languages and runtimes.

By itself, the mouse gem is not that useful; but in combination with a gem for discovering the positions of things (like buttons) on the screen, this gem is very powerful and can be used for tasks such as automated functional testing; this is the purpose of the AXElements project.

Documentation

Code Climate Dependency Status Gem Version Bitdeli Badge

Examples

require 'mouse'

Mouse.current_position # => #<CGPoint x=873.2 y=345.0>

# positions can be given as an array with two points, or a CGPoint
Mouse.move_to [10, 10]
Mouse.move_to CGPoint.new(10, 10)

# optionally specify how long it should take the mouse to move
Mouse.move_to [800, 300], 0.2

Mouse.click
Mouse.double_click
Mouse.triple_click

# secondary_click and right_click are aliases to the same method
Mouse.secondary_click
Mouse.right_click

# positive number scrolls up, negative number scrolls down
Mouse.scroll 10
Mouse.scroll -10

# perform horizontal scrolling as well
# positive number scrolls left, negative number scrolls right
Mouse.horizontal_scroll 10
Mouse.horizontal_scroll -10

# optionally specify units for scroll amount, :pixel or :line
Mouse.scroll 10, :pixels
Mouse.scroll -10, :pixels

# just like a two finger double tap
Mouse.smart_magnify
Mouse.smart_magnify [600, 500]

# pinch-to-zoom
Mouse.pinch :zoom
Mouse.pinch :expand, 2

# pinch-to-unzoom
Mouse.pinch :unzoom, 2.0, 5.0
Mouse.pinch :contract, 1.0

# even perform rotation gestures!
Mouse.rotate :clockwise, 90
Mouse.rotate :counter_clockwise, 180
Mouse.rotate :cw, 360

# swipe, swipe, swipe
Mouse.swipe :up
Mouse.swipe :down
Mouse.swipe :left
Mouse.swipe :right
=end

=begin
0 0x00 ANSI_A
1 0x01 ANSI_S
2 0x02 ANSI_D
3 0x03 ANSI_F
4 0x04 ANSI_H
5 0x05 ANSI_G
6 0x06 ANSI_Z
7 0x07 ANSI_X
8 0x08 ANSI_C
9 0x09 ANSI_V
10 0x0A ISO_Section
11 0x0B ANSI_B
12 0x0C ANSI_Q
13 0x0D ANSI_W
14 0x0E ANSI_E
15 0x0F ANSI_R
16 0x10 ANSI_Y
17 0x11 ANSI_T
18 0x12 ANSI_1
19 0x13 ANSI_2
20 0x14 ANSI_3
21 0x15 ANSI_4
22 0x16 ANSI_6
23 0x17 ANSI_5
24 0x18 ANSI_Equal
25 0x19 ANSI_9
26 0x1A ANSI_7
27 0x1B ANSI_Minus
28 0x1C ANSI_8
29 0x1D ANSI_0
30 0x1E ANSI_RightBracket
31 0x1F ANSI_O
32 0x20 ANSI_U
33 0x21 ANSI_LeftBracket
34 0x22 ANSI_I
35 0x23 ANSI_P
36 0x24 Return
37 0x25 ANSI_L
38 0x26 ANSI_J
39 0x27 ANSI_Quote
40 0x28 ANSI_K
41 0x29 ANSI_Semicolon
42 0x2A ANSI_Backslash
43 0x2B ANSI_Comma
44 0x2C ANSI_Slash
45 0x2D ANSI_N
46 0x2E ANSI_M
47 0x2F ANSI_Period
48 0x30 Tab
49 0x31 Space
50 0x32 ANSI_Grave
51 0x33 Delete
53 0x35 Escape
55 0x37 Command
56 0x38 Shift
57 0x39 CapsLock
58 0x3A Option
59 0x3B Control
60 0x3C RightShift
61 0x3D RightOption
62 0x3E RightControl
63 0x3F Function
64 0x40 F17
65 0x41 ANSI_KeypadDecimal
67 0x43 ANSI_KeypadMultiply
69 0x45 ANSI_KeypadPlus
71 0x47 ANSI_KeypadClear
72 0x48 VolumeUp
73 0x49 VolumeDown
74 0x4A Mute
75 0x4B ANSI_KeypadDivide
76 0x4C ANSI_KeypadEnter
78 0x4E ANSI_KeypadMinus
79 0x4F F18
80 0x50 F19
81 0x51 ANSI_KeypadEquals
82 0x52 ANSI_Keypad0
83 0x53 ANSI_Keypad1
84 0x54 ANSI_Keypad2
85 0x55 ANSI_Keypad3
86 0x56 ANSI_Keypad4
87 0x57 ANSI_Keypad5
88 0x58 ANSI_Keypad6
89 0x59 ANSI_Keypad7
90 0x5A F20
91 0x5B ANSI_Keypad8
92 0x5C ANSI_Keypad9
93 0x5D JIS_Yen
94 0x5E JIS_Underscore
95 0x5F JIS_KeypadComma
96 0x60 F5
97 0x61 F6
98 0x62 F7
99 0x63 F3
100 0x64 F8
101 0x65 F9
102 0x66 JIS_Eisu
103 0x67 F11
104 0x68 JIS_Kana
105 0x69 F13
106 0x6A F16
107 0x6B F14
109 0x6D F10
111 0x6F F12
113 0x71 F15
114 0x72 Help
115 0x73 Home
116 0x74 PageUp
117 0x75 ForwardDelete
118 0x76 F4
119 0x77 End
120 0x78 F2
121 0x79 PageDown
122 0x7A F1
123 0x7B LeftArrow
124 0x7C RightArrow
125 0x7D DownArrow
126 0x7E UpArrow
=end

