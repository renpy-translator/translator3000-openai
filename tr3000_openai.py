# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import base64
import collections
import ctypes
import glob
import io
import json
import os
import re
import shutil
import ssl
import subprocess
import tempfile
import threading
import time
from tr3000_ui import translate as ui_translate
try:
    from urllib.request import Request, urlopen
    from urllib.error import HTTPError, URLError
except ImportError:
    from urllib2 import Request, urlopen, HTTPError, URLError
try:
    text_type = unicode
except NameError:
    text_type = str

MODELS = ('gpt-6.1-sol', 'gpt-6-astra', 'gpt-6-sol', 'gpt-6-luna',
          'gpt-5.6-sol', 'gpt-5.6-terra', 'gpt-5.6-luna', 'gpt-5.5')
MODEL_LABELS = dict((model, model.upper().replace('GPT-', 'GPT-').replace(
    '-SOL', ' Sol').replace('-ASTRA', ' Astra').replace('-LUNA', ' Luna').replace(
    '-TERRA', ' Terra')) for model in MODELS)
EFFORT_LABELS = {'none': 'Без размышлений', 'low': 'Лёгкие', 'medium': 'Средние',
                 'high': 'Глубокие', 'xhigh': 'Очень глубокие',
                 'max': 'Максимальные', 'ultra': 'Предельные'}
BATCH_SIZES = (12000, 48000, 96000)
SCHEMA = {'type': 'object', 'properties': {'translations': {
    'type': 'array', 'items': {'type': 'object', 'properties': {
        'id': {'type': 'integer'}, 'text': {'type': 'string'}},
        'required': ['id', 'text'], 'additionalProperties': False}}},
    'required': ['translations'], 'additionalProperties': False}
INSTRUCTIONS = (
    'Translate each visual-novel line into the target language. Keep names, tone, '
    'profanity, tags, variables and every __TR3000_KEEP_N__ placeholder unchanged. '
    'context_before and context_after are reference only; do not translate them. '
    'Translate every item in lines. Return only a JSON array of [id, text] pairs, '
    'one pair per line, ids unchanged. No markdown or explanation.')
API_PACKET_CHARS = 2500
TOKENS = re.compile(r'\[\[|\{\{|\[(?:[^\[\]]|\[[^\[\]]*\])*\]|\{[^{}]*\}|%\([^)]+\)[#0 +\-]*\d*(?:\.\d+)?[a-zA-Z]|%[#0 +\-]*\d*(?:\.\d+)?[sdif]|%%|__TR3000_KEEP_\d+__')

class TranslationError(RuntimeError):
    pass

def protect(text):
    saved = []
    def replace(match):
        saved.append(match.group(0))
        return '__TR3000_KEEP_%d__' % (len(saved) - 1)
    return TOKENS.sub(replace, text), saved

def restore(text, saved):
    found = re.findall(r'__TR3000_KEEP_(\d+)__', text)
    if collections.Counter(found) != collections.Counter(str(i) for i in range(len(saved))):
        raise TranslationError('OpenAI изменил теги или переменные. Ответ не сохранён.')
    result = re.sub(r'__TR3000_KEEP_(\d+)__', lambda m: saved[int(m.group(1))], text)
    if collections.Counter(TOKENS.findall(result)) != collections.Counter(saved):
        raise TranslationError('OpenAI добавил разметку. Ответ не сохранён.')
    if re.findall(r'\{[^{}]*\}', result) != [s for s in saved if s.startswith('{') and s != '{{']:
        raise TranslationError('OpenAI изменил порядок тегов. Ответ не сохранён.')
    return result

def dpapi(data, decrypt=False):
    if os.name != 'nt':
        raise TranslationError('Сохранение ключа поддерживается только в Windows.')
    class Blob(ctypes.Structure):
        _fields_ = [('size', ctypes.c_ulong), ('data', ctypes.POINTER(ctypes.c_char))]
    buf = ctypes.create_string_buffer(data)
    source = Blob(len(data), ctypes.cast(buf, ctypes.POINTER(ctypes.c_char)))
    target = Blob()
    func = ctypes.windll.crypt32.CryptUnprotectData if decrypt else ctypes.windll.crypt32.CryptProtectData
    func.argtypes = [ctypes.POINTER(Blob), ctypes.c_void_p, ctypes.c_void_p,
                     ctypes.c_void_p, ctypes.c_void_p, ctypes.c_ulong, ctypes.POINTER(Blob)]
    func.restype = ctypes.c_int
    if not func(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(target)):
        raise TranslationError('Windows не смогла обработать сохранённый ключ.')
    try:
        return ctypes.string_at(target.data, target.size)
    finally:
        ctypes.windll.kernel32.LocalFree.argtypes = [ctypes.c_void_p]
        ctypes.windll.kernel32.LocalFree(ctypes.cast(target.data, ctypes.c_void_p))

class Settings(object):
    def __init__(self):
        self.filename = None
        self.key = ''
        self.base_url = 'https://api.openai.com/v1/responses'
        self.api_model = 'gpt-5.6-luna'
        self.codex_model = 'gpt-5.6-luna'
        self.api_effort = 'medium'
        self.codex_effort = 'medium'
        self.batch_chars = 48000
        self.api_concurrency = 4
        self.debug = False
        self.codex_path = ''
        self.remember_key = False
        self.status = 'Выберите подключение и модель, затем проверьте связь.'
        self.busy = False
        self.cert_path = None
        self.account_status = 'Вход через ChatGPT не проверен.'
        self.account_busy = False
        self.account_cancel = threading.Event()
        # Use the normal user Codex profile and its configured provider.
        self.codex_home = os.environ.get('CODEX_HOME') or os.path.join(
            os.path.expanduser('~'), '.codex')

    def account_action(self, login=False):
        if self.account_busy:
            return
        self.account_busy = True
        self.account_cancel.clear()
        self.account_status = 'Завершите вход в браузере.' if login else 'Проверка входа...'
        def work():
            try:
                executable = find_codex()
                env = codex_environment()
                if login:
                    command = [executable, '-c', 'forced_login_method="chatgpt"', 'login']
                    code, unused = run_codex(command, env, self.account_cancel, 300)
                    if code:
                        raise TranslationError('Вход не завершён. Повторите вход через ChatGPT.')
                require_chatgpt(executable, env, self.account_cancel)
                self.account_status = 'Вход через ChatGPT выполнен.'
            except TranslationError as ex:
                self.account_status = text_type(ex)
            except Exception:
                self.account_status = 'Не удалось выполнить вход. Проверьте путь к codex.exe.'
            finally:
                self.account_busy = False
        thread = threading.Thread(target=work)
        thread.daemon = True
        thread.start()

    def load(self, filename):
        self.filename = filename
        if not os.path.isfile(filename):
            return
        try:
            with io.open(filename, encoding='utf-8') as f:
                data = json.load(f)
            self.codex_path = data.get('codex_path', '')
            self.base_url = data.get('base_url', self.base_url).strip() or self.base_url
            self.api_model = data.get('api_model', self.api_model)
            self.codex_model = data.get('codex_model', self.codex_model)
            self.api_effort = data.get('api_effort', 'medium')
            self.codex_effort = data.get('codex_effort', 'medium')
            self.batch_chars = data.get('batch_chars', 48000)
            if self.batch_chars not in BATCH_SIZES:
                self.batch_chars = 48000
            for backend in ('api', 'codex'):
                field = backend + '_effort'
                if getattr(self, field) not in effort_options(backend):
                    setattr(self, field, 'medium')
            if self.api_model not in MODELS:
                self.api_model = MODELS[0]
            if self.codex_model not in MODELS:
                self.codex_model = MODELS[0]
            self.debug = bool(data.get('debug', False))
            try:
                self.api_concurrency = max(1, min(8, int(data.get('api_concurrency', 4))))
            except (TypeError, ValueError):
                self.api_concurrency = 4
            file_key = data.get('api_key') or ''
            if isinstance(file_key, text_type) and file_key.strip():
                self.key = file_key.strip()
                self.remember_key = True
            else:
                encrypted = data.get('encrypted_key', '')
                if encrypted:
                    self.key = dpapi(base64.b64decode(encrypted), True).decode('utf-8')
                    self.remember_key = True
        except Exception:
            self.status = 'Не удалось прочитать настройки OpenAI. Введите ключ заново.'

    def save(self):
        try:
            existing = {}
            if self.filename and os.path.isfile(self.filename):
                try:
                    with io.open(self.filename, encoding='utf-8') as f:
                        loaded = json.load(f)
                    if isinstance(loaded, dict):
                        existing = loaded
                except Exception:
                    existing = {}
            data = {'codex_path': self.codex_path.strip(), 'base_url': self.base_url.strip(),
                    'api_model': self.api_model, 'codex_model': self.codex_model,
                    'api_effort': self.api_effort, 'codex_effort': self.codex_effort,
                    'batch_chars': self.batch_chars, 'debug': bool(self.debug),
                    'api_concurrency': int(self.api_concurrency)}
            file_key = existing.get('api_key')
            if getattr(self, '_clear_file_key', False):
                file_key = ''
                self._clear_file_key = False
            if isinstance(file_key, text_type) and file_key.strip():
                data['api_key'] = file_key.strip()
            elif self.remember_key and self.key.strip() and not isinstance(file_key, text_type):
                data['encrypted_key'] = base64.b64encode(dpapi(self.key.strip().encode('utf-8'))).decode('ascii')
            parent = os.path.dirname(self.filename)
            if not os.path.isdir(parent):
                os.makedirs(parent)
            fd, name = tempfile.mkstemp(prefix='openai-', dir=parent)
            try:
                with os.fdopen(fd, 'wb') as f:
                    f.write(json.dumps(data, ensure_ascii=True, indent=2).encode('utf-8'))
                if os.name == 'nt':
                    move = ctypes.windll.kernel32.MoveFileExW
                    move.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_ulong]
                    if not move(text_type(name), text_type(self.filename), 9):
                        raise OSError('Cannot save settings')
                else:
                    os.rename(name, self.filename)
            finally:
                if os.path.exists(name):
                    os.unlink(name)
            self.status = 'Настройки сохранены.'
        except Exception:
            self.status = 'Не удалось сохранить настройки OpenAI.'

    def forget_key(self):
        self.key = ''
        self.remember_key = False
        self._clear_file_key = True
        self.save()

    def test(self, service):
        if self.busy:
            return
        spec = SERVICES.get(canonical_service(service))
        if not spec:
            self.status = 'Сначала выберите один из сервисов OpenAI.'
            return
        self.busy = True
        self.status = 'Проверка связи…'
        def work():
            try:
                model = selected_model(spec[0])
                result = translate_text('Hello, [player]!', 'ru', 'en', spec[0], model)
                self.status = 'Связь работает: ' + result
            except TranslationError as ex:
                self.status = text_type(ex)
            except Exception:
                self.status = 'Ошибка подключения. Проверьте настройки и доступ к модели.'
            finally:
                self.busy = False
        thread = threading.Thread(target=work)
        thread.daemon = True
        thread.start()

settings = Settings()
SERVICES = collections.OrderedDict([
    ('openai_api', ('api', None)),
    ('openai_chatgpt', ('codex', None)),
])

def canonical_service(service):
    service = (service or '').lower()
    if service in ('openai_api', 'openai_api_gpt6', 'openai_api_sol'):
        return 'openai_api'
    if service in ('openai_chatgpt', 'openai_chatgpt_auto', 'openai_chatgpt_app',
                   'openai_codex_gpt6', 'openai_codex_sol'):
        return 'openai_chatgpt'
    return service

def service_label(service):
    return ui_translate({'openai_api': 'OpenAI API — перевод по ключу',
            'openai_chatgpt': 'ChatGPT — вход в учётную запись'}.get(
                canonical_service(service), service))

def model_label(model, backend):
    return MODEL_LABELS.get(model, model)

def selected_model(backend, model=None):
    return getattr(settings, backend + '_model')

def effort_options(backend, model=None):
    model = model or selected_model(backend)
    levels = ('low', 'medium', 'high', 'xhigh', 'max')
    if model == 'gpt-5.5':
        levels = levels[:-1]
    if backend == 'api' and model not in ('gpt-6.1-sol', 'gpt-6-astra', 'gpt-6-sol'):
        levels = ('none',) + levels
    if backend == 'codex' and model in ('gpt-6.1-sol', 'gpt-6-astra', 'gpt-6-sol',
                                      'gpt-5.6-sol', 'gpt-5.6-terra'):
        levels += ('ultra',)
    return levels

def set_model(backend, model):
    if model not in MODELS:
        raise TranslationError('Неизвестная модель.')
    setattr(settings, backend + '_model', model)
    if getattr(settings, backend + '_effort') not in effort_options(backend, model):
        setattr(settings, backend + '_effort', 'medium')
    settings.save()

def output_budget(prompt, backend):
    effort = getattr(settings, backend + '_effort')
    reserve = {'none': 2048, 'low': 8192, 'medium': 16384,
               'high': 32768, 'xhigh': 49152, 'max': 65536, 'ultra': 65536}[effort]
    return min(128000, max(8192, len(prompt.encode('utf-8')) + reserve))

class TranslationSizeError(TranslationError):
    pass

class TranslationFormatError(TranslationError):
    pass

def apply_file_settings():
    if not settings.filename or not os.path.isfile(settings.filename):
        return
    try:
        with io.open(settings.filename, encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        return
    if not isinstance(data, dict):
        return
    base_url = data.get('base_url')
    if isinstance(base_url, text_type) and base_url.strip():
        settings.base_url = base_url.strip()
    file_key = data.get('api_key')
    if isinstance(file_key, text_type) and file_key.strip():
        settings.key = file_key.strip()
    model = data.get('api_model')
    if model in MODELS:
        settings.api_model = model
    if 'debug' in data:
        settings.debug = bool(data.get('debug'))
    if 'api_concurrency' in data:
        try:
            settings.api_concurrency = max(1, min(8, int(data.get('api_concurrency'))))
        except (TypeError, ValueError):
            pass

def shared_config_dir():
    return os.path.join(os.path.expanduser('~'), "vladya's projects database", 'translator3000')

def use_shared_settings(basedir):
    folder = shared_config_dir()
    if not os.path.isdir(folder):
        os.makedirs(folder)
    shared = os.path.join(folder, '_translator3000_openai.json')
    local = os.path.join(basedir, '_translator3000_openai.json')
    if not os.path.isfile(shared) and os.path.isfile(local):
        shutil.copyfile(local, shared)
    settings.debug_dir = basedir
    settings.load(shared)

_debug_lock = threading.Lock()

def debug_log(event, fields):
    if not getattr(settings, 'debug', False):
        return
    folder = getattr(settings, 'debug_dir', None) or os.path.dirname(settings.filename or '')
    if not folder:
        return
    path = os.path.join(folder, '_translator3000_openai_debug.log')
    lines = ['======== %s %s ========' % (event, time.strftime('%Y-%m-%d %H:%M:%S'))]
    for name in ('model', 'endpoint', 'source', 'target', 'lines', 'packets', 'batch_chars',
                 'elapsed_ms', 'attempt', 'input_tokens', 'output_tokens', 'token_source',
                 'instruction_chars', 'packet_chars', 'sent_chars', 'output_chars', 'error'):
        if fields.get(name) is not None:
            lines.append('%s: %s' % (name, fields[name]))
    for name in ('source_text', 'sent', 'output'):
        if fields.get(name) is not None:
            lines.append('-------- %s --------' % name)
            lines.append(text_type(fields[name]))
    text = re.sub(r'sk-[A-Za-z0-9_\-]{8,}', '[redacted]', '\n'.join(lines) + '\n\n')
    with _debug_lock:
        parent = os.path.dirname(path)
        if parent and not os.path.isdir(parent):
            os.makedirs(parent)
        with io.open(path, 'a', encoding='utf-8') as handle:
            handle.write(text)

def usage_counts(result):
    usage = result.get('usage') if isinstance(result, dict) else None
    if not isinstance(usage, dict):
        return None, None, 'missing'
    incoming = usage.get('prompt_tokens', usage.get('input_tokens'))
    outgoing = usage.get('completion_tokens', usage.get('output_tokens'))
    return incoming, outgoing, 'api'

def unwrap_model_text(text):
    text = (text or '').strip()
    fenced = re.match(r'^```(?:json)?\s*(.*?)\s*```$', text, re.S)
    if fenced:
        text = fenced.group(1).strip()
    return text

def api_response(prompt, model, cancel):
    apply_file_settings()
    model = settings.api_model if settings.api_model in MODELS else model
    key = settings.key.strip() or os.environ.get('OPENAI_API_KEY', '').strip()
    if not key:
        raise TranslationError('Впишите api_key в общий _translator3000_openai.json Translator3000.')
    endpoint = settings.base_url.strip() or 'https://api.openai.com/v1/responses'
    if not re.match(r'^https?://', endpoint, re.I):
        raise TranslationError('Base URL должен начинаться с http:// или https://.')
    endpoint_key = endpoint.lower().rstrip('/')
    is_completions = endpoint_key.endswith('/completions') and not endpoint_key.endswith('/chat/completions')
    is_chat = (not is_completions) and ('/chat/completions' in endpoint_key or 'polza.ai' in endpoint_key)
    if is_chat and not endpoint_key.endswith('/chat/completions'):
        endpoint = endpoint.rstrip('/') + '/chat/completions'
    if is_completions:
        data = {'model': model, 'prompt': INSTRUCTIONS + '\n\n' + prompt,
                'max_tokens': min(8192, output_budget(prompt, 'api')), 'temperature': 0}
    elif is_chat:
        data = {'model': model, 'messages': [
            {'role': 'system', 'content': INSTRUCTIONS}, {'role': 'user', 'content': prompt}],
            'reasoning_effort': settings.api_effort,
            'max_completion_tokens': output_budget(prompt, 'api'),
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': 'translation', 'strict': True, 'schema': SCHEMA}}}
    else:
        if 'api.openai.com' in endpoint_key:
            data = {'model': model, 'store': False, 'instructions': INSTRUCTIONS, 'input': [
                        {'role': 'user', 'content': [
                            {'type': 'input_text', 'text': 'Translate the complete attached packet.'},
                            {'type': 'input_file', 'filename': 'translation_packet.json',
                             'file_data': 'data:application/json;base64,' + base64.b64encode(
                                 prompt.encode('utf-8')).decode('ascii')}]}],
                    'reasoning': {'effort': settings.api_effort},
                    'max_output_tokens': output_budget(prompt, 'api'),
                    'text': {'format': {'type': 'json_schema', 'name': 'translation',
                                        'strict': True, 'schema': SCHEMA}}}
        else:
            data = {'model': model, 'store': False,
                    'input': INSTRUCTIONS + '\n\n' + prompt,
                    'max_output_tokens': min(4096, output_budget(prompt, 'api'))}
    request = Request(endpoint,
                      json.dumps(data).encode('utf-8'),
                      {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    cafile = settings.cert_path if settings.cert_path and os.path.isfile(settings.cert_path) else None

    def open_api():
        try:
            return urlopen(request, timeout=90, context=ssl.create_default_context(cafile=cafile))
        except URLError as ex:
            reason = getattr(ex, 'reason', None)
            if isinstance(reason, ssl.SSLError) or 'CERTIFICATE_VERIFY_FAILED' in str(ex):
                return urlopen(request, timeout=90, context=ssl._create_unverified_context())
            raise

    for attempt in range(3):
        if cancel.is_set():
            raise TranslationError('Перевод отменён.')
        started = time.time()
        result = None
        output_text = None
        error_text = None
        try:
            response = open_api()
            try:
                result = json.loads(response.read().decode('utf-8'))
            finally:
                response.close()
            if is_completions or is_chat:
                choice = result['choices'][0]
                if choice.get('finish_reason') == 'length':
                    raise TranslationSizeError('Ответ слишком большой; пакет будет разделён.')
                if is_completions:
                    output_text = unwrap_model_text(choice.get('text') or (choice.get('message') or {}).get('content') or '')
                elif choice.get('finish_reason') != 'stop' or choice['message'].get('refusal'):
                    raise TranslationError('API не завершил перевод или отказал. Ответ не сохранён.')
                else:
                    output_text = unwrap_model_text(choice['message']['content'])
            elif result.get('status') == 'incomplete' and (result.get('incomplete_details') or {}).get('reason') == 'max_output_tokens':
                raise TranslationSizeError('Ответ слишком большой; пакет будет разделён.')
            elif result.get('status') != 'completed':
                raise TranslationError('OpenAI не завершил перевод. Ответ не сохранён.')
            else:
                content = [c for item in result.get('output', []) for c in item.get('content', [])]
                if any(c.get('type') == 'refusal' for c in content):
                    raise TranslationError('Модель отказалась переводить этот текст. Ответ не сохранён.')
                output_text = ''.join(c.get('text', '') for c in content if c.get('type') == 'output_text')
            return output_text
        except TranslationError as ex:
            error_text = text_type(ex)
            raise
        except HTTPError as ex:
            status = ex.code
            retry = ex.headers.get('Retry-After', '')
            detail = ''
            try:
                detail = ex.read().decode('utf-8', 'replace')
            except Exception:
                detail = ''
            ex.close()
            detail = re.sub(r'(sk-|Bearer )[A-Za-z0-9_\-\.]{8,}', '[redacted]', detail)
            detail = ' '.join(detail.split())[:180]
            if status in (408, 499):
                error_text = 'HTTP %s' % status
                raise TranslationSizeError('Ответ оборван по таймауту. Пакет будет разделён.')
            if status in (429, 500, 502, 503, 504) and attempt < 2:
                error_text = 'HTTP %s' % status
                try:
                    delay = min(20, max(1, float(retry)))
                except ValueError:
                    delay = 2 ** (attempt + 1)
                cancel.wait(delay)
                continue
            messages = {401: 'Ключ OpenAI недействителен.', 403: 'Нет доступа к OpenAI или выбранной модели.',
                        404: 'Модель недоступна этому API-аккаунту.', 429: 'Лимит запросов или баланс OpenAI исчерпан.'}
            message = messages.get(status, 'Ошибка OpenAI API: HTTP %s.' % status)
            if detail:
                message = '%s %s' % (message, detail)
            error_text = message
            raise TranslationError(message)
        except ssl.SSLError:
            error_text = 'SSL'
            raise TranslationError('Не удалось проверить сертификат API. Проверьте Base URL и доверенный сертификат.')
        except (URLError, IOError, ValueError, KeyError, TypeError) as ex:
            detail = ' '.join(str(ex).split())[:180]
            error_text = detail
            if 'timed out' in detail.lower():
                raise TranslationSizeError('Ответ оборван по таймауту. Пакет будет разделён.')
            raise TranslationError('Нет корректного ответа OpenAI. Проверьте интернет-соединение или Base URL. ' + detail)
        finally:
            sent = prompt
            if isinstance(data.get('input'), text_type):
                sent = data['input']
            elif isinstance(data.get('prompt'), text_type):
                sent = data['prompt']
            incoming, outgoing, token_source = usage_counts(result)
            debug_log('api', {
                'model': model, 'endpoint': endpoint, 'attempt': attempt + 1,
                'elapsed_ms': int((time.time() - started) * 1000),
                'input_tokens': incoming, 'output_tokens': outgoing, 'token_source': token_source,
                'instruction_chars': len(INSTRUCTIONS), 'packet_chars': len(prompt),
                'sent_chars': len(sent), 'output_chars': len(output_text or ''),
                'error': error_text, 'source_text': prompt, 'sent': sent, 'output': output_text})


def find_codex():
    if settings.codex_path.strip():
        candidates = [settings.codex_path.strip().strip('"')]
    else:
        candidates = [os.path.join(folder, 'codex.exe') for folder in os.environ.get('PATH', '').split(os.pathsep)]
        local = os.environ.get('LOCALAPPDATA', os.path.expanduser('~/AppData/Local'))
        candidates += sorted(glob.glob(os.path.join(local, 'OpenAI', 'Codex', 'bin', '*', 'codex.exe')),
                             key=os.path.getmtime, reverse=True)
        npm = os.path.join(os.environ.get('APPDATA', ''), 'npm', 'node_modules', '@openai', 'codex')
        candidates += glob.glob(os.path.join(npm, 'node_modules', '@openai', 'codex-win32-*',
                                            'vendor', '*', 'codex', 'codex.exe'))
        candidates += glob.glob(os.path.join(npm, 'vendor', '*', 'codex', 'codex.exe'))
    for candidate in candidates:
        if os.path.isfile(candidate) and candidate.lower().endswith('.exe'):
            return os.path.abspath(candidate)
    raise TranslationError('Codex не найден. Укажите путь к codex.exe в настройках OpenAI.')

OPENAI_LOGIN_BASE = 'https://api.openai.com/v1'

def codex_environment():
    env = os.environ.copy()
    for key in list(env):
        if key.startswith('CODEX_THREAD') or key in (
                'CODEX_INTERNAL_ORIGINATOR_OVERRIDE', 'OPENAI_API_KEY', 'OPENAI_BASE_URL'):
            env.pop(key, None)
    # ChatGPT login must not inherit the custom API base URL from settings.
    env['OPENAI_BASE_URL'] = OPENAI_LOGIN_BASE
    env['CODEX_HOME'] = settings.codex_home
    if text_type is not str:
        encoding = 'mbcs' if os.name == 'nt' else 'utf-8'
        env = dict((k.encode(encoding) if isinstance(k, text_type) else k,
                    v.encode(encoding) if isinstance(v, text_type) else v)
                   for k, v in env.items())
    return env


def run_codex(command, env, cancel, timeout, work=None, prompt=None):
    process = None
    try:
        with tempfile.TemporaryFile() as output:
            process = subprocess.Popen(command, cwd=work or settings.codex_home, env=env,
                                       shell=False, stdin=subprocess.PIPE,
                                       stdout=output, stderr=output,
                                       creationflags=0x08000000 if os.name == 'nt' else 0)
            if prompt is not None:
                process.stdin.write(prompt.encode('utf-8'))
            process.stdin.close()
            deadline = time.time() + timeout
            while process.poll() is None:
                if cancel.wait(0.1) or time.time() > deadline:
                    raise TranslationError('Операция отменена или истекло время ожидания Codex.')
            output.seek(0)
            return process.returncode, output.read().decode('utf-8', 'replace')
    except OSError:
        raise TranslationError('Не удалось запустить codex.exe.')
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()


def require_chatgpt(executable, env, cancel):
    code, output = run_codex([executable, 'login', 'status'], env, cancel, 20)
    if code or 'logged in using chatgpt' not in output.lower():
        raise TranslationError('Нажмите "Войти через ChatGPT" в разделе "OpenAI / ChatGPT — перевод".')


def codex_response(prompt, model, cancel):
    executable = find_codex()
    env = codex_environment()
    require_chatgpt(executable, env, cancel)
    work = tempfile.mkdtemp(prefix='tr3000-codex-')
    try:
        schema_file = os.path.join(work, 'schema.json')
        result_file = os.path.join(work, 'result.json')
        with io.open(schema_file, 'w', encoding='utf-8') as f:
            f.write(text_type(json.dumps(SCHEMA)))
        command = [executable, 'exec', '--ephemeral', '--ignore-user-config',
                   '-c', 'forced_login_method="chatgpt"',
                   '-c', 'openai_base_url="%s"' % OPENAI_LOGIN_BASE,
                   '-c', 'model_reasoning_effort="%s"' % settings.codex_effort,
                   '-c', 'project_doc_max_bytes=0', '-c', 'web_search="disabled"',
                   '-c', 'features.memories=false',
                   '--skip-git-repo-check', '--sandbox', 'read-only',
                   '-c', 'approval_policy="never"', '-c', 'features.shell_tool=false',
                   '-c', 'features.multi_agent=false',
                   '--color', 'never', '--output-schema', schema_file,
                   '--output-last-message', result_file, '-']
        if model is not None:
            command[2:2] = ['-m', model]
        packet_file = os.path.join(work, 'translation_packet.json')
        with io.open(packet_file, 'w', encoding='utf-8') as f:
            f.write(text_type(prompt))
        code, output = run_codex(command, env, cancel, 600, work, INSTRUCTIONS + '\n' + prompt)
        if code or not os.path.isfile(result_file):
            if any(word in output.lower() for word in ('usage limit', 'rate limit', 'quota')):
                raise TranslationError('Лимит ChatGPT/Codex исчерпан. Дождитесь его обновления.')
            raise TranslationError('Codex не выполнил перевод. Проверьте вход и доступ к модели.')
        with io.open(result_file, encoding='utf-8') as f:
            return f.read()
    finally:
        try:
            shutil.rmtree(work)
        except OSError:
            pass

def split_packets(originals, limit):
    packets, current, size = [], [], 0
    for index, line in enumerate(originals):
        line_size = len(line) + 3
        if current and size + line_size > limit:
            packets.append(current)
            current, size = [], 0
        current.append((index, line))
        size += line_size
    if current:
        packets.append(current)
    return packets

def install_prescan(preparer_class):
    original_parts = preparer_class.get_translate_parts

    def ordered_parts(self, strings_array, only_not_translated=True, _use_fast_logic=False):
        service = canonical_service(self._translator._translationService)
        if service not in SERVICES:
            for part in original_parts(self, strings_array, only_not_translated, _use_fast_logic):
                yield part
            return
        mappings = [value for name, value in vars(self).items()
                    if name.endswith('__sort_keys_mapping') and isinstance(value, dict)]
        mapping = mappings[0] if mappings else {}
        def order_key(value):
            key = mapping.get(value)
            if key and len(key) in (3, 4):
                priority = key[1] if len(key) == 4 else 0
                return (key[0], text_type(key[-2]), int(key[-1]), priority, value)
            return (2, '', 0, 0, value)
        rows = sorted(set(strings_array), key=order_key)
        if only_not_translated:
            rows = [row for row in rows if self._need_translate(row)]
        provider = self._translator._translator_object._get_translator(service)
        provider._openai_context = []
        current, size, scene = [], 0, None
        for row in rows:
            key = order_key(row)
            next_scene = key[:2]
            row_size = len(row) + 3
            if current and (size + row_size > settings.batch_chars or next_scene != scene):
                yield '\n\n\n'.join(current)
                current, size = [], 0
            if next_scene != scene:
                provider._openai_context = []
            scene = next_scene
            current.append(row)
            size += row_size
        if current:
            yield '\n\n\n'.join(current)

    preparer_class.get_translate_parts = ordered_parts

def looks_like_ui(text):
    stripped = text.strip()
    if not stripped or (stripped.startswith('(') and stripped.endswith(')')):
        return True
    if stripped.startswith('%') or '%(' in stripped:
        return True
    letters = 0
    for ch in stripped:
        if ch.isalpha():
            letters += 1
    return letters < 3


def neighbor_lines(originals, start, end):
    sample = originals[start:end]
    if sample and sum(1 for line in sample if looks_like_ui(line)) * 2 >= len(sample):
        return [], []
    before, after = [], []
    index = start - 1
    while index >= 0 and len(before) < 2:
        if not looks_like_ui(originals[index]):
            before.append(originals[index])
        index -= 1
    before.reverse()
    index = end
    while index < len(originals) and len(after) < 2:
        if not looks_like_ui(originals[index]):
            after.append(originals[index])
        index += 1
    return before, after


def parse_rows(response):
    data = json.loads(response)
    if isinstance(data, dict):
        data = data.get('translations')
    if not isinstance(data, list):
        raise ValueError()
    rows = []
    for row in data:
        if isinstance(row, dict):
            rows.append((row.get('id'), row.get('text')))
        elif isinstance(row, (list, tuple)) and len(row) == 2:
            rows.append((row[0], row[1]))
        else:
            raise ValueError()
    return rows


def translate_text(text, dest, src, backend, model, cancel=None, context_before=None):
    cancel = cancel or threading.Event()
    if backend not in ('api', 'codex') or model not in MODELS:
        raise TranslationError('Неизвестное подключение или модель OpenAI.')
    originals = text.split('\n\n\n')
    translated = {}
    result_lock = threading.Lock()
    limit = API_PACKET_CHARS if backend == 'api' else settings.batch_chars
    packets = split_packets(originals, limit)
    workers = 1
    if backend == 'api' and len(packets) > 1:
        workers = max(1, min(len(packets), int(settings.api_concurrency or 4)))
    started = time.time()
    debug_log('start', {
        'model': model, 'source': src, 'target': dest, 'lines': len(originals),
        'packets': len(packets), 'batch_chars': limit, 'api_concurrency': workers,
        'packet_chars': len(text), 'source_text': text})

    def request_packet(packet, depth=0):
        if cancel.is_set():
            raise TranslationError('Перевод отменён.')
        protected = dict((index, protect(line)) for index, line in packet)
        start, end = packet[0][0], packet[-1][0] + 1
        before, after = neighbor_lines(originals, start, end)
        payload = {'source_language': src, 'target_language': dest,
                   'context_before': before, 'context_after': after,
                   'lines': [{'id': index, 'text': protected[index][0]}
                             for index, line in packet]}
        prompt = json.dumps(payload, ensure_ascii=False)
        settings.status = 'Перевод строк %d–%d из %d; %s, %s.' % (
            start + 1, end, len(originals), model_label(model, backend),
            EFFORT_LABELS[getattr(settings, backend + '_effort')])
        try:
            response = (api_response if backend == 'api' else codex_response)(prompt, model, cancel)
            if cancel.is_set():
                raise TranslationError('Перевод отменён.')
            try:
                rows = parse_rows(response)
                if len(rows) != len(packet):
                    raise ValueError()
                by_id = {}
                for index, value in rows:
                    if isinstance(index, bool) or not isinstance(index, int) or index in by_id:
                        raise ValueError()
                    if index not in protected or not isinstance(value, text_type):
                        raise ValueError()
                    original = originals[index]
                    if (original.strip() and not value.strip()) or '\n' in value or '\r' in value:
                        raise ValueError()
                    by_id[index] = restore(value, protected[index][1])
                if set(by_id) != set(protected):
                    raise ValueError()
            except (ValueError, KeyError, TypeError):
                raise TranslationFormatError('Неполный или некорректный перевод. Ответ не сохранён.')
        except (TranslationSizeError, TranslationFormatError):
            if len(packet) < 2 or depth >= 12:
                raise
            middle = len(packet) // 2
            request_packet(packet[:middle], depth + 1)
            request_packet(packet[middle:], depth + 1)
            return
        with result_lock:
            translated.update(by_id)

    if workers == 1:
        for packet in packets:
            request_packet(packet)
    else:
        queue = list(packets)
        failures = []

        def worker():
            while not cancel.is_set():
                with result_lock:
                    if not queue:
                        return
                    packet = queue.pop(0)
                try:
                    request_packet(packet)
                except Exception as ex:
                    with result_lock:
                        failures.append(ex)
                    return

        pool = [threading.Thread(target=worker) for _ in range(workers)]
        for thread in pool:
            thread.daemon = True
            thread.start()
        for thread in pool:
            thread.join()
        if failures:
            raise failures[0]
    if cancel.is_set():
        raise TranslationError('Перевод отменён.')
    if len(translated) != len(originals):
        raise TranslationError('Перевод неполный. Ответ не сохранён.')
    debug_log('done', {
        'model': model, 'source': src, 'target': dest, 'lines': len(originals),
        'elapsed_ms': int((time.time() - started) * 1000),
        'output_chars': sum(len(translated[index]) for index in translated),
        'output': '\n\n\n'.join(translated[index] for index in range(len(originals)))})
    settings.status = 'Готово: %d строк, включая последнюю. Теги и переменные проверены.' % len(originals)
    return '\n\n\n'.join(translated[index] for index in range(len(originals)))

def register():
    from _translator3000 import translator, translator_abstract, lang_codes, _paths, LOGGER
    translator.Translator.alias_mapping.update({
        'openai_chatgpt': ('openai_chatgpt_auto', 'openai_chatgpt_app',
                          'openai_codex_gpt6', 'openai_codex_sol'),
        'openai_api': ('openai_api_gpt6', 'openai_api_sol')})
    for service in list(translator.Translator.CLASSES):
        if service.startswith('openai_'):
            translator.Translator.CLASSES.pop(service)
    use_shared_settings(_paths.RENPY_BASEDIR)
    settings.cert_path = _paths.CERT_PATH
    def make_provider(service, backend, model):
        folder = 'OpenAI_' + backend + '_contextual_v2'
        class OpenAITranslator(translator_abstract.TranslatorAbstract):
            TRANSLATOR_GROUP = 'OpenAI'
            BROWSER_TRANSLATOR = False
            SYMB_LIMIT = 96001
            FORCE_RPM = None
            single_instance = None
            is_initialized = False
            DATABASE_FN = os.path.join(_paths.TRANSLATIONS_DB_DIR, folder, 'translations.dbformat')
            LOCAL_DATABASE_FN = os.path.join(_paths.LOCAL_DATABASE_FOLDER, folder, 'translations.dbformat')
            IMPORT_TRANSLATIONS_DIR = None

            def __init__(self, setting_dict=None, multi_setting=None):
                if self.is_initialized:
                    return
                self._openai_cancel = threading.Event()
                self._openai_context = []
                self._openai_language = None
                super(OpenAITranslator, self).__init__(setting_dict, multi_setting)

            def get_lang_code(self, data, dest_direction=True):
                return lang_codes.get_lang_code(data, 'google')

            def get_all_lang_codes(self, dest_direction=True):
                return lang_codes.get_lang_codes_for_translator('google')

            def interrupt_web_translation(self):
                self._openai_cancel.set()

            def _web_translate(self, text, dest, src):
                self._openai_cancel.clear()
                try:
                    if self._openai_language != (dest, src):
                        self._openai_context = []
                        self._openai_language = (dest, src)
                    result = translate_text(text, dest, src, backend, selected_model(backend),
                                            self._openai_cancel, self._openai_context)
                    self._openai_context = [
                        {'source': original, 'translation': translated}
                        for original, translated in zip(text.split('\n\n\n'), result.split('\n\n\n'))][-2:]
                    return result
                except TranslationError as ex:
                    settings.status = text_type(ex)
                    # Stop the current job cleanly. If TranslationError
                    # escapes from the worker, Ren'Py reports an uncaught
                    # exception during scanning or translation.
                    raise translator_abstract.InterruptTranslate()
        OpenAITranslator.LOGGER = LOGGER.getChild('OpenAI.' + backend + '.' + (model or 'account_default'))
        return OpenAITranslator
    for service, (backend, model) in SERVICES.items():
        if service not in translator.Translator.CLASSES:
            translator.Translator.CLASSES[service] = make_provider(service, backend, model)
