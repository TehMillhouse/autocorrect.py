#!/usr/bin/env python3
#
#    Copyright (C) 2006 Alex Badea <vamposdecampos@gmail.com>
#    Copyright (C) 2013 LiuLang <gsushzhsosgsu@gmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# This is mostly based on the demo for the RECORD extension (from python-xlib),
# with the special_X_keysyms table taken from pykey (http://shallowsky.com/software/crikey).
# Both of these are GPL, so alas, this will have to be, too.
# Thanks, Stallman.

import os
import json

import Xlib
from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq

inject_dpy = display.Display()
record_dpy = display.Display()

def reset_state():
    global state
    state = {k: 0 for k in shortcuts}

shortcuts = {
    'help': 'Please add a config file at ~/.config/autocorrect containing a JSON object with a text->text mapping.'
}

def load_config():
    global shortcuts
    config_path = os.path.join(os.path.expanduser('~'), '.config/autocorrect')
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            shortcuts = json.loads(f.read())


def advance_state(char): # -> (key, value) if key has been detected, else None
    for key in state:
        if key[state[key]] == char:
            # done?
            if len(key) == state[key]+1:
                # last character was just matched!
                state[key] = 0
                return (key, shortcuts[key])
            # next state
            state[key] += 1
        else:
            state[key] = 0


special_X_keysyms = {
    ' ' : "space",
    '\t' : "Tab",
    '\n' : "Return",  # for some reason this needs to be cr, not lf
    '\r' : "Return",
    '\e' : "Escape",
    '!' : "exclam",
    '#' : "numbersign",
    '%' : "percent",
    '$' : "dollar",
    '&' : "ampersand",
    '"' : "quotedbl",
    '\'' : "apostrophe",
    '(' : "parenleft",
    ')' : "parenright",
    '*' : "asterisk",
    '=' : "equal",
    '+' : "plus",
    ',' : "comma",
    '-' : "minus",
    '.' : "period",
    '/' : "slash",
    ':' : "colon",
    ';' : "semicolon",
    '<' : "less",
    '>' : "greater",
    '?' : "question",
    '@' : "at",
    '[' : "bracketleft",
    ']' : "bracketright",
    '\\' : "backslash",
    '^' : "asciicircum",
    '_' : "underscore",
    '`' : "grave",
    '{' : "braceleft",
    '|' : "bar",
    '}' : "braceright",
    '~' : "asciitilde"
    }

special_X_keysyms_inv = {v: k for k, v in special_X_keysyms.items()}

def lookup_keysym(keysym):
    for name in dir(XK):
        if name[:3] == "XK_" and getattr(XK, name) == keysym:
            return name[3:]
    return "[%d]" % keysym

def inject_unicode(char):
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyPress, 37)  # ctrl
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyPress, 50)  # shift

    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyPress, 30)  # u
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyRelease, 30)

    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyRelease, 37)  # ctrl
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyRelease, 50)  # shift

    # str(unicode-escape) gives us something like "b'\u1313'" or "b'\xeb'", so we need to skip
    # the first 5 and the very last character
    codepoint = str(char.encode('unicode-escape'))[5:-1]
    codepoint = hex(ord(char))[2:]
    for n in codepoint:
        keycode = inject_dpy.keysym_to_keycode(XK.string_to_keysym(n))
        Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyPress, keycode)
        Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyRelease, keycode)

    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyPress, 65)  # space, ends unicode input
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyRelease, 65)


def backspace():
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyPress, 22)
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyRelease, 22)


def inject_ascii(char):
    if char in special_X_keysyms:
        keysym = XK.string_to_keysym(special_X_keysyms[char])
    else:
        keysym = XK.string_to_keysym(char)
    keycode = inject_dpy.keysym_to_keycode(keysym)
    if char.isupper() or char in "~!@#$%^&*()_+{}|:\"<>?":
        Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyPress, 50)  # shift
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyPress, keycode)
    Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyRelease, keycode)
    if char.isupper() or char in "~!@#$%^&*()_+{}|:\"<>?":
        Xlib.ext.xtest.fake_input(inject_dpy, Xlib.X.KeyRelease, 50)  # shift

def inject_str(string):
    for c in string:
        try:
            c.encode('ascii')
            inject_ascii(c)
        except:
            inject_unicode(c)
    inject_dpy.flush()


def record_callback(reply):
    if reply.category != record.FromServer:
        return
    if reply.client_swapped:
        print("* received swapped protocol data, cowardly ignored")
        return
    if not len(reply.data) or reply.data[0] < 2:
        # not an event
        return

    data = reply.data
    while len(data):
        event, data = rq.EventField(None).parse_binary_value(data,
                record_dpy.display, None, None)

        if event.type in [X.KeyPress, X.KeyRelease]:
            pr = event.type == X.KeyPress and "Press" or "Release"

            keysym = inject_dpy.keycode_to_keysym(event.detail, 0)
            if not keysym:
                print("KeyCode%s %s" % (pr, event.detail))
            else:
                char = lookup_keysym(keysym)
                char = special_X_keysyms_inv.get(char, char)
                if pr == 'Release' and len(char) < 2:
                    char = lookup_keysym(keysym)
                    char = special_X_keysyms_inv.get(char, char)
                    res = advance_state(char)
                    if res:
                        # recognized a shortcut!
                        print('substituting: %s --> %s' % (res[0], res[1]))
                        for _ in range(len(res[0])):
                            backspace()  # delete the original text
                        inject_str(res[1])

        elif event.type == X.FocusOut:
            reset_state()

def main():
    # Create a recording context; we only want key and focus events
    ctx = record_dpy.record_create_context(
            0,
            [record.AllClients],
            [{
                'core_requests': (0, 0),
                'core_replies': (0, 0),
                'ext_requests': (0, 0, 0, 0),
                'ext_replies': (0, 0, 0, 0),
                'delivered_events': (X.FocusIn, X.FocusOut),
                'device_events': (X.KeyPress, X.KeyRelease),
                'errors': (0, 0),
                'client_started': False,
                'client_died': False,
            }])

    # Enable the context; this only returns after a call to record_disable_context,
    # while calling the callback function in the meantime
    try:
        record_dpy.record_enable_context(ctx, record_callback)
    except:
        pass
    print("shutting down")
    # Finally free the context
    record_dpy.record_free_context(ctx)



if __name__ == '__main__':
    reset_state()
    load_config()
    main()
