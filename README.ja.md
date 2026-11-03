# Translator3000 — OpenAI エディション

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <strong>日本語</strong> ·
  <a href="README.es.md">Español</a>
</p>

> Ren'Py ゲーム向け **Translator3000** の拡張版です。OpenAI / ChatGPT 翻訳、ゲーム UI（メニュー・設定）の翻訳、ゲーム内でのモード即時切り替え、翻訳のエクスポート/インポートを追加し、2 種類の単体ファイルで提供します：単独版 `Translator3000-openai.rpa`（オリジナル + 拡張）と、オリジナル `Translator3000.rpa` の横に置く小さな `Translator3000-openai-addon.rpa` です。

Translator3000 はもともと内蔵サービスで Ren'Py ゲームの台詞をリアルタイム翻訳します。本プロジェクトはオリジナルの Translator3000 をそのまま保持し、その上に新機能を重ねます。別のゲームで使うには、`.rpa` ファイル 1 つ（同梱済みの単独版、またはオリジナル `Translator3000.rpa` の横に置くアドオン）をそのゲームの `game` フォルダにコピーするだけです。

---

## ✨ オリジナルの Translator3000 に対する追加機能

### 1. OpenAI / ChatGPT 翻訳

- 新しい `openai_api` プロバイダー：OpenAI API またはアカウント ChatGPT で翻訳。API キー、Base URL、モデル選択（内蔵 GPT モデル一覧）、reasoning effort レベルを指定できます。
- 大規模なバッチ翻訳と、プレースホルダーによる Ren'Py タグ保護（`[変数]`、`{タグ}`、`%(...)s`）により、訳文がゲームの構文を壊しません。
- Translator3000 自身のプリススキャン入口にフックします：スクリプト全体を事前にスキャンし、データベースの既存エントリを再利用して、新しい行だけを翻訳に送ります。
- OpenAI の設定は、同じコンピューター上のすべてのゲームで共有されます。

### 2. ゲーム UI の翻訳 — ゲームごとのパッチ不要

- プリスキャンは **Ren'Py に登録されたすべての画面**（メインメニュー、Preferences、Settings、セーブ/ロードなど）から、画面 AST を直接読み取ってテキストを収集します。文字列をハードコードしないため、どのゲームでも動作します。
- UI の訳文は台詞と**同じデータベース**に保存され、**同じプロバイダー**で生成されます。
- 表示は設定のチェックボックスでオプトイン方式。Translator3000 のモードに従います：**Off** = 原文、**DB only / Prescan** = データベース検索のみ、**Realtime** = 未登録時にライブ翻訳。
- ゲームは常にデフォルトで原文で起動します。

### 3. モードの即時切り替え（Off ↔ DB only）

- 画面右上に常時表示されるバッジが現在のモードを示します（`OFF: original`、`Mode: DB only` など）。
- バッジをクリックするか **Alt+1**（macOS は Option+1）を押すと、現在のシーンや台詞の行から離れることなく、設定ファイルにも触れずに **Off ↔ DB only** を即座に切り替えられます。

### 4. 翻訳のエクスポート / インポート

- 設定パネル（Ctrl+`）の先頭にある **Export translation** / **Import translation** ボタン。
- エクスポートで `translations.tr3000.json` を書き出し、バックアップや別マシンへの移行に使えます。インポートは不足分だけを追加し、このマシンにある既存の訳文は保持されます。

### 5. その他

- Translator3000 の強制アップデートチェックをブロック（`tr3000_disable_update.py`）。
- 訳文を枠内に自動でフィット（`tr3000_autofit.py`）。
- 設定 UI の英語ラベル（`tr3000_ui.py`）。

オリジナルの Translator3000 のすべて — Ctrl+` パネル、Off / Prescan / DB-only / Realtime の各モード、ゲームごとの翻訳データベース — はそのまま動作します。追加機能はそれらの既存のポイントにフックするだけです。

---

## 🚀 インストール

1. パッケージをビルドするか（[ビルド](#-ビルド)参照）、ビルド済みの `build/Translator3000-openai.rpa` を使います。
2a. または `Translator3000-openai.rpa` をゲームの `game` フォルダにコピーします — オリジナルの Translator3000 がすでに含まれています。
2b. または、ゲームにオリジナルの `Translator3000.rpa` がすでにある場合は、`build/Translator3000-openai-addon.rpa` をその横にコピーしてください：アドオンがオリジナルの上に新機能を追加します。
3. ゲームを起動し、**Ctrl+`** で Translator3000 パネルを開きます。

> オリジナルの `Translator3000.rpa` や、単体の `.py` / `.rpy` ファイルをゲームにコピー**しないでください**。単体ファイルは RPA 内のファイルより優先されてしまいます。Ren'Py は `game` フォルダ内のすべての `.rpa` を自動で読み込みます。

設定ページの最初の 2 つのボタンが **Export translation** と **Import translation** です（ロシア語 UI では **Экспорт перевода** / **Импорт перевода**）。

---

## 📖 使い方

### ゲームを翻訳する

1. **Ctrl+`** を押し、OpenAI プロバイダー（API キー、Base URL、モデル）を設定します。
2. **Prescan** を実行し、スクリプト全体（と UI テキスト）をデータベースに翻訳します。
3. 表示モードを選びます：
   - **DB only** — データベースにある訳文のみ表示（プリスキャン後に推奨）。
   - **Realtime** — 不足する行をその場で翻訳。
   - **Off** — 原文言語。

### ゲーム UI を翻訳する

1. OpenAI 設定（Ctrl+`）で **「Переводить интерфейс игры (меню, настройки, подсказки)」**（「ゲームインターフェース：メニュー、設定、ヒントを翻訳」）にチェックを入れます。デフォルトは**オフ**です。
2. プリスキャンを実行します — 画面の文字列が台詞と一緒に収集・翻訳されます。
3. **DB only** を選ぶと UI が翻訳言語で表示され、**Off** を選ぶと原文に戻ります。

### クイック切り替え

- **Alt+1**（macOS は Option+1）または右上のバッジのクリックで **Off ↔ DB only** を切り替えます。現在のモードが Prescan または Realtime の場合、切り替えると Off になります。
- 切り替えは `translator3000._gui` の `mode` プロパティ経由 — Ctrl+` パネルのボタンとまったく同じ仕組み — で行われるため、パネルと画面上のすべてのテキストが一斉に更新されます。設定ファイルは一切変更されません。再起動後も `modeOnStartup` が適用されます。

---

## 💾 データの保存場所

使用中の翻訳はユーザーフォルダにあります：

```
vladya's projects database/translator3000/translations/<ゲームのセーブ ID>/
```

この ID はゲームの `config.save_directory` から取得されます。同じゲーム・サービス・言語ペアであれば、プリスキャンは既存の行を再利用し、新しい行だけを翻訳します。

共有の OpenAI 設定（API キー、Base URL、選択内容）は全ゲーム共通で 1 か所に保存されます：

```
vladya's projects database/translator3000/_translator3000_openai.json
```

UI 翻訳の設定（`ui_translate_enabled`、`ui_max_chars`、`ui_debug`）：

```
vladya's projects database/translator3000/_translator3000_ui.json
```

`ui_debug` を `true` にすると UI 翻訳ログ（同じフォルダの `_translator3000_ui_debug.log`）が書き出されます。

---

## 🔧 ビルド

MOD のソースは `src/` にあります。変更したら、パッケージを再ビルドします：

```text
python build_rpa.py          # full：オリジナル + アドオン -> build/Translator3000-openai.rpa
python build_rpa.py addon    # アドオンのみ               -> build/Translator3000-openai-addon.rpa
python build_rpa.py all      # 両方
```

MOD のソースは `src/` にあります。フルビルドはオリジナルの `Translator3000.rpa` と以下の MOD ファイルを統合します；アドオンビルドは MOD ファイルだけを詰めるため、お持ちのオリジナル `Translator3000.rpa` の横に `Translator3000-openai-addon.rpa` をコピーしてください：

- `zzz_translator3000_openai.rpyc`
- `tr3000_openai.py`
- `tr3000_ui.py`
- `tr3000_ui_translate.py`
- `tr3000_mode_toggle.py`
- `tr3000_autofit.py`
- `tr3000_disable_update.py`
- `tr3000_transfer.py`

> Ren'Py は RPA 内の `.rpy` ファイルを実行しません。画面スクリプトは、**対象ゲーム**の Ren'Py バージョンでコンパイルした `zzz_translator3000_openai.rpyc` が必要です：`.rpy` をゲームの `game` フォルダに入れて一度起動し、生成された `.rpyc` をここにコピーしてください。`.py` のみの変更なら `python build_rpa.py` で十分です。

### UI モジュールの仕組み

`tr3000_ui_translate.py` は独立モジュールで、そのローダーは `zzz_translator3000_openai.rpy` の中にあります（別ファイルのローダーはありません）：

- **プリスキャンは常に UI テキストをスキャンします**：文字列は Ren'Py に登録されたすべての画面から収集され、Translator3000 の通常のプリスキャンリストに追加され、同じプロバイダーで翻訳されて同じデータベースに保存されます。ゲームごとにハードコードする内容はありません。
- **表示はオプトイン方式**：設定のチェックボックスはデフォルトでオフのため、UI は原文を表示します。有効にすると表示は Translator3000 のモードに従います — Off は原文、DB-only/Prescan はデータベースのみ、Realtime はライブ翻訳も追加。

`tr3000_mode_toggle.py` が別モジュールなのは、モード切り替えが UI だけでなく台詞にも影響するためです。バッジ画面と Alt+1 ホットキーが使う `current_mode()`、`set_mode()`、`toggle_db_only()`、`mode_label()` を収めています。

---

## 🤝 コントリビューション

Issue や Pull Request を歓迎します。あるゲームで UI が翻訳されない場合は、`ui_debug` を有効にして `_translator3000_ui_debug.log` の該当行をレポートに添付してください。

## 📄 ライセンス

Translator3000 と Ren'Py はそれぞれの作者の作品です。本リポジトリはその上に OpenAI/UI 拡張層を追加するだけです。再配布の前に原プロジェクトの規約を確認してください。
