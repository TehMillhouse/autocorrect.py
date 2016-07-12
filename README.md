Autocorrect.py
==============

Heavy user of `¯\_(ツ)_/¯`, but can't be bothered to copy & paste it every time you want to use it?
Autokey too capable for you? Then this is the prefect shitty one-day project for you!

Simply add a config file at `~/.config/autocorrect` containing a JSON object with the mapping from pattern to substitution and run this script.

Example:
```json
{
    "dunnolol": "¯\\_(ツ)_/¯",
    "gal pals": "ｇａｌ　ｐａｌｓ"
}
```

License
-------

GPLv2 (I'm sorry).

Caveats
-------

* There's a ton of patterns that won't work, e.g. anything that requires modifier Keys to type.
* Substitutions may trigger additional substitutions. I.e. setting up a substitution from `"a"` to `"aa"` is a bad idea.
* Non-ascii characters are tricky to get working through keyboard events alone, so I've opted for sending <kbd>Ctrl</kdb>+<kbd>Shift</kbd>+<kbd>u</kbd> followed by the hexadecimal unicode codepoint and <kbd>Space</kbd>. This works in Gtk and Qt programs, but not everywhere (it doesn't work in Emacs and xterm for example).

(Note: the "accepted" way to work around this is to temporarily modify the keyboard mapping to include whatever unicode character is to be typed and wait a couple of milliseconds for the X server to catch up before typing it. That was a bit too icky for me)
