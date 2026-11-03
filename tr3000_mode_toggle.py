# -*- coding: utf-8 -*-
# Translator3000 - quick mode toggle (separate module)
#
# Lets the player flip Translator3000 between "off" (original text) and
# "db_only" (translations taken from the database) without opening the
# Ctrl+` panel:
#
#   * a badge in the top-right corner of the game screen always shows the
#     current mode ("OFF: original" / "Mode: DB only" / ...); clicking it
#     toggles;
#   * Alt+1 (Option+1 on macOS) toggles from the keyboard.
#
# This is deliberately a separate file from tr3000_ui_translate.py: this
# module switches Translator3000's mode, which affects DIALOGUE and UI
# alike; it is not UI translation logic.
#
# How it works
# ------------
# The switch goes through the mode property of translator3000._gui - the
# exact same path the Ctrl+` panel buttons use - so:
#   * the panel reflects the change immediately;
#   * dialogue AND interface text follow together (mode is read live by
#     tr3000_ui_translate.translator_mode(), which still lives there and is
#     imported lazily, only for the badge label / logging);
#   * Translator3000's own side effects (database-only switch, interrupting
#     in-flight translations, restarting the interaction when leaving
#     prescan) are handled by Translator3000 itself.
# No settings file is touched: this is the runtime mode, and a restart
# still follows the persisted "modeOnStartup".
#
# Toggle rules:
#   off                 -> db_only   (show translations from the database)
#   db_only             -> off       (show the original text)
#   prescan / realtime  -> off       (bail out safely to the original text)
from __future__ import unicode_literals

import sys

try:
    text_type = unicode  # noqa: F821 - Python 2 (old Ren'Py)
except NameError:
    text_type = str

VERSION = 1

MODE_OFF = 'off'
MODE_DB_ONLY = 'db_only'
MODE_PRESCAN = 'prescan'
MODE_REALTIME = 'realtime'
_KNOWN_MODES = (MODE_OFF, MODE_DB_ONLY, MODE_PRESCAN, MODE_REALTIME)


def _store():
    return sys.modules.get('store')


def main_object():
    store = _store()
    return getattr(store, 'translator3000', None) if store is not None else None


def current_mode():
    """Current Translator3000 mode, read live; 'off' when unknown/absent.

    Mirrors tr3000_ui_translate.translator_mode() so both modules always
    agree on the mode without importing each other at load time.
    """
    main = main_object()
    if main is None:
        return MODE_OFF
    candidates = []
    gui = getattr(main, '_gui', None)
    if gui is not None:
        candidates.append(getattr(gui, 'mode', None))
        candidates.append(getattr(gui, '_mode', None))
    setting = getattr(main, '_setting', None)
    if isinstance(setting, dict):
        candidates.append(setting.get('mode'))
        candidates.append(setting.get('modeOnStartup'))
    candidates.append(getattr(main, '_mode', None))
    candidates.append(getattr(main, 'mode', None))
    for value in candidates:
        if isinstance(value, text_type):
            value = value.strip().lower()
            if value in _KNOWN_MODES:
                return value
    return MODE_OFF


def _poke_renpy():
    try:
        import renpy
        renpy.restart_interaction()
    except Exception:
        pass


def _log(message):
    # Reuse the UI module's debug log when available (same settings file).
    try:
        import tr3000_ui_translate
        tr3000_ui_translate.log(message)
    except Exception:
        pass


def set_mode(new_mode):
    """Switch Translator3000's own mode. Returns True if accepted.

    Goes through the GUI's `mode` property - the same path the Ctrl+`
    panel buttons use. Falls back to assigning the persisted setting only
    if the property is unavailable.
    """
    mode = (new_mode or '').strip().lower()
    if mode not in _KNOWN_MODES:
        return False
    main = main_object()
    if main is None:
        return False
    gui = getattr(main, '_gui', None)
    changed = False
    if gui is not None:
        try:
            gui.mode = mode
            changed = True
        except Exception:
            pass
    if not changed:
        setting = getattr(main, '_setting', None)
        if isinstance(setting, dict):
            setting['modeOnStartup'] = mode
            changed = True
    if changed:
        _log('Mode switched to %r (was read back as %r).'
             % (mode, current_mode()))
        _poke_renpy()
    return changed


def toggle_db_only():
    """off <-> db_only quick toggle (top-right badge / Alt+1 hotkey).

    MUST return None: this is called from Ren'Py screen actions
    (Function(...)), and a non-None return value ends the current
    interaction - during a dialogue line that means jumping straight to
    the next line/scene. Returning None (plus the restart_interaction in
    set_mode) keeps the player on the current line, just re-rendered in
    the other language.
    """
    current = current_mode()
    target = MODE_DB_ONLY if current == MODE_OFF else MODE_OFF
    if current in (MODE_PRESCAN, MODE_REALTIME):
        target = MODE_OFF
    set_mode(target)
    # Implicitly returns None - see docstring, do not change.


def mode_label():
    """Short label for the top-right mode badge."""
    return {
        MODE_OFF: u'OFF: original',
        MODE_DB_ONLY: u'Mode: DB only',
        MODE_PRESCAN: u'Mode: prescan',
        MODE_REALTIME: u'Mode: realtime',
    }.get(current_mode(), u'Mode: ?')
