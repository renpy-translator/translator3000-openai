
init -999 python:
    import sys as _tr3000_sys
    import types as _tr3000_types
    with renpy.file("tr3000_disable_update.py") as _tr3000_noupdate_file:
        _tr3000_noupdate_source = _tr3000_noupdate_file.read()
    tr3000_noupdate = _tr3000_types.ModuleType("tr3000_disable_update".encode("ascii") if _tr3000_sys.version_info[0] < 3 else "tr3000_disable_update")
    _tr3000_sys.modules["tr3000_disable_update"] = tr3000_noupdate
    exec(compile(_tr3000_noupdate_source, "tr3000_disable_update.py", "exec"), tr3000_noupdate.__dict__)
    del _tr3000_noupdate_source

init -39 python:
    import sys as _tr3000_sys
    import types as _tr3000_types
    with renpy.file("tr3000_ui.py") as _tr3000_ui_file:
        _tr3000_ui_source = _tr3000_ui_file.read()
    tr3000_ui = _tr3000_types.ModuleType("tr3000_ui".encode("ascii") if _tr3000_sys.version_info[0] < 3 else "tr3000_ui")
    _tr3000_sys.modules["tr3000_ui"] = tr3000_ui
    exec(compile(_tr3000_ui_source, "tr3000_ui.py", "exec"), tr3000_ui.__dict__)
    del _tr3000_ui_source
    with renpy.file("tr3000_openai.py") as _tr3000_file:
        _tr3000_source = _tr3000_file.read()
    tr3000_ai = _tr3000_types.ModuleType("tr3000_openai".encode("ascii") if _tr3000_sys.version_info[0] < 3 else "tr3000_openai")
    tr3000_ai.__file__ = "tr3000_openai.py"
    _tr3000_sys.modules["tr3000_openai"] = tr3000_ai
    exec(compile(_tr3000_source, "tr3000_openai.py", "exec"), tr3000_ai.__dict__)
    del _tr3000_source
    tr3000_ai.register()
    if renpy.loadable("tr3000_transfer.py"):
        with renpy.file("tr3000_transfer.py") as _tr3000_transfer_file:
            _tr3000_transfer_source = _tr3000_transfer_file.read()
        tr3000_transfer = _tr3000_types.ModuleType("tr3000_transfer".encode("ascii") if _tr3000_sys.version_info[0] < 3 else "tr3000_transfer")
        _tr3000_sys.modules["tr3000_transfer"] = tr3000_transfer
        exec(compile(_tr3000_transfer_source, "tr3000_transfer.py", "exec"), tr3000_transfer.__dict__)
        del _tr3000_transfer_source
        tr3000_transfer.install()

init -7 python:
    tr3000_ai.install_prescan(_translator3000.Preparer)
    with renpy.file("tr3000_autofit.py") as _tr3000_fit_file:
        _tr3000_fit_source = _tr3000_fit_file.read()
    tr3000_fit = _tr3000_types.ModuleType("tr3000_autofit".encode("ascii") if _tr3000_sys.version_info[0] < 3 else "tr3000_autofit")
    _tr3000_sys.modules["tr3000_autofit"] = tr3000_fit
    exec(compile(_tr3000_fit_source, "tr3000_autofit.py", "exec"), tr3000_fit.__dict__)
    if "tr3000_autofit_button" not in config.overlay_screens:
        config.overlay_screens.append("tr3000_autofit_button")

init 5 python:
    tr3000_fit.install(type(translator3000))
    _tr3000_current_service = translator3000._translationService
    if tr3000_ai.canonical_service(_tr3000_current_service) != _tr3000_current_service:
        translator3000._translationService = tr3000_ai.canonical_service(_tr3000_current_service)
        translator3000._setting["useNoFreezeLogic"] = True

init 9999:
    screen tr3000_autofit_button():
        zorder 101
        if renpy.get_screen("say") is not None and not _menu:
            textbutton "{#notTranslate}Aa":
                id "tr3000_fit_button"
                style "tr3000_autofit_button"
                text_style "tr3000_autofit_button_text"
                xalign 0.99
                yalign 1.0
                yoffset -36
                action Function(tr3000_fit.refit)
                tooltip tr3000_ui.translate("Подогнать размер текста")

    style tr3000_autofit_button is default:
        background None
        hover_background None
        padding (5, 2)

    style tr3000_autofit_button_text is default:
        size 16
        color "#8888"
        hover_color "#cccc"
        outlines []

    screen translator3000_openai_keys():
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        default editing = None
        use translator3000_base_vbox_in_window(Function(tr3000_ai.settings.save), spacing=_translator3000_gui.resize_from_1080(20), background=None):
            label tr3000_ui.mark('API-ключи')
            window:
                has vbox
                label "{#notTranslate}OpenAI API"
                textbutton "{#notTranslate}" + (tr3000_ui.translate("Изменить ключ") if tr3000_ai.settings.key else tr3000_ui.translate("Ввести ключ")):
                    id "openai_edit_key"
                    action SetScreenVariable("editing", "key")
                textbutton tr3000_ui.mark('Удалить ключ'):
                    id "openai_delete_key"
                    sensitive bool(tr3000_ai.settings.key)
                    action (Function(tr3000_ai.settings.forget_key), SetScreenVariable("editing", None))
                text "{#notTranslate}" + (tr3000_ui.translate("Ключ введён") if tr3000_ai.settings.key else tr3000_ui.translate("Ключ не введён"))
                if editing == "key":
                    input:
                        id "openai_key_input"
                        value FieldInputValue(tr3000_ai.settings, "key")
                        copypaste True
                        length 512
                        exclude "\r\n "
                    textbutton tr3000_ui.mark('Готово'):
                        id "openai_key_done"
                        action (SetScreenVariable("editing", None), Function(tr3000_ai.settings.save))
                text "{#notTranslate}Base URL: " + translator3000.quote(tr3000_ai.settings.base_url)
                textbutton tr3000_ui.mark('Изменить Base URL'):
                    id "openai_edit_base_url"
                    action SetScreenVariable("editing", "base_url")
                if editing == "base_url":
                    input:
                        id "openai_base_url_input"
                        value FieldInputValue(tr3000_ai.settings, "base_url")
                        copypaste True
                        length 2048
                        exclude "\r\n "
                    textbutton tr3000_ui.mark('Готово'):
                        id "openai_base_url_done"
                        action (SetScreenVariable("editing", None), Function(tr3000_ai.settings.save))
                textbutton tr3000_ui.mark('Сохранять ключ для текущего пользователя Windows'):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (ToggleField(tr3000_ai.settings, "remember_key"), Function(tr3000_ai.settings.save))
                text tr3000_ui.mark('OpenAI API оплачивается отдельно. Сохранённый ключ защищён Windows.')
            window:
                has vbox
                label tr3000_ui.mark('Учётная запись ChatGPT')
                textbutton tr3000_ui.mark('Войти через ChatGPT'):
                    sensitive not tr3000_ai.settings.account_busy
                    action Function(tr3000_ai.settings.account_action, True)
                textbutton tr3000_ui.mark('Проверить вход'):
                    sensitive not tr3000_ai.settings.account_busy
                    action Function(tr3000_ai.settings.account_action)
                if tr3000_ai.settings.account_busy:
                    textbutton tr3000_ui.mark('Отменить'):
                        action Function(tr3000_ai.settings.account_cancel.set)
                    timer 0.5 action Function(renpy.restart_interaction) repeat True
                text "{#notTranslate}" + translator3000.quote(tr3000_ui.translate(tr3000_ai.settings.account_status))
                text tr3000_ui.mark('Без API-ключа. Действуют доступные модели и лимиты вашего тарифа, включая Free.')
            window:
                has vbox
                label "{#notTranslate}Codex"
                text "{#notTranslate}" + translator3000.quote(tr3000_ai.settings.codex_path or tr3000_ui.translate("codex.exe: автоматически"))
                textbutton tr3000_ui.mark('Указать путь к codex.exe'):
                    action SetScreenVariable("editing", "codex_path")
                if editing == "codex_path":
                    input:
                        value FieldInputValue(tr3000_ai.settings, "codex_path")
                        copypaste True
                        length 1024
                        exclude "\r\n"
                    textbutton tr3000_ui.mark('Готово'):
                        action (SetScreenVariable("editing", None), Function(tr3000_ai.settings.save))
            textbutton tr3000_ui.mark('Сохранить настройки'):
                action Function(tr3000_ai.settings.save)
            text "{#notTranslate}" + translator3000.quote(tr3000_ui.translate(tr3000_ai.settings.status))
            textbutton tr3000_ui.mark('Выбрать подключение для перевода'):
                action translator3000._gui.ForwardAction("translator3000_openai_preferences")

    screen translator3000_openai_preferences():
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        use translator3000_base_vbox_in_window(Function(tr3000_ai.settings.save), spacing=_translator3000_gui.resize_from_1080(20), background=None):
            if renpy.loadable("tr3000_transfer.py"):
                window:
                    has vbox
                    label tr3000_ui.mark('Файл перевода')
                    textbutton tr3000_ui.mark('Экспорт перевода'):
                        action Function(tr3000_transfer.export_dialog)
                    textbutton tr3000_ui.mark('Импорт перевода'):
                        action Function(tr3000_transfer.import_dialog)
                    text tr3000_ui.mark('Файл остаётся на этом компьютере. Его можно передать другому человеку.')
            label tr3000_ui.mark('OpenAI / ChatGPT — перевод')
            textbutton tr3000_ui.mark('API-ключ / вход через ChatGPT'):
                action translator3000._gui.ForwardAction("translator3000_openai_keys")
            window:
                has vbox
                label tr3000_ui.mark('Подключение')
                for service, spec in tr3000_ai.SERVICES.items():
                    textbutton "{#notTranslate}" + tr3000_ai.service_label(service):
                        id service
                        style "translator3000_radio_button"
                        text_style "translator3000_button_text"
                        selected translator3000._translationService == service
                        action (SetField(translator3000, "_translationService", service), SetDict(translator3000._setting, "useNoFreezeLogic", True), translator3000._gui.ApplySettingAction(True, language_check=True, interrupt_translations=True))
                text tr3000_ui.mark('ChatGPT: лимиты учётной записи. API: отдельная оплата.')
            $ backend = "api" if translator3000._translationService == "openai_api" else "codex"
            window:
                has vbox
                label tr3000_ui.mark('Модель для ') + ("OpenAI API" if backend == "api" else "ChatGPT")
                for model in tr3000_ai.MODELS:
                    textbutton "{#notTranslate}" + tr3000_ai.model_label(model, backend):
                        id "tr3000_model_" + model
                        style "translator3000_radio_button"
                        text_style "translator3000_button_text"
                        selected tr3000_ai.selected_model(backend) == model
                        action (Function(tr3000_ai.set_model, backend, model), translator3000._gui.ApplySettingAction(True, interrupt_translations=True))
                text tr3000_ui.mark('Доступ к выбранной модели зависит от вашего аккаунта.')
            window:
                has vbox
                label tr3000_ui.mark('Размышления')
                for effort in tr3000_ai.effort_options(backend):
                    textbutton "{#notTranslate}" + tr3000_ui.translate(tr3000_ai.EFFORT_LABELS[effort]):
                        style "translator3000_radio_button"
                        text_style "translator3000_button_text"
                        selected getattr(tr3000_ai.settings, backend + "_effort") == effort
                        action (SetField(tr3000_ai.settings, backend + "_effort", effort), Function(tr3000_ai.settings.save), translator3000._gui.ApplySettingAction(True, interrupt_translations=True))
            window:
                has vbox
                label tr3000_ui.mark('Пакеты GPT')
                for size in tr3000_ai.BATCH_SIZES:
                    textbutton tr3000_ui.mark('До %d символов') % size:
                        style "translator3000_radio_button"
                        text_style "translator3000_button_text"
                        selected tr3000_ai.settings.batch_chars == size
                        action (SetField(tr3000_ai.settings, "batch_chars", size), Function(tr3000_ai.settings.save), translator3000._gui.ApplySettingAction(True, interrupt_translations=True))
                text tr3000_ui.mark('Сканирование: порядок сцен, целые строки, контекст соседних реплик.')
                text tr3000_ui.mark('API получает файл JSON целиком. ChatGPT получает тот же пакет целиком.')
                text tr3000_ui.mark('Ответ проверяется до последней строки. При обрыве пакет делится автоматически.')
                text tr3000_ui.mark('В живом переводе передаются доступные реплики. Для всей игры запустите предварительное сканирование.')
            window:
                has vbox
                label tr3000_ui.mark('Проверка подключения')
                textbutton tr3000_ui.mark('Проверить перевод'):
                    sensitive not tr3000_ai.settings.busy and translator3000._translationService in tr3000_ai.SERVICES
                    action Function(tr3000_ai.settings.test, translator3000._translationService)
                text "{#notTranslate}" + translator3000.quote(tr3000_ui.translate(tr3000_ai.settings.status))
                timer 0.5 action Function(renpy.restart_interaction) repeat True

    screen translator3000_user_preferences:
        tag translator3000_screen
        style_prefix "translator3000"
        layer _translator3000.SCREEN_LAYER_NAME
        use translator3000_base_vbox_in_window(translator3000._gui.ApplySettingAction(), first_spacing=None, spacing=_translator3000_gui.resize_from_1080(20), background=None):
            if renpy.loadable("tr3000_transfer.py"):
                textbutton tr3000_ui.mark('Экспорт перевода'):
                    action Function(tr3000_transfer.export_dialog)
                textbutton tr3000_ui.mark('Импорт перевода'):
                    action Function(tr3000_transfer.import_dialog)
            textbutton tr3000_ui.mark('OpenAI / ChatGPT — перевод'):
                action translator3000._gui.ForwardAction("translator3000_openai_preferences")
            textbutton translator3000._gui.translate("Настроить параметры отображаемого текста."):
                action translator3000._gui.ForwardAction(
                    "translator3000_extra_text_preferences"
                )
            textbutton translator3000._gui.translate("Сбросить настройки уведомлений всплывающих окон."):
                action Function(translator3000.popup_windows_handler._reset_stats)
            window:
                has vbox
                for _label, _key, _dest_direction in (
                    ("Исходный язык игры.", "gameLanguage", False),
                    ("Направление перевода.", "directionOfTranslation", True)
                ):
                    window:
                        has vbox
                        label translator3000._gui.translate(_label)
                        if translator3000._setting[_key] is None:
                            text translator3000._gui.translate("Не установлено.")
                        else:
                            text "{{#notTranslate}}{0}".format(
                                translator3000.quote(
                                    translator3000._translator_object.get_lang_name(
                                        translator3000._translationService,
                                        translator3000._setting[_key],
                                        dest_direction=_dest_direction
                                    )
                                ).title()
                            )
                        textbutton translator3000._gui.translate("Сменить."):
                            action translator3000._gui.ForwardAction(
                                "translator3000_set_language",
                                field_name=_key,
                                dest_direction=_dest_direction
                            )
            window:
                has vbox
                label translator3000._gui.translate("Булевые параметры.")
                textbutton translator3000._gui.translate("Режим отладки."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "_debug_mode"),
                        translator3000._gui.ApplySettingAction()
                    )
                textbutton translator3000._gui.translate("Сохранять оригинал в истории."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "originalInHistory"),
                        translator3000._gui.ApplySettingAction()
                    )
                textbutton translator3000._gui.translate("Подставлять переменные из загруженной базы данных."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "addVariablesFromDB"),
                        translator3000._gui.ApplySettingAction(True)
                    )
                textbutton translator3000._gui.translate("Использовать видимую кнопку отображения переводчика."):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "useMinimizeButton"),
                        translator3000._gui.ApplySettingAction()
                    )
                textbutton translator3000._gui.translate("Использовать альтернативный метод сортировки в предварительном сканировании"):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "alternativeSortMethod"),
                        translator3000._gui.ApplySettingAction(True)
                    )
                textbutton translator3000._gui.translate("Показывать альтернативные переводы"):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "displayAlternateTranslations"),
                        translator3000._gui.ApplySettingAction()
                    )
                textbutton translator3000._gui.translate("Использовать режим \"без задержки\""):
                    style "translator3000_check_button"
                    text_style "translator3000_button_text"
                    action (
                        ToggleDict(translator3000._setting, "useNoFreezeLogic"),
                        translator3000._gui.ApplySettingAction()
                    )
            window:
                has vbox
                label translator3000._gui.translate("Показывать оригинал на экране.")
                textbutton translator3000._gui.translate("Отключено."):
                    style "translator3000_radio_button"
                    text_style "translator3000_button_text"
                    if translator3000._setting["workMethod"] != "translateInExtraWindow":
                        action (
                            SetDict(translator3000._setting, "displayOriginal", False),
                            translator3000._gui.ApplySettingAction()
                        )
                textbutton translator3000._gui.translate("Весь текст."):
                    style "translator3000_radio_button"
                    text_style "translator3000_button_text"
                    if translator3000._setting["workMethod"] != "translateInExtraWindow":
                        action (
                            SetDict(translator3000._setting, "displayOriginal", True),
                            translator3000._gui.ApplySettingAction()
                        )
                textbutton translator3000._gui.translate("Только текст в меню выборов."):
                    style "translator3000_radio_button"
                    text_style "translator3000_button_text"
                    if translator3000._setting["workMethod"] != "translateInExtraWindow":
                        action (
                            SetDict(translator3000._setting, "displayOriginal", "choice_menu_only"),
                            translator3000._gui.ApplySettingAction()
                        )
            window:
                has vbox
                label translator3000._gui.translate("Сервис перевода.")
                $ services = translator3000._translator_object.get_available_translator_services()
                for _group, srvs in services:
                    window:
                        has vbox
                        text "{{#notTranslate}}{0}".format(translator3000.quote(_group))
                        for srv in srvs:
                            textbutton "{{#notTranslate}}{0}".format(translator3000.quote(tr3000_ai.service_label(srv))):
                                style "translator3000_radio_button"
                                text_style "translator3000_button_text"
                                action (
                                    SetField(translator3000, "_translationService", srv),
                                    translator3000._gui.ApplySettingAction(True, language_check=True, interrupt_translations=True)
                                )
            window:
                has vbox
                label translator3000._gui.translate("Комбинации клавиш.")
                textbutton translator3000._gui.translate("Показ/скрытие окна переводчика"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "guiShow")
                textbutton translator3000._gui.translate("Включить/выключить перевод в режиме БД"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "databaseTranslateSwitcher")
                textbutton translator3000._gui.translate("Показ/скрытие оригинального текста"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "displayOriginal")
                textbutton translator3000._gui.translate("Показ/скрытие альтернативного перевода"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "displayAlternateTranslations")
                textbutton translator3000._gui.translate("Показ/скрытие окна редактирования текста"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "editWindow")
                textbutton translator3000._gui.translate("Обновить страницу"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "forceRestart")
                textbutton translator3000._gui.translate("Включить/выключить расширение меню выборов"):
                    action translator3000._gui.ForwardAction("translator3000_choice_key_command", "showMenuInfo")
            window:
                has vbox
                label translator3000._gui.translate("Способ работы переводчика.")
                textbutton translator3000._gui.translate("Перевод диалогов и меню."):
                    action (
                        SetDict(translator3000._setting, "workMethod", "dialogueOnly"),
                        translator3000._gui.ApplySettingAction(update_work_method=True)
                    )
                textbutton translator3000._gui.translate("Перевод в отдельном окне."):
                    action (
                        SetDict(translator3000._setting, "workMethod", "translateInExtraWindow"),
                        translator3000._gui.ApplySettingAction(update_work_method=True)
                    )
                textbutton translator3000._gui.translate("Перевод всего текста в игре (Бета)."):
                    action (
                        SetDict(translator3000._setting, "workMethod", "allText"),
                        translator3000._gui.ApplySettingAction(update_work_method=True)
                    )
            if not translator3000._translator_object._get_translator(translator3000._translationService).BROWSER_TRANSLATOR:
                window:
                    has vbox
                    label translator3000._gui.translate("Частота запросов.")
                    if (_translator3000.os.getenv("TRANSLATOR3000_DISABLE_RPM_LIMITS", '0') != '1') and (translator3000._translator_object._get_translator(translator3000._translationService).FORCE_RPM is not None):
                        text translator3000._gui.translate("Для этого сервиса перевода частота фиксированная.")
                    else:
                        if translator3000._setting["requestsFrequency"] is None:
                            text translator3000._gui.translate("Не установлено.")
                        else:
                            text translator3000._gui.translate("{0:.0f} запросов в минуту.").format(
                                float(translator3000._setting["requestsFrequency"])
                            )
                        bar value FieldValue(
                            translator3000._gui,
                            "requests_frequency_pref",
                            offset=10.,
                            range=500.,
                            step=.01
                        )
# Decompiled by unrpyc: https://github.com/CensoredUsername/unrpyc
