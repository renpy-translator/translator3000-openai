# AGENTS.md — translator3000-openai

This repo is one of **two independent Git repos** for Translator3000 (see the
workspace-root `AGENTS.md` in `../AGENTS.md` when working from the monorepo
workspace, or the summary below when this repo is cloned alone).

## Two repos, one feature set

- **`translator3000-openai` (this repo)** — add-on for the **stock**
  Translator3000. Ships `Translator3000-openai.rpa` (stock + add-on) and
  `Translator3000-openai-addon.rpa` (add-on only, next to a stock
  `Translator3000.rpa`). For users who already have the original
  Translator3000 and only want the OpenAI/UI extension.
- **`translator3000-source`** (sibling repo) — full reconstructed source of
  Translator3000 `1.45.11` that builds one drop-in `Translator3000.rpa`.
  For users who want to build/customize from scratch and develop new features.

The repos are independent and used differently, but they offer the **same
features**. When a feature is developed, update **both** repos — same
behavior, different code organization. This repo must keep stock
Translator3000 untouched and layer loose modules (`src/tr3000_*.py` +
`zzz_translator3000_openai.rpy`) on top of it; the source repo integrates the
same code natively instead. Do not force either layout onto the other repo.

## Rules for this repo

- The add-on must keep working next to an unmodified stock `Translator3000.rpa`
  on Ren'Py 7 (Python 2) and Ren'Py 8 (Python 3); shared code must be
  dual-compatible (`from __future__ import unicode_literals`, no f-strings).
- Build before committing: `python build_rpa.py all`.
- Git identity: `RenPy-Translator <hien.bt@htigroup.vn>`.
  Conventional commits, no AI references.
- Never commit `build/` output or `__pycache__/`.
