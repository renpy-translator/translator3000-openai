# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import renpy
import renpy.store as store
import renpy.exports as exports


def enabled():
    return store.persistent.tr3000_auto_fit is not False


def refit():
    store.persistent.tr3000_auto_fit = True
    store.persistent.tr3000_fit_revision = (store.persistent.tr3000_fit_revision or 0) + 1
    widget = exports.get_widget('say', 'what')
    if widget is not None:
        widget.kill_layout()
        exports.redraw(widget, 0)
    exports.restart_interaction()


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
        base_style = getattr(self, '_tr3000_fit_base_style', None)
        fitted_style = getattr(self, '_tr3000_fit_style', None)
        if base_style is None or self.style is not fitted_style:
            base_style = self.style
        target_width, target_height = width, height
        dialogue = self is exports.get_widget('say', 'what')
        if dialogue:
            gui = getattr(store, 'gui', None)
            box_height = getattr(gui, 'textbox_height', height)
            yoffset = getattr(gui, 'dialogue_ypos', 0)
            if isinstance(box_height, (int, float)) and isinstance(yoffset, (int, float)):
                quick_size = getattr(gui, 'quick_button_text_size', 14)
                bottom_space = max(8, int(quick_size) + 12)
                target_height = min(height, max(1, box_height - yoffset - bottom_space))
        signature = (tuple(self.text), width, height, target_height, id(base_style),
                     store.persistent.tr3000_fit_revision)
        if getattr(self, '_tr3000_fit_signature', None) == signature:
            return original_render(self, width, height, st, at)
        self._tr3000_fit_base_style = base_style
        self.style = base_style.copy()
        self._tr3000_fit_style = self.style
        self.kill_layout()
        result = original_render(self, width, height, st, at)
        if result.width > target_width or result.height > target_height:
            low, high = 1, max(1, int(base_style.size))
            best = low
            while low <= high:
                candidate = (low + high) // 2
                self.style = base_style.copy()
                self.style.size = candidate
                self.kill_layout()
                measured = original_render(self, width, height, st, at)
                if measured.width <= target_width and measured.height <= target_height:
                    best = candidate
                    low = candidate + 1
                else:
                    high = candidate - 1
            self.style = base_style.copy()
            self.style.size = best
            self.kill_layout()
            result = original_render(self, width, height, st, at)
        self._tr3000_fit_style = self.style
        self._tr3000_fit_signature = signature
        return result

    text_class.render = fitted_render
