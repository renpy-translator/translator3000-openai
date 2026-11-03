# -*- coding: utf-8 -*-
# Translator3000 - UI translation (separate module, game independent)
#
# Why this exists
# ---------------
# Stock Translator3000 has a workMethod "allText" (Beta). In dialogueOnly
# mode it never sees interface text, and allText is beta / heavy because it
# routes *every* string through the dialogue pipeline. This module instead
# hooks Ren'Py itself, at the one place all screen text passes through:
#
#     renpy.text.text.Text.set_text()
#
# Every `text`, `textbutton`, `label`, tooltip, bar caption ... in every
# screen of every Ren'Py game becomes a Text displayable and goes through
# set_text(). The say screen's dialogue does too, but Translator3000 has
# already replaced that string with its translation before the screen is
# built, so here we only translate what is still in the source language and
# still unknown to Translator3000's own database. Consequences:
#   * no per-game screen names, ids or file names are hardcoded;
#   * a new game needs zero configuration - open a screen, its labels are
#     collected, translated once, cached, and reused on every other screen;
#   * strings already translated as dialogue are never sent twice.
#
# How translation is performed
# ----------------------------
# Two separate gates, exactly as requested:
#
# 1. PRESCAN always collects UI strings. When Translator3000 prescans,
#    Preparer.get_translate_parts() receives every string it found in the
#    game script. This module appends the strings it statically extracts
#    from all registered Ren'Py screens (labels, button captions, text
#    widgets) to that same list, so they are translated by the prescan and
#    stored in the same provider database as dialogue. Nothing is hardcoded
#    per game: the screen strings come from renpy.display.screen.
#    screens_by_name at runtime.
#
# 2. DISPLAY is opt-in via the "Translate game interface" checkbox in the
#    OpenAI settings screen (default OFF - a fresh game shows the original
#    language). When ticked, UI text follows Translator3000's own mode
#    switch (the Ctrl+` panel):
#      mode "off"               -> every screen shows the original language.
#      mode "db_only"/"prescan" -> UI text is replaced ONLY by translations
#                                  already present in the active provider's
#                                  database (or this session's cache).
#      mode "realtime"          -> additionally, a missing UI string may be
#                                  translated live in a background thread,
#                                  mirroring how dialogue is live-translated.
#    The mode is read live from translator3000._gui.mode / _setting /
#    persisted "modeOnStartup".
#
# Safety rules (a mistranslated UI string must never break a game)
# ----------------------------------------------------------------
#   * never touch the say screen (ids "what"/"who") - dialogue is owned by
#     Translator3000; touching it would double-translate and break the
#     slow-text (typewriter) effect;
#   * never touch Translator3000's own screens (they manage themselves);
#   * never touch strings without letters, pure numbers, file paths, image
#     names, or strings already containing non-source script;
#   * Ren'Py text tags {..}, substitutions [..] and % formats are protected
#     exactly like in tr3000_openai.protect() and verified after return;
#     a bad answer is discarded, the original is shown;
#   * translation runs on a worker thread. Until it returns, the original
#     text stays on screen - the game never freezes waiting for the net;
#   * any exception anywhere falls back to the original string.
#
# Settings (shared file, next to Translator3000's own settings):
#   ~/vladya's projects database/translator3000/_translator3000_ui.json
#     {"ui_translate_enabled": false, "ui_max_chars": 300, "ui_debug": false}
# The checkbox in the OpenAI settings screen toggles ui_translate_enabled.
# Default is OFF: a fresh game shows the original language.
# Old file without the key is treated as OFF (safe direction).
from __future__ import unicode_literals

import io
import json
import os
import re
import sys
import threading

try:
    text_type = unicode  # noqa: F821 - Python 2 (old Ren'Py)
except NameError:
    text_type = str

VERSION = 3
SETTINGS_FILE = '_translator3000_ui.json'

# ---------------------------------------------------------------------------
# Pure helpers (no Ren'Py imports - kept importable for offline unit tests)
# ---------------------------------------------------------------------------

TAG_RE = re.compile(
    r'\{\{|\[[^\[\]]*(?:\[[^\[\]]*\][^\[\]]*)*\]|\{[^{}]*\}'
    r'|%\([^)]+\)[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z]'
    r'|%[#0 +\-]*\d*(?:\.\d+)?[sdif]|%%')
NOT_TRANSLATE = '{#notTranslate}'
# String literals inside a Python expression (for $ / python: screen code).
_EXPR_STRING_RE = re.compile(r'"([^"\\\n]{2,120})"|\'([^\'\\\n]{2,120})\'')


def protect(text):
    """Replace Ren'Py markup with placeholders the model must keep."""
    saved = []

    def replace(match):
        saved.append(match.group(0))
        return '__TR3000_KEEP_%d__' % (len(saved) - 1)

    return TAG_RE.sub(replace, text), saved


def restore(text, saved):
    def replace(match):
        index = int(match.group(1))
        return saved[index] if index < len(saved) else match.group(0)

    return re.sub(r'__TR3000_KEEP_(\d+)__', replace, text)


def placeholders_ok(original_saved, translated):
    found = re.findall(r'__TR3000_KEEP_(\d+)__', translated)
    return sorted(int(x) for x in found) == list(range(len(original_saved)))


def looks_translatable(text, max_chars=300):
    """Decide whether a rendered UI string is worth sending to a translator.

    Deliberately conservative: false negatives (a label left in English) are
    acceptable, false positives (a translated file name / number / id) can
    break a game.
    """
    if not isinstance(text, text_type):
        return False
    stripped = text.strip()
    if not stripped or len(stripped) > max_chars:
        return False
    if stripped.startswith('{#notTranslate}'):
        return False
    # Strip markup before judging the visible content.
    visible = TAG_RE.sub('', stripped)
    visible = re.sub(r'\{[^}]*\}', '', visible).strip()
    if not visible:
        return False
    letters = 0
    for ch in visible:
        if ch.isalpha():
            letters += 1
    if letters < 2:
        return False
    # File names, paths, image tags, sound names: never translate.
    lowered = visible.lower()
    if '/' in visible or '\\' in visible:
        return False
    for ext in ('.png', '.jpg', '.jpeg', '.webp', '.ogg', '.mp3', '.wav',
                '.rpy', '.rpyc', '.json', '.ttf', '.otf'):
        if lowered.endswith(ext) or (ext + ' ') in lowered:
            return False
    # Pure "Key: 12 / 30"-style counters and clock strings.
    if re.match(r'^[\d\s:.,%+\-/()]+$', visible):
        return False
    return True


def already_target_language(text, dest):
    """Cheap script check: if the visible text is already in the destination
    script, sending it again only wastes tokens and can corrupt names."""
    if not dest:
        return False
    dest = dest.lower()
    visible = re.sub(r'\{[^}]*\}', '', text)
    counts = {'cyrillic': 0, 'latin': 0, 'han': 0, 'kana': 0, 'hangul': 0, 'arabic': 0}
    for ch in visible:
        code = ord(ch)
        if 0x0400 <= code <= 0x04ff:
            counts['cyrillic'] += 1
        elif (0x41 <= code <= 0x5a) or (0x61 <= code <= 0x7a) or (0xc0 <= code <= 0x24f):
            counts['latin'] += 1
        elif 0x4e00 <= code <= 0x9fff:
            counts['han'] += 1
        elif 0x3040 <= code <= 0x30ff:
            counts['kana'] += 1
        elif 0xac00 <= code <= 0xd7a3:
            counts['hangul'] += 1
        elif 0x0600 <= code <= 0x06ff:
            counts['arabic'] += 1
    total = sum(counts.values())
    if not total:
        return False
    if dest in ('ru', 'uk', 'be', 'bg', 'sr', 'mk', 'kk'):
        return counts['cyrillic'] * 2 >= total
    if dest in ('zh', 'zh-cn', 'zh-tw', 'ja'):
        return (counts['han'] + counts['kana']) * 2 >= total
    if dest == 'ko':
        return counts['hangul'] * 2 >= total
    if dest in ('ar', 'fa', 'ur'):
        return counts['arabic'] * 2 >= total
    # Latin-script targets (en, vi, es, fr, de, ...): only skip text that is
    # clearly written in a different script.
    other = total - counts['latin']
    return other * 2 >= total and counts['latin'] == 0


# ---------------------------------------------------------------------------
# Runtime state
# ---------------------------------------------------------------------------

class UiState(object):
    def __init__(self):
        # Opt-in display gate (checkbox in the OpenAI settings screen).
        # Default False = a fresh game shows the original language.
        # Prescan collection is independent of this flag and always runs.
        self.enabled = False
        self.max_chars = 300
        self.debug = False
        self.cache = {}          # source -> translation (this session)
        self.pending = set()     # sources with a worker in flight
        self.failed = set()      # sources whose translation failed/was rejected
        self.lock = threading.Lock()
        self.installed = False
        self.settings_path = None
        self.log_path = None
        self._status = 'UI translation: off (tick the checkbox in OpenAI settings to show UI translations).'

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        log(value)


state = UiState()
_worker_started = False
_queue = []
_queue_lock = threading.Lock()
_queue_event = threading.Event()


def log(message):
    if not state.debug or not state.log_path:
        return
    try:
        parent = os.path.dirname(state.log_path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(state.log_path, 'a', encoding='utf-8') as handle:
            handle.write(text_type(message) + u'\n')
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Settings (shared across games, same folder as Translator3000 settings)
# ---------------------------------------------------------------------------

def settings_dir():
    try:
        import tr3000_openai
        folder = tr3000_openai.shared_config_dir()
    except Exception:
        folder = os.path.join(os.path.expanduser('~'),
                              "vladya's projects database", 'translator3000')
    if not os.path.isdir(folder):
        try:
            os.makedirs(folder)
        except Exception:
            pass
    return folder


def load_settings():
    folder = settings_dir()
    state.settings_path = os.path.join(folder, SETTINGS_FILE)
    state.log_path = os.path.join(folder, '_translator3000_ui_debug.log')
    if os.path.isfile(state.settings_path):
        try:
            with io.open(state.settings_path, encoding='utf-8') as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                # Default OFF when the key is missing (safe direction).
                state.enabled = bool(data.get('ui_translate_enabled', False))
                try:
                    state.max_chars = max(20, min(2000, int(data.get('ui_max_chars', 300))))
                except (TypeError, ValueError):
                    pass
                state.debug = bool(data.get('ui_debug', state.debug))
        except Exception:
            pass
    return state


def save_settings():
    try:
        if not state.settings_path:
            load_settings()
        data = {'ui_translate_enabled': bool(state.enabled),
                'ui_max_chars': int(state.max_chars),
                'ui_debug': bool(state.debug)}
        with io.open(state.settings_path, 'w', encoding='utf-8') as handle:
            handle.write(text_type(json.dumps(data, ensure_ascii=False, indent=2)))
    except Exception:
        pass


def set_enabled(value):
    """Checkbox in the OpenAI settings screen: show UI translations or not.

    When OFF (default), the hook is bypassed entirely - original language.
    When ON, UI text follows Translator3000's mode (off = original,
    db_only/prescan = database only, realtime = database + live fallback).
    """
    state.enabled = bool(value)
    save_settings()
    state.status = ('UI translation: on, following Translator3000 mode (%s).'
                    % translator_mode()
                    if state.enabled else
                    'UI translation: off (tick the checkbox in OpenAI settings to show UI translations).')
    with state.lock:
        state.failed.clear()
    _poke_renpy()


# ---------------------------------------------------------------------------
# Talking to Translator3000's active provider
# ---------------------------------------------------------------------------

def _store():
    return sys.modules.get('store')


def main_object():
    store = _store()
    return getattr(store, 'translator3000', None) if store is not None else None


# Translator3000's work modes (Ctrl+` panel, persisted as "modeOnStartup").
MODE_OFF = 'off'
MODE_DB_ONLY = 'db_only'
MODE_PRESCAN = 'prescan'
MODE_REALTIME = 'realtime'
_KNOWN_MODES = (MODE_OFF, MODE_DB_ONLY, MODE_PRESCAN, MODE_REALTIME)


def translator_mode():
    """Current Translator3000 mode, read live; 'off' when unknown/absent.

    Defaulting to 'off' is the safe direction the user asked for: a fresh
    game start (modeOnStartup is typically 'off') shows the original
    language until the user explicitly enables translation.
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


def ui_display_active():
    """True when UI text may be replaced by database translations."""
    return state.enabled and translator_mode() in (MODE_DB_ONLY, MODE_PRESCAN, MODE_REALTIME)


def ui_live_active():
    """True when a missing UI string may also be translated live."""
    return state.enabled and translator_mode() == MODE_REALTIME


# Mode switching (off <-> db_only badge / Alt+1 hotkey) lives in its own
# module, tr3000_mode_toggle.py - it affects dialogue too, so it does not
# belong in this UI-translation file. Only the read helper translator_mode()
# below is kept here, because the render gate needs it on every frame.


def current_languages():
    main = main_object()
    if main is None:
        return None, None
    setting = getattr(main, '_setting', {}) or {}
    # Translator3000 keeps the Ren'Py-style keys in its renpy-facing dict and
    # the file-style keys in the exported settings; accept both.
    dest = setting.get('directionOfTranslation') or setting.get('dest')
    src = setting.get('gameLanguage') or setting.get('src')
    if not dest:
        try:
            import renpy
            dest = getattr(renpy.game.preferences, 'language', None)
        except Exception:
            dest = None
    return dest, src


def active_provider():
    main = main_object()
    if main is None:
        return None
    service = getattr(main, '_translationService', None)
    engine = getattr(main, '_translator_object', None)
    if engine is None or not service:
        return None
    try:
        return engine._get_translator(service)
    except Exception:
        return None


def provider_lookup(provider, source, dest, src):
    """Return a cached translation from the provider's own database, or None.

    The database layout is {src_lang: {source: {dest_lang: translation}}};
    we scan defensively because each provider subclass keeps the same shape
    but under locks of its own.
    """
    database = getattr(provider, '_database', None)
    if not isinstance(database, dict):
        return None
    try:
        for src_lang, texts in database.items():
            if not isinstance(texts, dict):
                continue
            row = texts.get(source)
            if isinstance(row, dict):
                value = row.get(dest)
                if isinstance(value, text_type) and value:
                    return value
    except Exception:
        return None
    return None


def provider_store(provider, source, translation, dest, src):
    """Write a UI translation into the provider database (best effort).

    Mirrors tr3000_transfer.save_provider: merge under the provider lock,
    then ask it to persist. Failures are silent - the session cache in this
    module still makes the translation stick for the current run.
    """
    if not isinstance(translation, text_type) or not translation:
        return False
    src_key = src or 'auto'
    try:
        database = getattr(provider, '_database', None)
        if not isinstance(database, dict):
            return False
        lock = getattr(provider, '_database_lock', None)

        def merge():
            row = database.setdefault(src_key, {}).setdefault(source, {})
            if not row.get(dest):
                row[dest] = translation
            local = getattr(provider, '_local_db', None)
            if isinstance(local, dict):
                local.setdefault(src_key, {}).setdefault(source, {})[dest] = translation

        if lock is not None:
            with lock:
                merge()
        else:
            merge()
        backup = getattr(provider, 'backup_database', None)
        if callable(backup):
            backup()
        return True
    except Exception:
        return False


def provider_translate(provider, source, dest, src):
    """Translate one short UI string with the active provider.

    Providers expose _web_translate(text, dest, src) (TranslatorAbstract);
    some expose translate() instead. Both are tried. The caller runs this on
    a worker thread, so a slow network never blocks the game.
    """
    for name in ('_web_translate', 'translate', 'web_translate'):
        func = getattr(provider, name, None)
        if callable(func):
            try:
                result = func(source, dest, src)
            except TypeError:
                result = func(source, dest)
            if isinstance(result, text_type) and result.strip():
                return result
    return None


# ---------------------------------------------------------------------------
# Worker: translate queued strings off the main thread
# ---------------------------------------------------------------------------

def _enqueue(source):
    with _queue_lock:
        if source in state.pending:
            return
        state.pending.add(source)
        _queue.append(source)
    _queue_event.set()
    _start_worker()


def _start_worker():
    global _worker_started
    if _worker_started:
        return
    _worker_started = True
    thread = threading.Thread(target=_worker_loop)
    thread.daemon = True
    thread.start()


def _worker_loop():
    while True:
        _queue_event.wait()
        while True:
            with _queue_lock:
                if not _queue:
                    _queue_event.clear()
                    break
                batch = _queue[:]
                del _queue[:]
            provider = active_provider()
            dest, src = current_languages()
            if provider is None or not dest:
                with state.lock:
                    for source in batch:
                        state.pending.discard(source)
                state.status = 'UI translation: no active Translator3000 provider - open Translator3000 and pick a service.'
                break
            for source in batch:
                try:
                    _translate_one(provider, source, dest, src)
                except Exception:
                    with state.lock:
                        state.failed.add(source)
                        state.pending.discard(source)
            _poke_renpy()


def _translate_one(provider, source, dest, src):
    protected, saved = protect(source)
    try:
        result = provider_translate(provider, protected, dest, src)
    finally:
        pass
    with state.lock:
        state.pending.discard(source)
    if not result:
        with state.lock:
            state.failed.add(source)
        return
    result = result.strip()
    if not placeholders_ok(saved, result):
        log('UI rejected (placeholders changed): %r -> %r' % (source, result))
        with state.lock:
            state.failed.add(source)
        return
    restored = restore(result, saved)
    if restored == source or not looks_translatable(restored, state.max_chars * 2):
        with state.lock:
            state.failed.add(source)
        return
    with state.lock:
        state.cache[source] = restored
    provider_store(provider, source, restored, dest, src)
    log('UI translated: %r -> %r' % (source, restored))


def lookup(source):
    """Synchronous fast path used by the render hook: cache or provider DB."""
    with state.lock:
        value = state.cache.get(source)
    if value:
        return value
    provider = active_provider()
    if provider is None:
        return None
    dest, src = current_languages()
    value = provider_lookup(provider, source, dest, src)
    if value:
        with state.lock:
            state.cache[source] = value
    return value


def request(source):
    """Return a translation if instantly available, else queue it (live mode only)."""
    value = lookup(source)
    if value:
        return value
    with state.lock:
        if source in state.failed:
            return None
    if ui_live_active():
        _enqueue(source)
    return None


def lookup_only(source):
    """Database/cache lookup with NO live translation (db_only/prescan modes)."""
    return lookup(source)


# ---------------------------------------------------------------------------
# Prescan integration: feed screen strings into Translator3000's prescan
# ---------------------------------------------------------------------------

_prescan_installed = False
_screen_strings_cache = None


def _expression_strings(expr):
    """Literal strings inside a screen-language expression source string."""
    found = []
    for match in _EXPR_STRING_RE.findall(expr):
        found.append(match[0] or match[1])
    return found


def _ast_strings(node, out, seen_ids):
    """Collect literal strings from a Ren'Py screen AST (SL nodes).

    Screen language nodes keep their literal arguments in .children /
    .args-style attributes depending on Ren'Py version, so this walks every
    attribute defensively instead of assuming one exact node layout.
    """
    if id(node) in seen_ids:
        return
    seen_ids.add(id(node))
    if isinstance(node, text_type):
        out.append(node)
        return
    if isinstance(node, (list, tuple)):
        for item in node:
            _ast_strings(item, out, seen_ids)
        return
    if isinstance(node, dict):
        for item in node.values():
            _ast_strings(item, out, seen_ids)
        return
    children = getattr(node, 'children', None)
    if children:
        _ast_strings(children, out, seen_ids)
    # Screen-language positional/keyword arguments are expression *strings*
    # (e.g. '"Preferences"'), not evaluated values; they live in .positional
    # and .keyword on SLDisplayable/SLBlock nodes.
    for attr in ('args', 'kwargs', 'expressions', 'parameters', 'positional', 'keyword'):
        value = getattr(node, attr, None)
        if value:
            _ast_strings(value, out, seen_ids)
    code = getattr(node, 'code', None)
    if isinstance(code, text_type):
        for match in _EXPR_STRING_RE.findall(code):
            out.append(match[0] or match[1])


def collect_screen_strings():
    """All translatable UI strings statically present in registered screens.

    Game independent: screens come from Ren'Py's own registry, so this sees
    exactly the screens the current game defines - main menu, preferences,
    save/load, custom screens - without knowing any of their names.
    The say screen and Translator3000's own screens are excluded.
    """
    global _screen_strings_cache
    if _screen_strings_cache is not None:
        return _screen_strings_cache
    found = []
    try:
        import renpy.display.screen as screen_module
        registry = getattr(screen_module, 'screens_by_name', None) or {}
        for name, variants in registry.items():
            if _is_protected_screen(name):
                continue
            if not isinstance(variants, dict):
                continue
            for screen in variants.values():
                ast = getattr(screen, 'ast', None)
                if ast is None:
                    continue
                raw = []
                _ast_strings(ast, raw, set())
                for text in raw:
                    if not isinstance(text, text_type):
                        continue
                    # AST positional/keyword values are expression sources
                    # ('"Preferences"'); the rendered string has no quotes.
                    candidates = _expression_strings(text) if text[:1] in ('"', "'") else [text]
                    for candidate in candidates:
                        if looks_translatable(candidate, state.max_chars):
                            found.append(candidate)
    except Exception:
        pass
    # De-duplicated, deterministic order; prescan appends these after the
    # dialogue strings (unknown sort keys land last in install_prescan).
    result = sorted(set(found))
    _screen_strings_cache = result
    log('UI prescan: collected %d screen strings.' % len(result))
    return result


def install_prescan(preparer_class=None):
    """Append UI screen strings to every Translator3000 prescan.

    Wraps Preparer.get_translate_parts - the same hook point
    tr3000_openai.install_prescan uses - so UI strings travel through the
    exact same batching, provider and database as dialogue strings.
    """
    global _prescan_installed
    if _prescan_installed:
        return True
    if preparer_class is None:
        main = main_object()
        preparer = getattr(main, '_translate_preparer', None) if main is not None else None
        preparer_class = type(preparer) if preparer is not None else None
    if preparer_class is None or not hasattr(preparer_class, 'get_translate_parts'):
        log('UI prescan: Preparer.get_translate_parts not found; prescan hook skipped.')
        return False
    original = preparer_class.get_translate_parts
    if getattr(original, '_tr3000_ui_wrapped', False):
        _prescan_installed = True
        return True

    def get_translate_parts(self, strings_array, only_not_translated=True, _use_fast_logic=False):
        try:
            extra = collect_screen_strings()
            if extra:
                merged = list(strings_array) if strings_array is not None else []
                known = set(merged)
                added = [text for text in extra if text not in known]
                if added:
                    log('UI prescan: +%d screen strings.' % len(added))
                    merged.extend(added)
                    strings_array = merged
        except Exception:
            pass
        for part in original(self, strings_array, only_not_translated, _use_fast_logic):
            yield part

    get_translate_parts._tr3000_ui_wrapped = True
    preparer_class.get_translate_parts = get_translate_parts
    _prescan_installed = True
    log('UI prescan hook installed.')
    return True


# ---------------------------------------------------------------------------
# Ren'Py hook
# ---------------------------------------------------------------------------

_orig_set_text = None
_TEXT_CLASS = None


def _is_protected_screen(screen_name):
    if not screen_name:
        return False
    name = screen_name[0] if isinstance(screen_name, (list, tuple)) else screen_name
    name = text_type(name).lower()
    return name == 'say' or name.startswith('translator3000') or name.startswith('tr3000')


def _current_screen_name():
    try:
        import renpy
        screen = renpy.display.screen.current_screen()
        if screen is None:
            return None
        return getattr(screen, 'screen_name', None)
    except Exception:
        return None


def _poke_renpy():
    try:
        import renpy
        renpy.restart_interaction()
    except Exception:
        pass


def _translate_rendered(text):
    """Render-time transform. Gate order (cheap first):

    checkbox OFF        -> original text, always (fresh start included).
    checkbox ON + off   -> original text.
    checkbox ON + db_only/prescan -> translation only if in the database.
    checkbox ON + realtime        -> database first, live fallback.
    """
    if not isinstance(text, text_type):
        return text
    if not state.enabled:
        return text
    mode = translator_mode()
    if mode == MODE_OFF:
        return text
    if not looks_translatable(text, state.max_chars):
        return text
    dest, _src = current_languages()
    if dest and already_target_language(text, dest):
        return text
    if mode == MODE_REALTIME:
        value = request(text)
    else:
        value = lookup_only(text)
    return value if value else text


def install():
    """Patch renpy.text.text.Text.set_text. Idempotent and fail-safe."""
    global _orig_set_text, _TEXT_CLASS
    if state.installed:
        return True
    load_settings()
    try:
        import renpy.text.text as text_module
    except Exception:
        try:
            import renpy
            text_module = renpy.text.text
        except Exception:
            state.status = 'UI translation: Ren\'Py text module not found.'
            return False
    text_class = getattr(text_module, 'Text', None)
    if text_class is None or not hasattr(text_class, 'set_text'):
        state.status = 'UI translation: Text.set_text not found in this Ren\'Py version.'
        return False
    original = text_class.set_text

    def set_text(self, text, scope=None, substitute=False, update=True):
        try:
            if state.enabled and translator_mode() != MODE_OFF \
                    and not getattr(self, '_tr3000_ui_locked', False):
                screen_name = _current_screen_name()
                if not _is_protected_screen(screen_name):
                    widget_id = getattr(self, 'id', None)
                    # The say screen is normally already excluded by name;
                    # the id check is a second line of defence for games
                    # that renamed their say screen.
                    if widget_id not in ('what', 'who'):
                        if isinstance(text, (list, tuple)):
                            new_text = [
                                _translate_rendered(part) if isinstance(part, text_type) else part
                                for part in text]
                            if new_text != list(text):
                                text = new_text
                        elif isinstance(text, text_type):
                            translated = _translate_rendered(text)
                            if translated != text:
                                text = translated
        except Exception:
            pass
        return original(self, text, scope, substitute, update)

    text_class.set_text = set_text
    _orig_set_text = original
    _TEXT_CLASS = text_class
    state.installed = True
    state.status = ('UI translation: on, following Translator3000 mode (%s).'
                    % translator_mode()
                    if state.enabled else
                    'UI translation: off (tick the checkbox in OpenAI settings to show UI translations).')
    log('UI translation installed (v%d, enabled=%s, mode=%s).'
        % (VERSION, state.enabled, translator_mode()))
    return True


def uninstall():
    global _orig_set_text, _TEXT_CLASS
    if _TEXT_CLASS is not None and _orig_set_text is not None:
        try:
            _TEXT_CLASS.set_text = _orig_set_text
        except Exception:
            pass
    _orig_set_text = None
    _TEXT_CLASS = None
    state.installed = False
    state.status = 'UI translation: uninstalled.'
