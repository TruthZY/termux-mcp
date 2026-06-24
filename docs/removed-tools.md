# 已删除工具参考文档

以下工具已从主代码中移除（可通过 `shell_exec` 直接执行等价命令）。
如需恢复，取消注释对应的 `@register_tool` 块并添加回 handler 文件即可。

## device.py — 可删除的工具（31 个）

### Vision
- `screenshot` → `termux-screenshot -o FILE`
- `camera_photo` → `termux-camera-photo -c 0 FILE`
- `camera_info` → `termux-camera-info`

### Clipboard
- `clipboard_get` → `termux-clipboard-get`
- `clipboard_set` → `echo TEXT | termux-clipboard-set`

### Notifications
- `notify` → `termux-notification --title T --content C`
- `notify_remove` → `termux-notification-remove ID`

### Share / URL / Download
- `share` → `termux-share FILE`
- `open_url` → `termux-open-url URL`
- `download` → `termux-download URL`

### Device Info
- `battery_status` → `termux-battery-status`
- `wifi_info` → `termux-wifi-connectioninfo`
- `wifi_scan` → `termux-wifi-scaninfo`
- `location` → `termux-location -p gps`

### Contacts / SMS / Calls
- `contacts` → `termux-contact-list`
- `sms_send` → `termux-sms-send -n NUMBER TEXT`
- `sms_inbox` → `termux-sms-list -l 10`
- `phone_call` → `termux-telephony-call NUMBER`

### Apps / Vibrate / TTS
- `list_apps` → `termux-app-list`
- `vibrate` → `termux-vibrate -d 500`
- `tts_speak` → `termux-tts-speak TEXT`

### Torch / Wallpaper / Brightness / Volume
- `torch` → `termux-torch on/off`
- `wallpaper` → `termux-wallpaper -f FILE`
- `brightness` → `termux-brightness LEVEL`
- `volume` → `termux-volume STREAM LEVEL`

### Screen Record / QR / Barcode
- `screen_record` → `termux-screen-record -o FILE`
- `qrcode` → `qrencode -o FILE TEXT`
- `scan_barcode` → `zbarimg FILE`

### Biometric / Toast / Dialog
- `fingerprint` → `termux-fingerprint`
- `toast` → `termux-toast TEXT`
- `dialog` → `termux-dialog confirm -t TITLE -i MSG`

### Sensors / Mic / STT / Media
- `sensor_read` → `termux-sensor -s SENSOR -n LIMIT`
- `microphone_record` → `termux-microphone-record -l SECONDS -f FILE`
- `speech_to_text` → `termux-speech-to-text`
- `media_player` → `termux-media-player ACTION`

### Storage / Telephony
- `storage_get` → `termux-storage-get FILE`
- `telephony_device` → `termux-telephony-deviceinfo`
- `telephony_cell` → `termux-telephony-cellinfo`
- `infrared` → `termux-infrared-transmit -f FREQ PATTERN`

## tools.py — 可删除的工具（4 个）

- `speedtest` → `speedtest-cli` 或 `curl -s https://speedtest.net`
- `public_ip` → `curl -s ifconfig.me`
- `weather` → `curl -s wttr.in/CITY`
- `translate` → `curl` 调用翻译 API

---

*总计删除 35 个工具，保留约 53 个。*
*所有删除的工具均可通过 `shell_exec` 执行等价 shell 命令。*
