# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import re
import sys

ENGLISH = {
    'API-ключи': 'API keys',
    'Изменить ключ': 'Change key',
    'Ввести ключ': 'Enter key',
    'Удалить ключ': 'Delete key',
    'Ключ введён': 'Key entered',
    'Ключ не введён': 'Key not entered',
    'Готово': 'Done',
    'Изменить Base URL': 'Change Base URL',
    'Сохранять ключ для текущего пользователя Windows': 'Save key for the current Windows user',
    'OpenAI API оплачивается отдельно. Сохранённый ключ защищён Windows.': 'OpenAI API is billed separately. The saved key is protected by Windows.',
    'Учётная запись ChatGPT': 'ChatGPT account',
    'Войти через ChatGPT': 'Sign in with ChatGPT',
    'Проверить вход': 'Check sign-in',
    'Отменить': 'Cancel',
    'Без API-ключа. Действуют доступные модели и лимиты вашего тарифа, включая Free.': 'No API key required. Available models and limits of your plan apply, including Free.',
    'codex.exe: автоматически': 'codex.exe: automatic',
    'Указать путь к codex.exe': 'Set path to codex.exe',
    'Сохранить настройки': 'Save settings',
    'Выбрать подключение для перевода': 'Select translation connection',
    'OpenAI / ChatGPT — перевод': 'OpenAI / ChatGPT — translation',
    'API-ключ / вход через ChatGPT': 'API key / ChatGPT sign-in',
    'Подключение': 'Connection',
    'ChatGPT: лимиты учётной записи. API: отдельная оплата.': 'ChatGPT: account limits. API: separate billing.',
    'Модель для ': 'Model for ',
    'Доступ к выбранной модели зависит от вашего аккаунта.': 'Access to the selected model depends on your account.',
    'Размышления': 'Reasoning',
    'Без размышлений': 'No reasoning',
    'Лёгкие': 'Low',
    'Средние': 'Medium',
    'Глубокие': 'High',
    'Очень глубокие': 'Extra high',
    'Максимальные': 'Maximum',
    'Предельные': 'Ultra',
    'Пакеты GPT': 'GPT batches',
    'До %d символов': 'Up to %d characters',
    'Сканирование: порядок сцен, целые строки, контекст соседних реплик.': 'Scanning: scene order, complete lines, and context from nearby dialogue.',
    'API получает файл JSON целиком. ChatGPT получает тот же пакет целиком.': 'The API receives the complete JSON file. ChatGPT receives the same complete batch.',
    'Ответ проверяется до последней строки. При обрыве пакет делится автоматически.': 'The response is checked through the last line. Incomplete batches are split automatically.',
    'В живом переводе передаются доступные реплики. Для всей игры запустите предварительное сканирование.': 'Live translation sends available dialogue. Run a prescan to translate the entire game.',
    'Проверка подключения': 'Connection test',
    'Проверить перевод': 'Test translation',
    'Подогнать размер текста': 'Fit text size',
    'OpenAI API — перевод по ключу': 'OpenAI API — translation with an API key',
    'ChatGPT — вход в учётную запись': 'ChatGPT — account sign-in',
    'Выберите подключение и модель, затем проверьте связь.': 'Select a connection and model, then test the connection.',
    'Вход через ChatGPT не проверен.': 'ChatGPT sign-in has not been checked.',
    'Завершите вход в браузере.': 'Complete sign-in in your browser.',
    'Проверка входа...': 'Checking sign-in...',
    'Вход через ChatGPT выполнен.': 'Signed in with ChatGPT.',
    'Не удалось выполнить вход. Проверьте путь к codex.exe.': 'Sign-in failed. Check the path to codex.exe.',
    'Не удалось прочитать настройки OpenAI. Введите ключ заново.': 'Could not read OpenAI settings. Enter the key again.',
    'Настройки сохранены.': 'Settings saved.',
    'Не удалось сохранить настройки OpenAI.': 'Could not save OpenAI settings.',
    'Сначала выберите один из сервисов OpenAI.': 'Select an OpenAI service first.',
    'Проверка связи…': 'Testing connection…',
    'Связь работает: ': 'Connection works: ',
    'Ошибка подключения. Проверьте настройки и доступ к модели.': 'Connection error. Check the settings and model access.',
    'Перевод строк %d–%d из %d; %s, %s.': 'Translating lines %d–%d of %d; %s, %s.',
    'Готово: %d строк, включая последнюю. Теги и переменные проверены.': 'Done: %d lines, including the last one. Tags and variables verified.',
    'OpenAI изменил теги или переменные. Ответ не сохранён.': 'OpenAI changed tags or variables. The response was not saved.',
    'OpenAI добавил разметку. Ответ не сохранён.': 'OpenAI added markup. The response was not saved.',
    'OpenAI изменил порядок тегов. Ответ не сохранён.': 'OpenAI changed the tag order. The response was not saved.',
    'Сохранение ключа поддерживается только в Windows.': 'Saving keys is supported only on Windows.',
    'Windows не смогла обработать сохранённый ключ.': 'Windows could not process the saved key.',
    'Введите ключ OpenAI API в настройках OpenAI.': 'Enter an OpenAI API key in OpenAI settings.',
    'Впишите api_key в общий _translator3000_openai.json Translator3000.': 'Put api_key in the shared Translator3000 _translator3000_openai.json.',
    'Base URL должен начинаться с http:// или https://.': 'Base URL must start with http:// or https://.',
    'Ответ слишком большой; пакет будет разделён.': 'The response is too large; the batch will be split.',
    'OpenAI не завершил перевод. Ответ не сохранён.': 'OpenAI did not complete the translation. The response was not saved.',
    'API не завершил перевод или отказал. Ответ не сохранён.': 'The API did not complete the translation or refused it. The response was not saved.',
    'Ключ OpenAI недействителен.': 'The OpenAI key is invalid.',
    'Лимит запросов или баланс OpenAI исчерпан.': 'The OpenAI request limit or balance is exhausted.',
    'Модель недоступна этому API-аккаунту.': 'The model is unavailable to this API account.',
    'Нет доступа к OpenAI или выбранной модели.': 'No access to OpenAI or the selected model.',
    'Ошибка OpenAI API: HTTP %s.': 'OpenAI API error: HTTP %s.',
    'Не удалось проверить сертификат API. Проверьте Base URL и доверенный сертификат.': 'Could not verify the API certificate. Check Base URL and the trusted certificate.',
    'Нет корректного ответа OpenAI. Проверьте интернет-соединение или Base URL.': 'No valid OpenAI response. Check your internet connection or Base URL.',
    'Codex не найден. Укажите путь к codex.exe в настройках OpenAI.': 'Codex was not found. Set the path to codex.exe in OpenAI settings.',
    'Операция отменена или истекло время ожидания Codex.': 'The operation was cancelled or Codex timed out.',
    'Не удалось запустить codex.exe.': 'Could not start codex.exe.',
    'Нажмите "Войти через ChatGPT" в разделе "OpenAI / ChatGPT — перевод".': 'Click "Sign in with ChatGPT" under "OpenAI / ChatGPT — translation".',
    'Вход не завершён. Повторите вход через ChatGPT.': 'Sign-in is incomplete. Sign in with ChatGPT again.',
    'Лимит ChatGPT/Codex исчерпан. Дождитесь его обновления.': 'The ChatGPT/Codex limit is exhausted. Wait for it to reset.',
    'Codex не выполнил перевод. Проверьте вход и доступ к модели.': 'Codex did not translate the text. Check sign-in and model access.',
    'Неизвестная модель.': 'Unknown model.',
    'Неизвестное подключение или модель OpenAI.': 'Unknown OpenAI connection or model.',
    'Модель отказалась переводить этот текст. Ответ не сохранён.': 'The model refused to translate this text. The response was not saved.',
    'Неполный или некорректный перевод. Ответ не сохранён.': 'Incomplete or invalid translation. The response was not saved.',
    'Перевод отменён.': 'Translation cancelled.',
    'Файл перевода': 'Translation file',
    'Экспорт перевода': 'Export translation',
    'Импорт перевода': 'Import translation',
    'Файл остаётся на этом компьютере. Его можно передать другому человеку.': 'The file stays on this computer. You can give it to another person.',
    'Сначала выберите сервис перевода.': 'Select a translation service first.',
    'Нет перевода для экспорта.': 'There is no translation to export.',
    'Экспорт отменён.': 'Export cancelled.',
    'Импорт отменён.': 'Import cancelled.',
    'Экспортировано %d строк: %s': 'Exported %d lines: %s',
    'Импортировано %d новых строк. Уже было %d.': 'Imported %d new lines. %d were already stored.',
    'Файл перевода пуст или имеет неизвестный формат.': 'The translation file is empty or has an unknown format.',
    'Не найден сервис %s для импорта.': 'The %s service needed for import was not found.',
    'Выбор файла поддерживается только в Windows.': 'Choosing a file is supported only on Windows.',
    'Не удалось открыть окно выбора файла.': 'Could not open the file chooser.',
    'Не удалось экспортировать перевод: %s': 'Could not export the translation: %s',
    'Не удалось импортировать перевод: %s': 'Could not import the translation: %s',
}

def translate(text):
    store = sys.modules.get('store')
    translator = getattr(store, 'translator3000', None)
    gui = getattr(translator, '_gui', None)
    if getattr(gui, 'gui_language', None) not in ('english', 'en'):
        return text
    if text in ENGLISH:
        return ENGLISH[text]
    prefix = 'Связь работает: '
    if text.startswith(prefix):
        return ENGLISH[prefix] + text[len(prefix):]
    for original, english in ENGLISH.items():
        if '%d' not in original and '%s' not in original:
            continue
        pieces = re.split(u'(%d|%s)', original)
        pattern = [u'^']
        for piece in pieces:
            if piece == u'%d':
                pattern.append(u'(\\d+)')
            elif piece == u'%s':
                pattern.append(u'(.*?)')
            else:
                pattern.append(re.escape(piece))
        pattern.append(u'$')
        match = re.match(u''.join(pattern), text)
        if match:
            values = iter(match.groups())
            return re.sub(r'%[ds]', lambda unused: next(values), english)
    return text

def mark(text):
    return '{#notTranslate}' + translate(text)
