# -*- coding: utf-8 -*-
"""Merge stock Translator3000.rpa with the OpenAI files into one archive."""
import os
import pickle
import zlib

KEY = 0x42424242
HERE = os.path.dirname(os.path.abspath(__file__))
STOCK = os.path.join(HERE, 'Translator3000.rpa')
OUTPUT = os.path.join(HERE, 'build', 'Translator3000-openai.rpa')
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


def pack():
    stock = open(STOCK, 'rb').read()
    line = stock.split(b'\n', 1)[0]
    if not line.startswith(b'RPA-3.0 '):
        raise SystemExit('stock archive is not RPA-3.0')
    index_offset = int(line[8:24], 16)
    key = int(line[25:33], 16)
    if key != KEY:
        raise SystemExit('unexpected stock key')
    index = pickle.loads(zlib.decompress(stock[index_offset:]))
    out_dir = os.path.dirname(OUTPUT)
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)
    with open(OUTPUT, 'wb') as archive:
        archive.write(stock[:index_offset])
        for name in FILES:
            data = open(os.path.join(HERE, name), 'rb').read()
            offset = archive.tell()
            archive.write(data)
            index[name] = [(offset ^ KEY, len(data) ^ KEY, b'')]
        new_index_offset = archive.tell()
        archive.write(zlib.compress(pickle.dumps(index, protocol=2)))
        archive.seek(0)
        archive.write(b'RPA-3.0 %016x %08x\n' % (new_index_offset, KEY))
    print(OUTPUT)
    print('files', len(index), 'bytes', os.path.getsize(OUTPUT))


if __name__ == '__main__':
    pack()
