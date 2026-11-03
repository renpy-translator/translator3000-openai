# Translator3000 — OpenAI 版

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.ru.md">Русский</a> ·
  <strong>简体中文</strong> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.es.md">Español</a>
</p>

> **Translator3000** 的扩展版，面向 Ren'Py 游戏：新增 OpenAI / ChatGPT 翻译、游戏界面（菜单与设置）翻译、游戏内模式快速切换，以及翻译的导入/导出——全部打包在一个 `.rpa` 文件中。

Translator3000 本身已能用其内置服务实时翻译 Ren'Py 游戏对白。本项目完整保留原版 Translator3000，只在其之上叠加新功能。换到其他游戏时，只需把**一个文件**复制进游戏的 `game` 文件夹。

---

## ✨ 相比原版 Translator3000 新增的功能

### 1. OpenAI / ChatGPT 翻译

- 新增 `openai_api` 提供方：通过 OpenAI API 或 ChatGPT 账号翻译，可自备 API 密钥、Base URL、模型选择（内置 GPT 模型列表）和推理强度等级。
- 大批量翻译，并用占位符保护 Ren'Py 标签（`[变量]`、`{标签}`、`%(...)s`），译文不会破坏游戏语法。
- 挂接到 Translator3000 自身的预扫描入口：提前扫描整个脚本，复用数据库中已有条目，只把新行发去翻译。
- OpenAI 设置在同一台电脑的所有游戏间共享。

### 2. 游戏界面（UI）翻译——无需逐个游戏打补丁

- 预扫描还会从 **Ren'Py 每个已注册的界面**（主菜单、偏好设置、设置、存档/读档等）的 AST 中直接收集文本——不写死任何字符串，因此任何游戏都能用。
- 界面译文与对白存入**同一个数据库**，并由**同一个提供方**生成。
- 显示为可选功能，在设置中勾选后跟随 Translator3000 的模式：**Off** = 原文，**DB only / Prescan** = 仅查数据库，**Realtime** = 缺失时实时翻译。
- 游戏默认始终以原文启动。

### 3. 快速切换模式（Off ↔ DB only）

- 屏幕右上角常驻徽标显示当前模式（`OFF: original`、`Mode: DB only` 等）。
- 点击徽标或按 **Alt+1**（macOS 为 Option+1）即可在 **Off ↔ DB only** 之间即时切换——不离开当前场景或对白行，也不修改设置文件。

### 4. 导出 / 导入翻译

- 设置面板顶部（Ctrl+`）有 **Export translation** / **Import translation** 两个按钮。
- 导出会生成 `translations.tr3000.json`，可用于备份或迁移到另一台电脑。导入只补入缺失的行，本机已有的译文会被保留。

### 5. 附带工具

- 阻止 Translator3000 的强制更新检查（`tr3000_disable_update.py`）。
- 自动缩放译文以适配文本框（`tr3000_autofit.py`）。
- 设置界面的英文标签（`tr3000_ui.py`）。

原版 Translator3000 的一切——Ctrl+` 面板、Off / Prescan / DB-only / Realtime 四种模式、每个游戏独立的翻译数据库——都保持原样工作。新增功能只是挂接到这些现有的点上。

---

## 🚀 安装

1. 构建软件包（见[构建](#-构建)），或直接使用预构建的 `build/Translator3000-openai.rpa`。
2. 把 `Translator3000-openai.rpa` 复制到游戏的 `game` 文件夹。
3. 启动游戏，按 **Ctrl+`** 打开 Translator3000 面板。

> **请勿**同时把原版 `Translator3000.rpa` 或散装的 `.py` / `.rpy` 文件复制进游戏——散装文件会覆盖 RPA 内的文件。Ren'Py 会自动加载 `game` 文件夹中的每个 `.rpa`。

设置页的头两个按钮是 **Export translation** 和 **Import translation**（俄文界面中为 **Экспорт перевода** / **Импорт перевода**）。

---

## 📖 使用方法

### 翻译游戏

1. 按 **Ctrl+`**，配置 OpenAI 提供方（API 密钥、Base URL、模型）。
2. 运行 **Prescan**，把整个脚本（和界面文本）翻译进数据库。
3. 选择显示模式：
   - **DB only** — 显示数据库中已有的译文（预扫描后推荐）。
   - **Realtime** — 缺失的行实时翻译。
   - **Off** — 原文语言。

### 翻译游戏界面

1. 在 OpenAI 设置（Ctrl+`）中勾选 **"Переводить интерфейс игры (меню, настройки, подсказки)"**（"翻译游戏界面：菜单、设置、提示"）。默认**不勾选**。
2. 运行 Prescan——界面字符串会连同对白一起被收集和翻译。
3. 选择 **DB only** 即可看到目标语言的界面；选择 **Off** 则回到原文。

### 快速切换

- **Alt+1**（macOS 为 Option+1）或点击右上角徽标，在 **Off ↔ DB only** 间切换。若当前是 Prescan 或 Realtime 模式，切换会回到 Off。
- 切换走的是 `translator3000._gui` 的 `mode` 属性——与 Ctrl+` 面板按钮完全相同的机制——因此面板和屏幕上所有文本会一起更新。设置文件从不被修改：重启游戏后仍遵循 `modeOnStartup`。

---

## 💾 数据存放位置

正在使用的译文位于用户文件夹：

```
vladya's projects database/translator3000/translations/<游戏存档 ID>/
```

该 ID 来自游戏的 `config.save_directory`。同一游戏、同一服务、同一语言对时，预扫描会复用已有的行，只翻译新行。

共享的 OpenAI 设置（API 密钥、Base URL、选项）为所有游戏只保存一份：

```
vladya's projects database/translator3000/_translator3000_openai.json
```

界面翻译设置（`ui_translate_enabled`、`ui_max_chars`、`ui_debug`）：

```
vladya's projects database/translator3000/_translator3000_ui.json
```

把 `ui_debug` 设为 `true` 可写入界面翻译日志（`_translator3000_ui_debug.log`，位于同一文件夹）。

---

## 🔧 构建

修改源码后，重新构建软件包：

```text
python build_rpa.py
```

该命令把原版 `Translator3000.rpa` 与下列 MOD 文件合并，输出 `build/Translator3000-openai.rpa`：

- `zzz_translator3000_openai.rpyc`
- `tr3000_openai.py`
- `tr3000_ui.py`
- `tr3000_ui_translate.py`
- `tr3000_mode_toggle.py`
- `tr3000_autofit.py`
- `tr3000_disable_update.py`
- `tr3000_transfer.py`

> Ren'Py 不会执行 RPA 内的 `.rpy` 文件。界面脚本必须是编译好的 `zzz_translator3000_openai.rpyc`，且须用**目标游戏**的 Ren'Py 版本编译：把 `.rpy` 放进游戏的 `game` 文件夹，启动游戏一次，再把生成的 `.rpyc` 复制回来。若只改了 `.py` 文件，运行 `python build_rpa.py` 即可。

### 界面模块的工作方式

`tr3000_ui_translate.py` 是独立模块；其加载器位于 `zzz_translator3000_openai.rpy` 内部（没有单独的加载器文件）：

- **预扫描始终扫描界面文本**：字符串从 Ren'Py 所有已注册的界面收集，追加到 Translator3000 的常规预扫描列表，由同一提供方翻译并存入同一数据库。不针对任何游戏写死内容。
- **显示为可选功能**：设置中的勾选框默认关闭，界面显示原文。开启后，显示跟随 Translator3000 的模式——Off 为原文，DB-only/Prescan 仅查数据库，Realtime 再加实时翻译。

`tr3000_mode_toggle.py` 之所以是单独的模块，是因为切换模式不仅影响界面，也影响对白：其中包含徽标界面和 Alt+1 快捷键所用的 `current_mode()`、`set_mode()`、`toggle_db_only()` 与 `mode_label()`。

---

## 🤝 参与贡献

欢迎提交 Issue 和 Pull Request。若某款游戏的界面无法翻译，请开启 `ui_debug`，并把 `_translator3000_ui_debug.log` 中的相关行附在报告里。

## 📄 许可证

Translator3000 与 Ren'Py 归其各自作者所有；本仓库只在其之上添加 OpenAI/UI 扩展层。重新分发前请查阅原项目的条款。
