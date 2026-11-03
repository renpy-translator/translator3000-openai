# -*- coding: utf-8 -*-
"""Build Translator3000-openai.rpa (stock + add-on) or -addon.rpa (add-on only)."""
import os
import pickle
import sys
import zlib

KEY = 0x42424242
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, 'src')
STOCK = os.path.join(HERE, 'Translator3000.rpa')
OUT_DIR = os.path.join(HERE, 'build')
ADDON = 'build/Translator3000-openai-addon.rpa'
FULL = 'build/Translator3000-openai.rpa'
FILES = [
    'zzz_translator3000_openai.rpyc',
    'tr3000_openai.py',
    'tr3000_ui.py',
    'tr3000_ui_translate.py',
    'tr3000_mode_toggle.py',
    'tr3000_autofit.py',
    'tr3000_disable_update.py',
    'tr3000_transfer.py',
]


def read_files():
    result = []
    for name in FILES:
        data = open(os.path.join(SRC, name), 'rb').read()
        result.append((name, data))
    return result


def write_index(archive, index):
    offset = archive.tell()
    archive.write(zlib.compress(pickle.dumps(index, protocol=2)))
    archive.seek(0)
    archive.write(b'RPA-3.0 %016x %08x\n' % (offset, KEY))


def append_files(archive, index, files):
    for name, data in files:
        offset = archive.tell()
        archive.write(data)
        index[name] = [(offset ^ KEY, len(data) ^ KEY, b'')]


def build_addon(addon_files):
    output = os.path.join(HERE, ADDON)
    index = {}
    with open(output, 'wb') as archive:
        archive.write(b'RPA-3.0 %016x %08x\n' % (0, KEY))
        append_files(archive, index, addon_files)
        write_index(archive, index)
    print(output)
    print('files', len(index), 'bytes', os.path.getsize(output))
    return output


def build_full(addon_files):
    output = os.path.join(HERE, FULL)
    stock = open(STOCK, 'rb').read()
    line = stock.split(b'\n', 1)[0]
    if not line.startswith(b'RPA-3.0 '):
        raise SystemExit('stock archive is not RPA-3.0')
    index_offset = int(line[8:24], 16)
    key = int(line[25:33], 16)
    if key != KEY:
        raise SystemExit('unexpected stock key')
    index = pickle.loads(zlib.decompress(stock[index_offset:]))
    with open(output, 'wb') as archive:
        archive.write(stock[:index_offset])
        append_files(archive, index, addon_files)
        write_index(archive, index)
    print(output)
    print('files', len(index), 'bytes', os.path.getsize(output))
    return output


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else 'full'
    if mode not in ('full', 'addon', 'all'):
        raise SystemExit('usage: python build_rpa.py [full|addon|all]')
    os.makedirs(OUT_DIR, exist_ok=True)
    addon_files = read_files()
    if mode in ('addon', 'all'):
        build_addon(addon_files)
    if mode in ('full', 'all'):
        build_full(addon_files)


if __name__ == '__main__':
    main()
