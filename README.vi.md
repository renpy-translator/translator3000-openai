# Translator3000 — Bản OpenAI

<p align="center">
  <a href="README.md">English</a> ·
  <strong>Tiếng Việt</strong> ·
  <a href="README.ru.md">Русский</a> ·
  <a href="README.zh-CN.md">简体中文</a> ·
  <a href="README.ja.md">日本語</a> ·
  <a href="README.es.md">Español</a>
</p>

> Bản mở rộng của **Translator3000** cho game Ren'Py: thêm dịch bằng OpenAI / ChatGPT, dịch giao diện game (menu & cài đặt), chuyển mode nhanh trong game, và xuất/nhập bản dịch — Phát hành theo 2 dạng file đơn: `Translator3000-openai.rpa` độc lập (Translator3000 gốc + phần mở rộng) hoặc `Translator3000-openai-addon.rpa` nhỏ gọn, thả cạnh `Translator3000.rpa` gốc.

Translator3000 vốn đã dịch hội thoại game Ren'Py theo thời gian thực bằng các dịch vụ tích hợp sẵn. Dự án này giữ nguyên Translator3000 gốc và thêm một lớp tính năng mới lên trên. Muốn dùng cho game khác, chỉ cần copy 1 file `.rpa` (bản độc lập đã gộp sẵn, hoặc bản addon đặt cạnh `Translator3000.rpa` gốc) vào thư mục `game` của game đó.

---

## ✨ Tính năng bổ sung so với Translator3000 gốc

### 1. Dịch bằng OpenAI / ChatGPT

- Thêm provider `openai_api`: dịch qua OpenAI API hoặc tài khoản ChatGPT, với API key, Base URL, model tự chọn (danh sách model GPT tích hợp) và mức reasoning effort.
- Dịch theo batch lớn, có bảo vệ tag Ren'Py (`[biến]`, `{tag}`, `%(...)s`) bằng placeholder nên câu dịch không phá cú pháp game.
- Hook vào đúng điểm prescan của Translator3000: quét trước toàn bộ script, dùng lại câu đã có trong database, chỉ gửi dịch câu mới.
- Cài đặt OpenAI dùng chung cho mọi game trên cùng máy.

### 2. Dịch giao diện game (UI) — không cần sửa từng game

- Prescan thu thập thêm text từ **mọi screen đã đăng ký** của Ren'Py (menu chính, Preferences, Settings, save/load…) trực tiếp từ AST của screen — không hardcode chuỗi nên game nào cũng dùng được.
- Bản dịch UI lưu **cùng database** với hội thoại và dùng **cùng provider**.
- Hiển thị là opt-in qua checkbox trong cài đặt, bám theo mode của Translator3000: **Off** = nguyên gốc, **DB only / Prescan** = chỉ lấy bản dịch đã có, **Realtime** = dịch live khi thiếu.
- Mặc định game luôn khởi động bằng ngôn ngữ gốc.

### 3. Chuyển nhanh mode Off ↔ DB only

- Badge luôn hiển thị ở góc phải trên cùng màn hình, cho biết mode hiện tại (`OFF: original`, `Mode: DB only`…).
- Click vào badge hoặc nhấn **Alt+1** (Option+1 trên macOS) để chuyển qua lại **Off ↔ DB only** ngay lập tức — không rời khỏi cảnh hay câu thoại đang đọc, không đụng vào file settings.

### 4. Xuất / nhập bản dịch

- Hai nút **Export translation** / **Import translation** ngay đầu trang cài đặt (Ctrl+`).
- Export ghi ra `translations.tr3000.json` để sao lưu hoặc mang sang máy khác. Import chỉ thêm câu chưa có; bản dịch đã có trên máy được giữ nguyên.

### 5. Tiện ích đi kèm

- Chặn Translator3000 tự bắt cập nhật (`tr3000_disable_update.py`).
- Tự co giãn text cho vừa khung (`tr3000_autofit.py`).
- Nhãn tiếng Anh cho giao diện cài đặt (`tr3000_ui.py`).

Mọi thứ của Translator3000 gốc — panel Ctrl+`, các mode Off / Prescan / DB-only / Realtime, database bản dịch theo từng game — vẫn hoạt động nguyên vẹn. Phần bổ sung chỉ hook vào những điểm có sẵn đó.

---

## 🚀 Cài đặt

1. Đóng gói (xem [Đóng gói lại](#-đóng-gói-lại)) hoặc lấy sẵn `build/Translator3000-openai.rpa`.
2a. Hoặc copy `Translator3000-openai.rpa` vào thư mục `game` của game — bản này đã gộp sẵn Translator3000 gốc.
2b. Hoặc, nếu game đã có `Translator3000.rpa` gốc, copy `build/Translator3000-openai-addon.rpa` vào cạnh nó: addon cộng thêm tính năng mới lên trên bản gốc đó.
3. Mở game, nhấn **Ctrl+`** để mở panel Translator3000.

> **Không** copy kèm `Translator3000.rpa` gốc hay các file `.py` / `.rpy` rời vào game — file rời sẽ đè lên file trong RPA. Ren'Py tự nạp mọi file `.rpa` trong thư mục `game`.

Hai nút đầu trang cài đặt là **Export translation** và **Import translation** (giao diện tiếng Nga: **Экспорт перевода** / **Импорт перевода**).

---

## 📖 Cách dùng

### Dịch game

1. Nhấn **Ctrl+`**, cấu hình provider OpenAI (API key, Base URL, model).
2. Chạy **Prescan** để dịch toàn bộ script (và text UI) vào database.
3. Chọn mode hiển thị:
   - **DB only** — hiện bản dịch đã có trong database (khuyên dùng sau prescan).
   - **Realtime** — dịch live những câu còn thiếu.
   - **Off** — ngôn ngữ gốc.

### Dịch giao diện game

1. Trong cài đặt OpenAI (Ctrl+`), tick **"Переводить интерфейс игры (меню, настройки, подсказки)"** ("Dịch giao diện game: menu, cài đặt, gợi ý"). Mặc định **tắt**.
2. Chạy Prescan — chuỗi của các screen được thu thập và dịch cùng với hội thoại.
3. Chọn **DB only** để xem UI bằng ngôn ngữ đích; chọn **Off** để quay về nguyên gốc.

### Chuyển mode nhanh

- **Alt+1** (Option+1 trên macOS) hoặc click badge góc phải trên cùng để đổi **Off ↔ DB only**. Nếu mode hiện tại là Prescan hoặc Realtime, thao tác này chuyển về Off.
- Việc chuyển đi qua property `mode` của `translator3000._gui` — đúng cơ chế các nút trong panel Ctrl+` dùng — nên panel và mọi text trên màn hình cập nhật theo. File settings không bao giờ bị sửa: khởi động lại game vẫn theo `modeOnStartup`.

---

## 💾 Dữ liệu được lưu ở đâu

Bản dịch đang dùng nằm trong thư mục người dùng:

```
vladya's projects database/translator3000/translations/<mã save của game>/
```

Mã này lấy từ `config.save_directory` của game. Cùng một game, cùng dịch vụ và cùng cặp ngôn ngữ thì prescan dùng lại câu cũ và chỉ dịch câu mới.

Cài đặt OpenAI dùng chung (API key, Base URL, lựa chọn) lưu một lần cho mọi game:

```
vladya's projects database/translator3000/_translator3000_openai.json
```

Cài đặt dịch UI (`ui_translate_enabled`, `ui_max_chars`, `ui_debug`):

```
vladya's projects database/translator3000/_translator3000_ui.json
```

Đặt `ui_debug` thành `true` để ghi log dịch UI (`_translator3000_ui_debug.log`, cùng thư mục).

---

## 🔧 Đóng gói lại

File nguồn của mod nằm trong `src/`. Sau khi sửa chúng, tạo lại file RPA:

```text
python build_rpa.py          # full: gốc + addon -> build/Translator3000-openai.rpa
python build_rpa.py addon    # chỉ addon        -> build/Translator3000-openai-addon.rpa
python build_rpa.py all      # cả hai
```

File nguồn của mod nằm trong `src/`. Bản full gộp `Translator3000.rpa` gốc với các file mod dưới đây; bản addon chỉ đóng các file mod, nên hãy copy `Translator3000-openai-addon.rpa` vào cạnh `Translator3000.rpa` gốc bạn đã có:

- `zzz_translator3000_openai.rpyc`
- `tr3000_openai.py`
- `tr3000_ui.py`
- `tr3000_ui_translate.py`
- `tr3000_mode_toggle.py`
- `tr3000_autofit.py`
- `tr3000_disable_update.py`
- `tr3000_transfer.py`

> Ren'Py không chạy file `.rpy` nằm trong RPA. Script màn hình phải là `zzz_translator3000_openai.rpyc` đã biên dịch, bằng đúng bản Ren'Py của game đích: thả file `.rpy` vào thư mục `game`, mở game một lần, rồi copy file `.rpyc` sinh ra về đây. Sửa file `.py` thuần thì chỉ cần chạy `python build_rpa.py`.

### Cách module UI hoạt động

`tr3000_ui_translate.py` là module độc lập; trình nạp nằm trong `zzz_translator3000_openai.rpy` (không có file loader riêng):

- **Prescan luôn quét text UI**: chuỗi lấy từ mọi screen đã đăng ký của Ren'Py, nối vào danh sách prescan thường lệ của Translator3000, dịch bằng cùng provider và lưu cùng database. Không hardcode theo game nào.
- **Hiển thị là opt-in**: checkbox cài đặt mặc định tắt nên UI hiện ngôn ngữ gốc. Khi bật, hiển thị bám theo mode của Translator3000 — Off = nguyên gốc, DB-only/Prescan = chỉ database, Realtime = thêm dịch live.

`tr3000_mode_toggle.py` là module riêng vì chuyển mode ảnh hưởng cả hội thoại chứ không chỉ UI: nó chứa `current_mode()`, `set_mode()`, `toggle_db_only()` và `mode_label()` dùng cho màn hình badge và phím tắt Alt+1.

---

## 🤝 Đóng góp

Hoan nghênh issue và pull request. Nếu một game nào đó không dịch được UI, hãy bật `ui_debug` và đính kèm các dòng liên quan trong `_translator3000_ui_debug.log` vào báo cáo của bạn.

## 📄 Giấy phép

Translator3000 và Ren'Py thuộc về các tác giả tương ứng; repo này chỉ thêm lớp mở rộng OpenAI/UI lên trên. Hãy kiểm tra điều khoản của các dự án gốc trước khi phân phối lại.
