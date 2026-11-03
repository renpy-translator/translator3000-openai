# Translator3000 — OpenAI Edition

<p align="center">
  <strong>English</strong> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.es.md">Español</a>
</p>

> An extension of **Translator3000** for Ren'Py games that adds OpenAI / ChatGPT translation, game UI (menu & settings) translation, an in-game mode toggle, and translation export/import — all packaged into a single `.rpa` file.

Translator3000 already translates Ren'Py game dialogue in real time with its built-in services. This project keeps the original Translator3000 intact and layers new features on top of it. To use it in another game, copy **one file** into the game's `game` folder.

---

## ✨ Features added over stock Translator3000

### 1. OpenAI / ChatGPT translation

- New `openai_api` provider: translate via the OpenAI API or a ChatGPT account, with your own API key, Base URL, model choice (built-in GPT model list) and reasoning-effort level.
- Large-batch translation with Ren'Py tag protection (`[variables]`, `{tags}`, `%(...)s`) via placeholders, so translated lines never break game syntax.
- Hooks into Translator3000's own prescan entry point: the whole script is scanned upfront, existing database entries are reused, and only new lines are sent for translation.
- OpenAI settings are shared across every game on the same machine.

### 2. Game UI translation — no per-game patching

- Prescan also collects text from **every registered Ren'Py screen** (main menu, Preferences, Settings, save/load, …) directly from the screen AST — no hardcoded strings, so it works on any game.
- UI translations are stored in the **same database** as dialogue and produced by the **same provider**.
- Display is opt-in via a checkbox in the settings and follows Translator3000's mode: **Off** = original text, **DB only / Prescan** = database lookups only, **Realtime** = live translation on misses.
- Games always start in the original language by default.

### 3. Quick mode toggle (Off ↔ DB only)

- An always-visible badge in the top-right corner shows the current mode (`OFF: original`, `Mode: DB only`, …).
- Click the badge or press **Alt+1** (Option+1 on macOS) to switch **Off ↔ DB only** instantly — without leaving the current scene or dialogue line, and without touching the settings file.

### 4. Export / import translations

- **Export translation** / **Import translation** buttons at the top of the settings panel (Ctrl+`).
- Export writes `translations.tr3000.json` for backup or moving to another machine. Import only adds missing lines; existing local translations are kept.

### 5. Extras

- Blocks Translator3000's forced update check (`tr3000_disable_update.py`).
- Auto-fits translated text into its frame (`tr3000_autofit.py`).
- English labels for the settings UI (`tr3000_ui.py`).

Everything from stock Translator3000 — the Ctrl+` panel, the Off / Prescan / DB-only / Realtime modes, and the per-game translation database — keeps working unchanged. The additions only hook into those existing points.

---

## 🚀 Installation

1. Build the package (see [Building](#-building)) or take the prebuilt `build/Translator3000-openai.rpa`.
2. Copy `Translator3000-openai.rpa` into the game's `game` folder.
3. Launch the game and press **Ctrl+`** to open the Translator3000 panel.

> **Do not** also copy the stock `Translator3000.rpa` or loose `.py` / `.rpy` files into the game — loose files override files inside the RPA. Ren'Py automatically loads every `.rpa` in the `game` folder.

The first two buttons of the settings page are **Export translation** and **Import translation** (in the Russian UI: **Экспорт перевода** / **Импорт перевода**).

---

## 📖 Usage

### Translating a game

1. Press **Ctrl+`** and configure the OpenAI provider (API key, Base URL, model).
2. Run **Prescan** to translate the full script (and UI text) into the database.
3. Pick a display mode:
   - **DB only** — show translations already in the database (recommended after prescan).
   - **Realtime** — translate missing lines on the fly.
   - **Off** — original language.

### Translating the game UI

1. In the OpenAI settings (Ctrl+`), tick **"Переводить интерфейс игры (меню, настройки, подсказки)"** ("Translate the game interface: menus, settings, hints"). It is **off by default**.
2. Run Prescan — screen strings are collected and translated together with dialogue.
3. Select **DB only** to see UI in the target language; select **Off** to return to the original.

### Quick toggle

- **Alt+1** (Option+1 on macOS) or click the top-right badge to flip **Off ↔ DB only**. If the current mode is Prescan or Realtime, toggling switches to Off.
- Switching goes through the `mode` property of `translator3000._gui` — the exact mechanism the Ctrl+` panel buttons use — so the panel and all on-screen text update together. The settings file is never modified: restarting the game still follows `modeOnStartup`.

---

## 💾 Where data is stored

Translations in use live in the per-user folder:

```
vladya's projects database/translator3000/translations/<game save id>/
```

The id comes from the game's `config.save_directory`. For the same game, service and language pair, prescan reuses existing lines and only translates new ones.

Shared OpenAI settings (API key, Base URL, choices) are stored once for all games:

```
vladya's projects database/translator3000/_translator3000_openai.json
```

UI translation settings (`ui_translate_enabled`, `ui_max_chars`, `ui_debug`):

```
vladya's projects database/translator3000/_translator3000_ui.json
```

Set `ui_debug` to `true` to write a UI translation log (`_translator3000_ui_debug.log`, same folder).

---

## 🔧 Building

After editing the sources, rebuild the package:

```text
python build_rpa.py
```

This merges the stock `Translator3000.rpa` with the mod files below and writes `build/Translator3000-openai.rpa`:

- `zzz_translator3000_openai.rpyc`
- `tr3000_openai.py`
- `tr3000_ui.py`
- `tr3000_ui_translate.py`
- `tr3000_mode_toggle.py`
- `tr3000_autofit.py`
- `tr3000_disable_update.py`
- `tr3000_transfer.py`

> Ren'Py does not execute `.rpy` files inside an RPA. The screen script must be the compiled `zzz_translator3000_openai.rpyc`, built with the **target game's** Ren'Py version: drop the `.rpy` into the game's `game` folder, launch the game once, then copy the generated `.rpyc` back here. Pure `.py` changes only need `python build_rpa.py`.

### How the UI module works

`tr3000_ui_translate.py` is a standalone module; its loader lives inside `zzz_translator3000_openai.rpy` (there is no separate loader file):

- **Prescan always scans UI text**: strings are collected from all registered Ren'Py screens, appended to Translator3000's normal prescan list, translated by the same provider and stored in the same database. Nothing is hardcoded per game.
- **Display is opt-in**: the settings checkbox is off by default, so the UI shows the original language. When enabled, display follows Translator3000's mode — Off = original, DB-only/Prescan = database only, Realtime = plus live translation.

`tr3000_mode_toggle.py` is a separate module because mode switching affects dialogue too, not just the UI: it owns `current_mode()`, `set_mode()`, `toggle_db_only()` and `mode_label()` used by the badge screen and the Alt+1 hotkey.

---

## 🤝 Contributing

Issues and pull requests are welcome. If a game fails to translate its UI, enable `ui_debug` and attach the relevant lines from `_translator3000_ui_debug.log` to your report.

## 📄 License

Translator3000 and Ren'Py are the work of their respective authors; this repository only adds the OpenAI/UI extension layer on top. Check the original projects' terms before redistributing.
