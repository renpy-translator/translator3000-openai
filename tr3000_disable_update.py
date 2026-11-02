# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
import sys

_PATCHED = False
UPDATE_URL = 'actualVersion.json'


def local_version():
    module = sys.modules.get('_translator3000')
    version = getattr(module, 'VERSION', None)
    numbers = getattr(version, 'version', None) or (0, 0, 0)
    try:
        text = '.'.join(str(int(part)) for part in numbers)
    except (TypeError, ValueError):
        text = '0.0.0'
    return {
        'version': text,
        'versionName': getattr(version, 'name', '') or '',
        'boostyLink': None,
        'patreonLink': None,
        'betaInfo': None,
    }


class LocalVersionResponse(object):
    status_code = 200
    ok = True

    def __init__(self):
        self._payload = local_version()
        self.content = json.dumps(self._payload).encode('utf-8')
        self.text = self.content.decode('utf-8')

    def json(self):
        return local_version()

    def raise_for_status(self):
        return None


def is_update_check(url):
    return UPDATE_URL in str(url or '')


def patch_requests():
    global _PATCHED
    if _PATCHED:
        return
    try:
        from requests.sessions import Session
    except Exception:
        return
    original = Session.request

    def request(self, method, url, *args, **kwargs):
        if is_update_check(url):
            return LocalVersionResponse()
        return original(self, method, url, *args, **kwargs)

    Session.request = request
    _PATCHED = True


def pin_installed_version():
    module = sys.modules.get('_translator3000')
    version = getattr(module, 'VERSION', None)
    if module is None or version is None:
        return
    module.LAST_VERSION = version
    module.LAST_BETA = None


def keep_current_version():
    pin_installed_version()


def install():
    patch_requests()
    pin_installed_version()
    try:
        import renpy
        callbacks = renpy.config.periodic_callbacks
        if keep_current_version not in callbacks:
            callbacks.append(keep_current_version)
    except Exception:
        pass


install()
