# Translator3000 — Edición OpenAI

<p align="center">
  <a href="README.md">English</a> ·
  <a href="README.vi.md">Tiếng Việt</a> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <strong>Español</strong>
</p>

> Una extensión de **Translator3000** para juegos Ren'Py que añade traducción con OpenAI / ChatGPT, traducción de la interfaz del juego (menús y ajustes), un cambio rápido de modo dentro del juego y exportación/importación de traducciones, Se ofrece en dos variantes de un solo archivo: un `Translator3000-openai.rpa` independiente (el original + el complemento) o un pequeño `Translator3000-openai-addon.rpa` que se coloca junto a un `Translator3000.rpa` original.

Translator3000 ya traduce los diálogos de los juegos Ren'Py en tiempo real con sus servicios integrados. Este proyecto mantiene intacto el Translator3000 original y añade nuevas funciones por encima. Para usarlo en otro juego, basta con copiar 1 archivo `.rpa` (la versión independiente ya combinada, o el complemento junto a un `Translator3000.rpa` original) en la carpeta `game` de ese juego.

---

## ✨ Funciones añadidas respecto al Translator3000 original

### 1. Traducción con OpenAI / ChatGPT

- Nuevo proveedor `openai_api`: traduce mediante la API de OpenAI o una cuenta de ChatGPT, con tu propia clave API, Base URL, elección de modelo (lista integrada de modelos GPT) y nivel de esfuerzo de razonamiento.
- Traducción por lotes grandes con protección de etiquetas de Ren'Py (`[variables]`, `{etiquetas}`, `%(...)s`) mediante marcadores, para que las líneas traducidas nunca rompan la sintaxis del juego.
- Se engancha al propio punto de preescaneo de Translator3000: todo el guion se escanea de antemano, las entradas existentes de la base de datos se reutilizan y solo se envían a traducir las líneas nuevas.
- Los ajustes de OpenAI se comparten entre todos los juegos del mismo equipo.

### 2. Traducción de la interfaz del juego — sin parchear cada juego

- El preescaneo también recoge el texto de **cada pantalla registrada** de Ren'Py (menú principal, Preferencias, Ajustes, guardar/cargar…) directamente desde el AST de las pantallas: sin cadenas codificadas a mano, por lo que funciona en cualquier juego.
- Las traducciones de la interfaz se guardan en la **misma base de datos** que los diálogos y las produce el **mismo proveedor**.
- La visualización es opcional mediante una casilla en los ajustes y sigue el modo de Translator3000: **Off** = texto original, **DB only / Prescan** = solo búsqueda en la base de datos, **Realtime** = traducción en vivo cuando falta una entrada.
- Por defecto, los juegos siempre arrancan en el idioma original.

### 3. Cambio rápido de modo (Off ↔ DB only)

- Una insignia siempre visible en la esquina superior derecha muestra el modo actual (`OFF: original`, `Mode: DB only`, …).
- Haz clic en la insignia o pulsa **Alt+1** (Option+1 en macOS) para alternar **Off ↔ DB only** al instante, sin abandonar la escena ni la línea de diálogo actual y sin tocar el archivo de ajustes.

### 4. Exportar / importar traducciones

- Botones **Export translation** / **Import translation** en la parte superior del panel de ajustes (Ctrl+`).
- La exportación genera `translations.tr3000.json` para hacer copias de seguridad o trasladarlo a otro equipo. La importación solo añade las líneas que faltan; las traducciones locales existentes se conservan.

### 5. Extras

- Bloquea la comprobación forzada de actualizaciones de Translator3000 (`tr3000_disable_update.py`).
- Ajusta automáticamente el texto traducido a su marco (`tr3000_autofit.py`).
- Etiquetas en inglés para la interfaz de ajustes (`tr3000_ui.py`).

Todo lo del Translator3000 original —el panel Ctrl+`, los modos Off / Prescan / DB-only / Realtime y la base de datos de traducción por juego— sigue funcionando sin cambios. Las novedades solo se enganchan a esos puntos existentes.

---

## 🚀 Instalación

1. Compila el paquete (véase [Compilación](#-compilación)) o usa el ya generado `build/Translator3000-openai.rpa`.
2a. O bien copia `Translator3000-openai.rpa` en la carpeta `game` del juego: ya incluye el Translator3000 original.
2b. O bien, si el juego ya tiene un `Translator3000.rpa` original, copia `build/Translator3000-openai-addon.rpa` junto a él: el complemento añade las funciones nuevas sobre el original.
3. Inicia el juego y pulsa **Ctrl+`** para abrir el panel de Translator3000.

> **No** copies también el `Translator3000.rpa` original ni archivos sueltos `.py` / `.rpy` en el juego: los archivos sueltos tienen prioridad sobre los que están dentro del RPA. Ren'Py carga automáticamente cada `.rpa` de la carpeta `game`.

Los dos primeros botones de la página de ajustes son **Export translation** e **Import translation** (en la interfaz rusa: **Экспорт перевода** / **Импорт перевода**).

---

## 📖 Uso

### Traducir un juego

1. Pulsa **Ctrl+`** y configura el proveedor OpenAI (clave API, Base URL, modelo).
2. Ejecuta **Prescan** para traducir todo el guion (y el texto de la interfaz) a la base de datos.
3. Elige un modo de visualización:
   - **DB only**: muestra las traducciones que ya están en la base de datos (recomendado tras el preescaneo).
   - **Realtime**: traduce las líneas que faltan sobre la marcha.
   - **Off**: idioma original.

### Traducir la interfaz del juego

1. En los ajustes de OpenAI (Ctrl+`), marca **«Переводить интерфейс игры (меню, настройки, подсказки)»** («Traducir la interfaz del juego: menús, ajustes, consejos»). Está **desactivada por defecto**.
2. Ejecuta el preescaneo: las cadenas de las pantallas se recogen y se traducen junto con los diálogos.
3. Selecciona **DB only** para ver la interfaz en el idioma de destino; selecciona **Off** para volver al original.

### Cambio rápido

- **Alt+1** (Option+1 en macOS) o un clic en la insignia de la esquina superior derecha alterna **Off ↔ DB only**. Si el modo actual es Prescan o Realtime, el cambio pasa a Off.
- El cambio se realiza a través de la propiedad `mode` de `translator3000._gui`, el mismo mecanismo que usan los botones del panel Ctrl+`, así que el panel y todo el texto en pantalla se actualizan a la vez. El archivo de ajustes nunca se modifica: al reiniciar el juego sigue aplicándose `modeOnStartup`.

---

## 💾 Dónde se guardan los datos

Las traducciones en uso están en la carpeta del usuario:

```
vladya's projects database/translator3000/translations/<id de guardado del juego>/
```

El id procede del `config.save_directory` del juego. Para el mismo juego, servicio y par de idiomas, el preescaneo reutiliza las líneas existentes y solo traduce las nuevas.

Los ajustes compartidos de OpenAI (clave API, Base URL, opciones) se guardan una sola vez para todos los juegos:

```
vladya's projects database/translator3000/_translator3000_openai.json
```

Ajustes de traducción de la interfaz (`ui_translate_enabled`, `ui_max_chars`, `ui_debug`):

```
vladya's projects database/translator3000/_translator3000_ui.json
```

Pon `ui_debug` a `true` para escribir un registro de traducción de la interfaz (`_translator3000_ui_debug.log`, en la misma carpeta).

---

## 🔧 Compilación

Las fuentes del mod están en `src/`. Tras editarlas, vuelve a generar el paquete:

```text
python build_rpa.py          # full: original + complemento -> build/Translator3000-openai.rpa
python build_rpa.py addon    # solo el complemento         -> build/Translator3000-openai-addon.rpa
python build_rpa.py all      # ambos
```

Las fuentes del mod están en `src/`. La compilación completa combina el `Translator3000.rpa` original con los siguientes archivos del mod; la del complemento empaqueta solo los archivos del mod, así que copia `Translator3000-openai-addon.rpa` junto a un `Translator3000.rpa` original que ya tengas:

- `zzz_translator3000_openai.rpyc`
- `tr3000_openai.py`
- `tr3000_ui.py`
- `tr3000_ui_translate.py`
- `tr3000_mode_toggle.py`
- `tr3000_autofit.py`
- `tr3000_disable_update.py`
- `tr3000_transfer.py`

> Ren'Py no ejecuta los archivos `.rpy` que están dentro de un RPA. El script de pantallas debe ser el `zzz_translator3000_openai.rpyc` compilado, generado con la versión de Ren'Py **del juego de destino**: coloca el `.rpy` en la carpeta `game`, inicia el juego una vez y copia de vuelta el `.rpyc` generado. Si solo cambian archivos `.py`, basta con `python build_rpa.py`.

### Cómo funciona el módulo de interfaz

`tr3000_ui_translate.py` es un módulo independiente; su cargador vive dentro de `zzz_translator3000_openai.rpy` (no hay un archivo cargador aparte):

- **El preescaneo siempre escanea el texto de la interfaz**: las cadenas se recogen de todas las pantallas registradas de Ren'Py, se añaden a la lista normal de preescaneo de Translator3000, se traducen con el mismo proveedor y se guardan en la misma base de datos. Nada está codificado para un juego concreto.
- **La visualización es opcional**: la casilla de ajustes está desactivada por defecto, así que la interfaz muestra el idioma original. Al activarla, la visualización sigue el modo de Translator3000: Off = original, DB-only/Prescan = solo base de datos, Realtime = más traducción en vivo.

`tr3000_mode_toggle.py` es un módulo aparte porque el cambio de modo también afecta a los diálogos, no solo a la interfaz: contiene `current_mode()`, `set_mode()`, `toggle_db_only()` y `mode_label()`, que usan la pantalla de la insignia y la tecla rápida Alt+1.

---

## 🤝 Contribuir

Se aceptan issues y pull requests. Si la interfaz de algún juego no se traduce, activa `ui_debug` y adjunta a tu informe las líneas relevantes de `_translator3000_ui_debug.log`.

## 📄 Licencia

Translator3000 y Ren'Py son obra de sus respectivos autores; este repositorio solo añade encima la capa de extensión OpenAI/UI. Consulta las condiciones de los proyectos originales antes de redistribuir.
