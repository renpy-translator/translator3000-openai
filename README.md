# Translator3000 OpenAI

Bản Translator3000 gốc kèm phần dịch qua OpenAI API hoặc tài khoản ChatGPT. Sang game khác chỉ cần copy một file vào thư mục `game`.

## Copy vào game

File đóng gói là `build\Translator3000-openai.rpa`. Trong đó có bản Translator3000 gốc, menu OpenAI, chặn bắt cập nhật, và xuất/nhập bản dịch.

Ren'Py tự nạp mọi file `.rpa` trong thư mục `game`. Không copy kèm `Translator3000.rpa` gốc hay các file `.py` và `.rpy` rời, vì file rời sẽ đè lên file trong RPA.

Mở game, nhấn `Ctrl` + `` ` ``. Hai nút đầu trang cài đặt là **Export translation** và **Import translation**. Nếu giao diện đang tiếng Nga, đó là **Экспорт перевода** và **Импорт перевода**.

## Xuất và nhập bản dịch

**Export translation** thu cửa sổ game xuống và mở hộp lưu file. File mặc định là `translations.tr3000.json` trên Desktop. File này nằm trên máy, không được gửi lên mạng.

**Import translation** mở hộp chọn file đó. Câu chưa có được thêm vào. Câu đã có trên máy được giữ nguyên.

Bản dịch đang dùng vẫn nằm trong thư mục người dùng:

`vladya's projects database\translator3000\translations\<mã save của game>\`

Mã này lấy từ `config.save_directory` của game. Cùng một game, cùng dịch vụ và cùng cặp ngôn ngữ thì prescan dùng lại câu cũ và chỉ dịch câu mới.

## Cài đặt dùng chung

Khóa API, Base URL và các lựa chọn OpenAI được ghi ở:

`vladya's projects database\translator3000\_translator3000_openai.json`

File này dùng cho mọi game trên cùng máy.

## Đóng gói lại

Sau khi sửa các file nguồn, tạo lại file RPA:

```text
python build_rpa.py
```

Ren'Py không chạy file `.rpy` nằm trong RPA. Script màn hình phải là `zzz_translator3000_openai.rpyc`, biên dịch bằng đúng bản Ren'Py của game. Với Guilty Pleasure, mở game một lần khi file `.rpy` còn nằm trong thư mục `game`, rồi copy file `.rpyc` vừa tạo về thư mục này.

Lệnh đóng gói gộp `Translator3000.rpa` với các file dưới đây và ghi `build\Translator3000-openai.rpa`:

- `zzz_translator3000_openai.rpyc`
- `tr3000_openai.py`
- `tr3000_ui.py`
- `tr3000_ui_translate.py`
- `tr3000_mode_toggle.py`
- `tr3000_autofit.py`
- `tr3000_disable_update.py`
- `tr3000_transfer.py`

## Chuyển nhanh mode (off / DB only)

Module riêng `tr3000_mode_toggle.py` (không nằm trong file dịch UI vì nó chuyển
mode của Translator3000, ảnh hưởng cả hội thoại):

- Badge ở góc phải trên cùng màn hình luôn hiển thị mode hiện tại
  (`OFF: original` / `Mode: DB only` / ...). Click vào badge hoặc nhấn
  **Alt+1** (Option+1 trên macOS) để chuyển qua lại **off ↔ DB only**;
  đang ở prescan/realtime thì nhấn sẽ về off.
- Việc chuyển đi qua property `mode` của `translator3000._gui` — đúng cơ chế
  các nút trong panel Ctrl+\` dùng — nên panel và mọi text cập nhật theo.
  Không đụng vào file settings: khởi động lại game vẫn theo `modeOnStartup`.

## Dịch giao diện game (UI)

Module riêng `tr3000_ui_translate.py` (trình nạp nằm chung trong
`zzz_translator3000_openai.rpy`, không có file loader riêng). Cách hoạt động:

- **Prescan luôn quét cả text UI**: chuỗi lấy từ mọi screen đã đăng ký của
  Ren'Py (menu, cài đặt, save/load...), nối vào cùng danh sách prescan của
  Translator3000, dịch bằng cùng provider và lưu **cùng database** với hội
  thoại. Không hardcode chuỗi của game nào.
- **Hiển thị là opt-in**: trong màn hình cài đặt OpenAI (Ctrl+`) có checkbox
  "Переводить интерфейс игры (меню, настройки, подсказки)" — mặc định **tắt**.
  Tắt thì UI hiện nguyên gốc. Bật thì UI bám theo mode của Translator3000:
  Off = nguyên gốc, DB-only/Prescan = chỉ lấy bản dịch đã có trong DB,
  Realtime = thêm dịch live khi thiếu.
- Cấu hình lưu ở `vladya's projects database\translator3000\_translator3000_ui.json`
  (`ui_translate_enabled`, `ui_max_chars`, `ui_debug`). Bật `ui_debug` sẽ ghi
  log dịch UI vào `_translator3000_ui_debug.log` cùng thư mục.
