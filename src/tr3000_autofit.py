# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import renpy
import renpy.store as store
import renpy.exports as exports

try:
    _basestring = basestring  # noqa: F821 - Python 2 (Ren'Py 7)
except NameError:
    _basestring = str

# Fitted sizes are reusable across Text/style objects. Stock Translator3000
# replaces a translated Text object's style with a fresh copy on every
# interaction restart, so identity-based keys (id(style)) never hit. The
# cache below is keyed by stable *effective* style values instead.
_FIT_CACHE = {}
_FIT_CACHE_LIMIT = 512

# Style properties that can change how Ren'Py lays out text (font size is
# handled separately, as it is the value autofit itself overrides).
_STYLE_ATTRS = (
    'antialias', 'vertical', 'font', 'bold', 'italic', 'hinting',
    'underline', 'strikethrough', 'color', 'black_color', 'kerning',
    'slow_cps', 'slow_cps_multiplier', 'outline_scaling',
    'line_overlap_split', 'first_indent', 'rest_indent', 'language',
    'layout', 'line_spacing', 'line_leading', 'newline_indent',
    'min_width', 'max_width', 'text_align', 'justify', 'adjust_spacing',
    'outlines', 'drop_shadow', 'drop_shadow_color', 'hyperlink_functions',
    'ruby_style', 'altruby_style', 'shaper',
)

_MISSING = '<missing>'


def enabled():
    return store.persistent.tr3000_auto_fit is not False


def refit():
    store.persistent.tr3000_auto_fit = True
    store.persistent.tr3000_fit_revision = (store.persistent.tr3000_fit_revision or 0) + 1
    _FIT_CACHE.clear()
    widget = exports.get_widget('say', 'what')
    if widget is not None:
        widget.kill_layout()
        exports.redraw(widget, 0)
    exports.restart_interaction()


def _freeze(value, depth=0):
    """Convert a style value into a stable, hashable cache component."""
    if value is None or isinstance(value, (bool, int, float, _basestring)):
        return value
    if depth > 6:
        return ('obj', type(value).__name__, id(value))
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(item, depth + 1) for item in value)
    if isinstance(value, dict):
        return tuple((key, _freeze(value[key], depth + 1))
                     for key in sorted(value, key=lambda item: repr(item)))
    if isinstance(value, (set, frozenset)):
        return frozenset(_freeze(item, depth + 1) for item in value)
    return ('obj', type(value).__name__, id(value))


def _style_key(style, depth=0):
    values = []
    try:
        values.append(('prefix', getattr(style, 'prefix', None)))
    except Exception:
        values.append(('prefix', _MISSING))
    for name in _STYLE_ATTRS:
        try:
            value = getattr(style, name)
        except Exception:
            values.append((name, _MISSING))
            continue
        if name in ('ruby_style', 'altruby_style') and value is not None:
            if depth == 0:
                values.append((name, _style_key(value, depth + 1)))
            else:
                values.append((name, getattr(value, 'name', None)))
        else:
            values.append((name, _freeze(value)))
    return tuple(values)


def _text_key(text):
    result = []
    for value in text:
        if isinstance(value, _basestring):
            result.append(value)
        else:
            result.append(('displayable', type(value).__name__, id(value)))
    return tuple(result)


def _int_size(style):
    try:
        return int(style.size)
    except Exception:
        return None


def _style_with_size(style, size):
    new_style = style.copy()
    new_style.size = size
    try:
        prefix = style.prefix
        if prefix and new_style.prefix != prefix:
            new_style.set_prefix(prefix)
    except Exception:
        pass
    return new_style


def install(translator_class):
    if getattr(translator_class, '_tr3000_autofit_installed', False):
        return
    translator_class._tr3000_autofit_installed = True
    original_props = translator_class._get_text_props

    def native_text_props(self):
        props = original_props(self)
        if enabled():
            props.pop('size', None)
        return props

    translator_class._get_text_props = native_text_props
    text_class = renpy.text.text.Text
    original_render = text_class.render

    def fitted_render(self, width, height, st, at):
        marker = store.translator3000.CUSTOM_TAG
        translated = any(isinstance(value, type(marker)) and marker in value.lower()
                         for value in self.text)
        if not enabled() or not translated or self.style.vertical or width <= 0 or height <= 0:
            return original_render(self, width, height, st, at)

        target_width, target_height = width, height
        try:
            dialogue = self is exports.get_widget('say', 'what')
        except Exception:
            dialogue = False
        if dialogue:
            try:
                gui = getattr(store, 'gui', None)
                box_height = getattr(gui, 'textbox_height', height)
                yoffset = getattr(gui, 'dialogue_ypos', 0)
                if isinstance(box_height, (int, float)) and isinstance(yoffset, (int, float)):
                    quick_size = getattr(gui, 'quick_button_text_size', 14)
                    bottom_space = max(8, int(quick_size) + 12)
                    target_height = min(height, max(1, box_height - yoffset - bottom_space))
            except Exception:
                target_height = height

        current_size = _int_size(self.style)
        if not current_size or current_size <= 0:
            return original_render(self, width, height, st, at)

        # The current size may be the game's base size or the size fitted
        # earlier (stock copies the fitted style into the next interaction).
        # Anything else means the style changed externally - take the new
        # size as the base to fit from.
        stored_base = getattr(self, '_tr3000_fit_base_size', None)
        stored_fit = getattr(self, '_tr3000_fit_size', None)
        if stored_base and current_size in (stored_base, stored_fit):
            base_size = stored_base
        else:
            base_size = current_size

        try:
            font_transform = getattr(
                getattr(renpy.game, 'preferences', None), 'font_transform', None)
        except Exception:
            font_transform = None

        try:
            signature = (_text_key(self.text), width, height,
                         target_width, target_height, base_size,
                         _style_key(self.style),
                         getattr(store.persistent, 'tr3000_fit_revision', None),
                         font_transform,
                         getattr(self, 'start', None), getattr(self, 'end', None))
        except Exception:
            return original_render(self, width, height, st, at)

        # Same text/style/box as last time on this very Text object: the
        # layout Ren'Py already cached for it is still valid. Keep the
        # style at the fitted size, but do NOT kill the layout.
        if getattr(self, '_tr3000_fit_signature', None) == signature:
            fitted_size = stored_fit or base_size
            if current_size != fitted_size:
                self.style = _style_with_size(self.style, fitted_size)
            self._tr3000_fit_style = self.style
            return original_render(self, width, height, st, at)

        # Same stable signature fitted before (possibly on another Text or
        # style object): apply the known size with a single render, no
        # measurement pass.
        fitted_size = _FIT_CACHE.get(signature)
        if fitted_size is not None:
            if current_size != fitted_size:
                self.style = _style_with_size(self.style, fitted_size)
                self.kill_layout()
            self._tr3000_fit_base_size = base_size
            self._tr3000_fit_size = fitted_size
            self._tr3000_fit_style = self.style
            self._tr3000_fit_signature = signature
            return original_render(self, width, height, st, at)

        # First time this signature is seen: measure at the base size.
        if current_size != base_size:
            self.style = _style_with_size(self.style, base_size)
            self.kill_layout()
        result = original_render(self, width, height, st, at)
        if result.width <= target_width and result.height <= target_height:
            fitted_size = base_size
        else:
            low, high = 1, base_size - 1
            best = 1
            last_candidate = None
            last_result = None
            while low <= high:
                candidate = (low + high) // 2
                self.style = _style_with_size(self.style, candidate)
                self.kill_layout()
                measured = original_render(self, width, height, st, at)
                last_candidate = candidate
                last_result = measured
                if measured.width <= target_width and measured.height <= target_height:
                    best = candidate
                    low = candidate + 1
                else:
                    high = candidate - 1
            fitted_size = best
            if last_candidate == fitted_size and last_result is not None:
                result = last_result
            else:
                self.style = _style_with_size(self.style, fitted_size)
                self.kill_layout()
                result = original_render(self, width, height, st, at)

        if len(_FIT_CACHE) >= _FIT_CACHE_LIMIT:
            _FIT_CACHE.clear()
        _FIT_CACHE[signature] = fitted_size
        self._tr3000_fit_base_size = base_size
        self._tr3000_fit_size = fitted_size
        self._tr3000_fit_style = self.style
        self._tr3000_fit_signature = signature
        return result

    text_class.render = fitted_render
