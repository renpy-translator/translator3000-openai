# -*- coding: utf-8 -*-
# Copy this file into the game folder next to tr3000_openai.py.
# Export and import stay on this computer. Nothing is uploaded.
from __future__ import unicode_literals
import json
import os
import subprocess
import sys

FORMAT_NAME = 'tr3000-transfer'
FORMAT_VERSION = 1


def text_type(value):
    if sys.version_info[0] < 3:
        return unicode(value)
    return str(value)


def native_text(value):
    value = text_type(value)
    if sys.version_info[0] < 3:
        return value.encode('mbcs')
    return value


def read_text(path):
    import io
    with io.open(path, encoding='utf-8') as handle:
        return handle.read()


def write_text(path, value):
    import io
    if not isinstance(value, type(u'')):
        value = value.decode('utf-8')
    with io.open(path, 'w', encoding='utf-8') as handle:
        handle.write(value)


def store():
    return sys.modules.get('store')


def engine():
    main = getattr(store(), 'translator3000', None)
    return getattr(main, '_translator_object', None)


def provider_for(service):
    translator = engine()
    if translator is None or not service:
        return None
    try:
        return translator._get_translator(service)
    except Exception:
        return None


def active_service():
    main = getattr(store(), 'translator3000', None)
    service = getattr(main, '_translationService', None)
    if service is None:
        return None
    try:
        import tr3000_openai
        return tr3000_openai.canonical_service(service)
    except Exception:
        return service


def set_status(message):
    try:
        import tr3000_openai
        tr3000_openai.settings.status = message
    except Exception:
        pass
    try:
        import renpy
        renpy.restart_interaction()
    except Exception:
        pass


def count_rows(database):
    total = 0
    if not isinstance(database, dict):
        return 0
    for texts in database.values():
        if not isinstance(texts, dict):
            continue
        for translations in texts.values():
            if isinstance(translations, dict):
                total += len(translations)
    return total


def clean_database(database):
    result = {}
    if not isinstance(database, dict):
        return result
    for source_lang, texts in database.items():
        if not isinstance(source_lang, type(u'')) or not isinstance(texts, dict):
            continue
        clean_texts = {}
        for source_text, translations in texts.items():
            if not isinstance(source_text, type(u'')) or not isinstance(translations, dict):
                continue
            clean_translations = {}
            for dest_lang, translation in translations.items():
                if isinstance(dest_lang, type(u'')) and isinstance(translation, type(u'')) and translation:
                    clean_translations[dest_lang] = translation
            if clean_translations:
                clean_texts[source_text] = clean_translations
        if clean_texts:
            result[source_lang] = clean_texts
    return result


def snapshot(provider):
    lock = getattr(provider, '_database_lock', None)
    if lock is None:
        return clean_database(getattr(provider, '_database', {}))
    with lock:
        return clean_database(getattr(provider, '_database', {}))


def merge_into(target, incoming):
    added = 0
    kept = 0
    for source_lang, texts in incoming.items():
        language_db = target.setdefault(source_lang, {})
        for source_text, translations in texts.items():
            row = language_db.setdefault(source_text, {})
            for dest_lang, translation in translations.items():
                current = row.get(dest_lang)
                if isinstance(current, type(u'')) and current:
                    kept += 1
                    continue
                row[dest_lang] = translation
                added += 1
    return added, kept


def save_provider(provider, incoming):
    lock = getattr(provider, '_database_lock', None)
    if lock is None:
        added, kept = merge_into(provider._database, incoming)
        local_db = getattr(provider, '_local_db', None)
        if isinstance(local_db, dict):
            merge_into(local_db, incoming)
    else:
        with lock:
            added, kept = merge_into(provider._database, incoming)
            local_db = getattr(provider, '_local_db', None)
            if isinstance(local_db, dict):
                merge_into(local_db, incoming)
    provider.backup_database()
    return added, kept


def pick_path(kind):
    if os.name != 'nt':
        raise RuntimeError('Выбор файла поддерживается только в Windows.')
    if kind == 'save':
        title = 'Export translations'
        filename = 'translations.tr3000.json'
    else:
        title = 'Import translations'
        filename = ''
    env = os.environ.copy()
    env['TR3000_DIALOG_KIND'] = native_text(kind)
    env['TR3000_DIALOG_TITLE'] = native_text(title)
    env['TR3000_DIALOG_NAME'] = native_text(filename)
    if sys.version_info[0] < 3:
        encoded = {}
        for key, value in env.items():
            if isinstance(key, type(u'')):
                key = key.encode('mbcs')
            if isinstance(value, type(u'')):
                value = value.encode('mbcs')
            encoded[key] = value
        env = encoded
    script = u'''
Add-Type -AssemblyName System.Windows.Forms
$owner = New-Object System.Windows.Forms.Form
$owner.TopMost = $true
if ($env:TR3000_DIALOG_KIND -eq 'save') {
  $dialog = New-Object System.Windows.Forms.SaveFileDialog
  $dialog.OverwritePrompt = $true
  $dialog.AddExtension = $true
  $dialog.DefaultExt = 'tr3000.json'
  $dialog.FileName = $env:TR3000_DIALOG_NAME
} else {
  $dialog = New-Object System.Windows.Forms.OpenFileDialog
  $dialog.CheckFileExists = $true
}
$dialog.Title = $env:TR3000_DIALOG_TITLE
$dialog.Filter = 'Translator3000 (*.tr3000.json)|*.tr3000.json|JSON (*.json)|*.json'
if ($dialog.ShowDialog($owner) -eq [System.Windows.Forms.DialogResult]::OK) {
  [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding $false
  [Console]::Out.Write($dialog.FileName)
}
'''
    if isinstance(script, type(u'')):
        script = script.encode('utf-8')
    process = subprocess.Popen(
        ['powershell', '-STA', '-NoProfile', '-Command', '-'],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        creationflags=0x08000000)
    output, _error = process.communicate(script)
    if process.returncode not in (0, None):
        raise RuntimeError('Не удалось открыть окно выбора файла.')
    if not isinstance(output, type(u'')):
        output = output.decode('utf-8', 'replace')
    path = output.strip().strip(u'\ufeff')
    if not path:
        return None
    return path


def export_dialog():
    try:
        service = active_service()
        provider = provider_for(service)
        if provider is None:
            set_status('Сначала выберите сервис перевода.')
            return
        database = snapshot(provider)
        rows = count_rows(database)
        if not rows:
            set_status('Нет перевода для экспорта.')
            return
        path = pick_path('save')
        if not path:
            set_status('Экспорт отменён.')
            return
        payload = {
            'format': FORMAT_NAME,
            'version': FORMAT_VERSION,
            'service': service,
            'records': database,
        }
        text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
        write_text(path, text if isinstance(text, type(u'')) else text.decode('utf-8'))
        set_status('Экспортировано %d строк: %s' % (rows, path))
    except Exception as ex:
        set_status('Не удалось экспортировать перевод: %s' % text_type(ex))


def load_transfer(path):
    data = json.loads(read_text(path))
    if not isinstance(data, dict) or data.get('format') != FORMAT_NAME:
        raise ValueError('Файл перевода пуст или имеет неизвестный формат.')
    if data.get('version') != FORMAT_VERSION:
        raise ValueError('Файл перевода пуст или имеет неизвестный формат.')
    records = clean_database(data.get('records'))
    if not records:
        raise ValueError('Файл перевода пуст или имеет неизвестный формат.')
    service = data.get('service')
    if not isinstance(service, type(u'')) or not service:
        service = active_service()
    return service, records


def import_dialog():
    try:
        path = pick_path('open')
        if not path:
            set_status('Импорт отменён.')
            return
        service, records = load_transfer(path)
        provider = provider_for(service)
        if provider is None:
            set_status('Не найден сервис %s для импорта.' % service)
            return
        added, kept = save_provider(provider, records)
        set_status('Импортировано %d новых строк. Уже было %d.' % (added, kept))
    except Exception as ex:
        set_status('Не удалось импортировать перевод: %s' % text_type(ex))


def install():
    return None
