"""Device, media, and communication tools."""

from ..registry import register_tool
from ..shell import execute
from ..utils import error_msg, is_safe_path, shell_quote, shell_quote_num


# ── Vision ────────────────────────────────────────────────────────────────

@register_tool(
    name="screenshot",
    description="Take a screenshot of the current screen.",
    schema={
        "type": "object",
        "properties": {"output": {"type": "string", "description": "Output file path (default: auto-generated)"}},
    },
    category="device",
)
def handle_screenshot(data: dict) -> str:
    output = data.get("output", "").strip()
    if output:
        return execute(f"termux-screenshot -o {shell_quote(output)} 2>/dev/null || echo 'Screenshot failed'")
    return execute("termux-screenshot 2>/dev/null || echo 'Screenshot failed'")


@register_tool(
    name="camera_photo",
    description="Take a photo using the device camera and save as JPEG.",
    schema={
        "type": "object",
        "properties": {
            "camera_id": {"type": "integer", "description": "Camera ID (0=rear, 1=front, default: 0)"},
            "output": {"type": "string", "description": "Output file path (default: auto-generated)"},
        },
    },
    category="device",
)
def handle_camera_photo(data: dict) -> str:
    camera_id = shell_quote_num(data.get("camera_id", 0))
    output = data.get("output", "").strip() or "/sdcard/DCIM/termux_photo.jpg"
    return execute(
        f"termux-camera-photo -c {shell_quote(camera_id)} {shell_quote(output)} 2>/dev/null || echo Camera photo failed"
    )


@register_tool(
    name="camera_info",
    description="List device camera hardware specs (resolution, focus modes, etc.).",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_camera_info(data: dict) -> str:
    return execute("termux-camera-info 2>/dev/null || echo '{}'")


# ── Clipboard ─────────────────────────────────────────────────────────────

@register_tool(
    name="clipboard_get",
    description="Read text from the system clipboard.",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_clipboard_get(data: dict) -> str:
    return execute("termux-clipboard-get 2>/dev/null || echo '(clipboard empty)'")


@register_tool(
    name="clipboard_set",
    description="Write text to the system clipboard.",
    schema={
        "type": "object",
        "properties": {"text": {"type": "string", "description": "Text to write to clipboard"}},
        "required": ["text"],
    },
    category="device",
)
def handle_clipboard_set(data: dict) -> str:
    text = data.get("text", "").strip()
    if not text:
        return error_msg("Missing 'text'")
    return execute(f"echo {shell_quote(text)} | termux-clipboard-set && echo 'Clipboard set' || echo 'Failed'")


# ── Notifications ─────────────────────────────────────────────────────────

@register_tool(
    name="notify",
    description="Send a system notification with title, content, and optional priority.",
    schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Notification title"},
            "content": {"type": "string", "description": "Notification body text"},
            "priority": {"type": "string", "description": "Priority: low, default, high, max"},
            "id": {"type": "string", "description": "Notification ID for updates/removal"},
            "ongoing": {"type": "boolean", "description": "Make notification persistent"},
        },
        "required": ["content"],
    },
    category="device",
)
def handle_notify(data: dict) -> str:
    title = data.get("title", "TermuxGPT").strip()
    content = data.get("content", "").strip()
    if not content:
        return error_msg("Missing 'content'")
    priority = data.get("priority", "default").strip()
    nid = data.get("id", "").strip()
    flags = ""
    if nid:
        flags += f" --id {nid}"
    if data.get("ongoing"):
        flags += " --ongoing"
    return execute(
        f"termux-notification {flags} --priority {priority} "
        f"--title {shell_quote(title)} --content {shell_quote(content)} "
        f"2>/dev/null && echo 'Notification sent' || echo 'Notification failed'"
    )


@register_tool(
    name="notify_remove",
    description="Remove a notification by its ID.",
    schema={
        "type": "object",
        "properties": {"id": {"type": "string", "description": "Notification ID to remove"}},
        "required": ["id"],
    },
    category="device",
)
def handle_notify_remove(data: dict) -> str:
    nid = str(data.get("id", "")).strip()
    if not nid:
        return error_msg("Missing 'id'")
    return execute(f"termux-notification-remove {nid} 2>/dev/null && echo 'Removed' || echo 'Failed'")


# ── Share / URL / Download ────────────────────────────────────────────────

@register_tool(
    name="share",
    description="Share text or a file via Android share sheet.",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to share"},
            "file": {"type": "string", "description": "File path to share"},
        },
    },
    category="comm",
)
def handle_share(data: dict) -> str:
    text = data.get("text", "").strip()
    file_path = data.get("file", "").strip()
    if file_path:
        if not is_safe_path(file_path):
            return error_msg("Path not allowed")
        return execute(f"termux-share -a send {shell_quote(file_path)} 2>/dev/null || echo 'Share failed'")
    elif text:
        return execute(
            f"echo {shell_quote(text)} > /data/data/com.termux/files/usr/tmp/termux_share.txt 2>/dev/null && "
            f"termux-share -a send /data/data/com.termux/files/usr/tmp/termux_share.txt 2>/dev/null && "
            f"echo 'Share opened' || echo 'Share failed'"
        )
    return error_msg("Missing 'text' or 'file'")


@register_tool(
    name="open_url",
    description="Open a URL in the default browser or appropriate app.",
    schema={
        "type": "object",
        "properties": {"url": {"type": "string", "description": "URL to open"}},
        "required": ["url"],
    },
    category="comm",
)
def handle_open_url(data: dict) -> str:
    url = data.get("url", "").strip()
    if not url:
        return error_msg("Missing 'url'")
    return execute(f"termux-open-url {shell_quote(url)} 2>/dev/null && echo Opened: {shell_quote(url)} || echo Failed to open")


@register_tool(
    name="download",
    description="Download a file using Android's download manager.",
    schema={
        "type": "object",
        "properties": {
            "url": {"type": "string", "description": "URL to download"},
            "description": {"type": "string", "description": "Download description"},
            "title": {"type": "string", "description": "Download title"},
        },
        "required": ["url"],
    },
    category="comm",
)
def handle_download(data: dict) -> str:
    url = data.get("url", "").strip()
    if not url:
        return error_msg("Missing 'url'")
    desc = data.get("description", "").strip()
    title = data.get("title", "").strip()
    flags = ""
    if desc:
        flags += f" -d {shell_quote(desc)}"
    if title:
        flags += f" -t {shell_quote(title)}"
    return execute(f"termux-download{flags} {shell_quote(url)} 2>/dev/null && echo 'Download started' || echo 'Download failed'")


# ── Device Info ───────────────────────────────────────────────────────────

@register_tool(
    name="battery_status",
    description="Get battery status: level, charging state, temperature, voltage (JSON).",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_battery(data: dict) -> str:
    return execute("termux-battery-status 2>/dev/null || echo '{}'")


@register_tool(
    name="wifi_info",
    description="Get current WiFi connection info: SSID, IP, signal strength, frequency (JSON).",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_wifi_info(data: dict) -> str:
    return execute("termux-wifi-connectioninfo 2>/dev/null || echo '{}'")


@register_tool(
    name="wifi_scan",
    description="Get recent WiFi scan results: available networks and signal strength (JSON array).",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_wifi_scan(data: dict) -> str:
    return execute("termux-wifi-scaninfo 2>/dev/null || echo '[]'")


@register_tool(
    name="location",
    description="Get device GPS/network location: latitude, longitude, accuracy, altitude.",
    schema={
        "type": "object",
        "properties": {
            "provider": {"type": "string", "enum": ["gps", "network", "passive"], "description": "Location provider (default: gps)"}
        },
    },
    category="device",
)
def handle_location(data: dict) -> str:
    provider = data.get("provider", "gps").strip()
    return execute(f"termux-location -p {shell_quote(provider)} -r last 2>/dev/null || echo '{{}}'")


# ── Contacts / SMS / Calls ────────────────────────────────────────────────

@register_tool(
    name="contacts",
    description="List all contacts from the device address book (JSON array).",
    schema={"type": "object", "properties": {}},
    category="comm",
)
def handle_contacts(data: dict) -> str:
    return execute("termux-contact-list 2>/dev/null || echo '[]'")


@register_tool(
    name="sms_send",
    description="Send an SMS message. Warning: This actually sends an SMS.",
    schema={
        "type": "object",
        "properties": {
            "number": {"type": "string", "description": "Phone number"},
            "text": {"type": "string", "description": "Message content"},
        },
        "required": ["number", "text"],
    },
    category="comm",
)
def handle_sms_send(data: dict) -> str:
    number = data.get("number", "").strip()
    text = data.get("text", "").strip()
    if not number or not text:
        return error_msg("Missing 'number' or 'text'")
    return execute(f"termux-sms-send -n {shell_quote(number)} {shell_quote(text)} 2>/dev/null && echo 'SMS sent' || echo 'SMS failed'")


@register_tool(
    name="sms_inbox",
    description="List recent SMS messages from inbox.",
    schema={
        "type": "object",
        "properties": {"limit": {"type": "integer", "description": "Number of messages (default: 10)"}},
    },
    category="comm",
)
def handle_sms_inbox(data: dict) -> str:
    limit = shell_quote_num(data.get("limit", 10))
    return execute(f"termux-sms-inbox -n {limit} 2>/dev/null || echo '[]'")


@register_tool(
    name="phone_call",
    description="Dial a phone number. Warning: This actually initiates a call.",
    schema={
        "type": "object",
        "properties": {"number": {"type": "string", "description": "Phone number to call"}},
        "required": ["number"],
    },
    category="comm",
)
def handle_call(data: dict) -> str:
    number = data.get("number", "").strip()
    if not number:
        return error_msg("Missing 'number'")
    quoted = shell_quote(number)
    return execute(f"termux-telephony-call {quoted} 2>/dev/null && echo Calling {quoted} || echo Call failed")


# ── Apps / Vibrate / TTS ─────────────────────────────────────────────────

@register_tool(
    name="list_apps",
    description="List installed applications on the device (JSON).",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_list_apps(data: dict) -> str:
    return execute("termux-app-list 2>/dev/null || echo '{}'")


@register_tool(
    name="vibrate",
    description="Trigger device haptic vibration.",
    schema={
        "type": "object",
        "properties": {"duration_ms": {"type": "integer", "description": "Vibration duration in milliseconds (default: 500)"}},
    },
    category="device",
)
def handle_vibrate(data: dict) -> str:
    duration = shell_quote_num(data.get("duration_ms", 500))
    return execute(f"termux-vibrate -d {duration} 2>/dev/null && echo 'Vibrated {duration}ms' || echo 'Vibrate failed'")


@register_tool(
    name="tts_speak",
    description="Speak text aloud using the device TTS engine.",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to speak"},
            "rate": {"type": "number", "description": "Speech rate (default: 1.0)"},
            "pitch": {"type": "number", "description": "Speech pitch (default: 1.0)"},
        },
        "required": ["text"],
    },
    category="media",
)
def handle_tts_speak(data: dict) -> str:
    text = data.get("text", "").strip()
    if not text:
        return error_msg("Missing 'text'")
    rate = shell_quote_num(data.get("rate", 1.0))
    pitch = shell_quote_num(data.get("pitch", 1.0))
    return execute(f"termux-tts-speak --rate {rate} --pitch {pitch} {shell_quote(text)} 2>/dev/null && echo 'Spoken' || echo 'TTS failed'")


# ── Torch / Wallpaper / Brightness / Volume ───────────────────────────────

@register_tool(
    name="torch",
    description="Turn the flashlight (torch) on or off.",
    schema={
        "type": "object",
        "properties": {"state": {"type": "string", "enum": ["on", "off"], "description": "Torch state (default: on)"}},
    },
    category="device",
)
def handle_torch(data: dict) -> str:
    state = data.get("state", "on").strip().lower()
    if state not in ("on", "off"):
        return error_msg("State must be 'on' or 'off'")
    return execute(f"termux-torch {state} 2>/dev/null && echo 'Torch {state}' || echo 'Torch failed'")


@register_tool(
    name="wallpaper",
    description="Set device wallpaper from a file.",
    schema={
        "type": "object",
        "properties": {
            "file": {"type": "string", "description": "Image file path"},
            "lockscreen": {"type": "boolean", "description": "Set as lock screen wallpaper"},
        },
    },
    category="device",
)
def handle_wallpaper(data: dict) -> str:
    file_path = data.get("file", "").strip()
    lockscreen = data.get("lockscreen", False)
    if file_path and not is_safe_path(file_path):
        return error_msg("Path not allowed")
    flags = "-l" if lockscreen else ""
    if file_path:
        return execute(f"termux-wallpaper {flags} -f {shell_quote(file_path)} 2>/dev/null && echo 'Wallpaper set' || echo 'Wallpaper failed'")
    return execute(f"termux-wallpaper {flags} 2>/dev/null && echo 'Wallpaper set' || echo 'Wallpaper failed'")


@register_tool(
    name="brightness",
    description="Get or set screen brightness (0-255). Omit 'level' to read current value.",
    schema={
        "type": "object",
        "properties": {"level": {"type": "string", "description": "Brightness level 0-255 (omit to read current)"}},
    },
    category="device",
)
def handle_brightness(data: dict) -> str:
    level = shell_quote(data.get("level", "") or "")
    if not level:
        return execute("termux-brightness 2>/dev/null || echo '{}'")
    return execute(f"termux-brightness {level} 2>/dev/null && echo 'Brightness set to {level}' || echo 'Brightness failed'")


@register_tool(
    name="volume",
    description="Get or set audio stream volume. Streams: ring, alarm, music, notification, system, voice_call.",
    schema={
        "type": "object",
        "properties": {
            "stream": {"type": "string", "description": "Audio stream (default: music)"},
            "level": {"type": "string", "description": "Volume level (omit to read current)"},
        },
    },
    category="device",
)
def handle_volume(data: dict) -> str:
    stream = data.get("stream", "music").strip()
    level = shell_quote(data.get("level", "") or "")
    if level:
        return execute(f"termux-volume {shell_quote(stream)} {level} 2>/dev/null && echo 'Volume set' || echo 'Volume failed'")
    return execute(f"termux-volume {shell_quote(stream)} 2>/dev/null || echo 'Volume failed'")


# ── Screen Record / QR / Barcode ──────────────────────────────────────────

@register_tool(
    name="screen_record",
    description="Start or stop screen recording.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["start", "stop"], "description": "Recording action (default: start)"},
            "output": {"type": "string", "description": "Output file path"},
        },
    },
    category="media",
)
def handle_screen_record(data: dict) -> str:
    output = data.get("output", "/sdcard/DCIM/screen_record.mp4").strip()
    action = data.get("action", "start").strip()
    if action == "stop":
        return execute("termux-screen-record -q 2>/dev/null && echo 'Recording stopped' || echo 'Stop failed'")
    return execute(f"termux-screen-record -o {shell_quote(output)} 2>/dev/null && echo 'Recording started' || echo 'Recording failed'")


@register_tool(
    name="qrcode",
    description="Generate a QR code image from text.",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to encode in QR code"},
            "output": {"type": "string", "description": "Output image path (default: qrcode.png)"},
        },
        "required": ["text"],
    },
    category="media",
    requires=[{"pkg": "qrencode", "install": "pkg install qrencode"}],
)
def handle_qrcode(data: dict) -> str:
    text = data.get("text", "").strip()
    if not text:
        return error_msg("Missing 'text'")
    output = data.get("output", "/sdcard/DCIM/qrcode.png").strip()
    return execute(
        f"qrencode -o {shell_quote(output)} {shell_quote(text)} 2>/dev/null && "
        f"echo 'QR code saved to {output}' || echo 'Install qrencode: pkg install qrencode'"
    )


@register_tool(
    name="scan_barcode",
    description="Scan a barcode using the device camera.",
    schema={
        "type": "object",
        "properties": {
            "camera_id": {"type": "integer", "description": "Camera ID (default: 0)"},
            "output": {"type": "string", "description": "Output image path"},
        },
    },
    category="media",
    requires=[{"pkg": "zbarimg", "install": "pkg install zbar"}],
)
def handle_scan_barcode(data: dict) -> str:
    camera_id = shell_quote_num(data.get("camera_id", 0))
    output = data.get("output", "/sdcard/DCIM/barcode_capture.jpg").strip()
    return execute(
        f"termux-camera-photo -c {camera_id} {shell_quote(output)} 2>/dev/null && "
        f"zbarimg -q {shell_quote(output)} 2>/dev/null || echo 'Install zbar: pkg install zbar'"
    )


# ── Biometric / Fingerprint ───────────────────────────────────────────────

@register_tool(
    name="fingerprint",
    description="Authenticate using the device fingerprint scanner.",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_fingerprint(data: dict) -> str:
    return execute("termux-fingerprint 2>/dev/null && echo 'AUTH_SUCCESS' || echo 'AUTH_FAILED'")


# ── Toast / Dialog ────────────────────────────────────────────────────────

@register_tool(
    name="toast",
    description="Show a toast message on screen.",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Toast text"},
            "short_duration": {"type": "boolean", "description": "Short toast (default: true)"},
        },
        "required": ["text"],
    },
    category="device",
)
def handle_toast(data: dict) -> str:
    text = data.get("text", "").strip()
    if not text:
        return error_msg("Missing 'text'")
    short = str(data.get("short_duration", True)).lower() == "true"
    flags = " -s" if short else " -l"
    return execute(f"termux-toast{flags} {shell_quote(text)} 2>/dev/null && echo 'Toast shown' || echo 'Toast failed'")


@register_tool(
    name="dialog",
    description="Show a confirmation dialog on the device.",
    schema={
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Dialog title"},
            "message": {"type": "string", "description": "Dialog message"},
        },
        "required": ["message"],
    },
    category="device",
)
def handle_dialog(data: dict) -> str:
    title = data.get("title", "TermuxGPT").strip()
    msg = data.get("message", "").strip()
    if not msg:
        return error_msg("Missing 'message'")
    return execute(
        f"termux-dialog confirm -t {shell_quote(title)} -i {shell_quote(msg)} "
        f"2>/dev/null && echo 'Dialog shown' || echo 'Dialog failed'"
    )


# ── Sensors / Mic / STT / Media Player ────────────────────────────────────

@register_tool(
    name="sensor_read",
    description="Read device sensor data (accelerometer, gyroscope, magnetometer, etc.).",
    schema={
        "type": "object",
        "properties": {
            "sensor": {"type": "string", "description": "Sensor name (omit to list all sensors)"},
            "limit": {"type": "integer", "description": "Number of samples (default: 1)"},
        },
    },
    category="device",
)
def handle_sensor(data: dict) -> str:
    sensor_name = data.get("sensor", "").strip()
    limit = str(data.get("limit", 1))
    if sensor_name:
        return execute(f"termux-sensor -s {shell_quote(sensor_name)} -n {limit} 2>/dev/null || echo 'Sensor failed'")
    return execute("termux-sensor -l 2>/dev/null || echo 'Sensor list failed'")


@register_tool(
    name="microphone_record",
    description="Record audio from the device microphone.",
    schema={
        "type": "object",
        "properties": {
            "output": {"type": "string", "description": "Output audio file path"},
            "limit_seconds": {"type": "integer", "description": "Recording duration in seconds (default: 10)"},
            "action": {"type": "string", "enum": ["start", "stop"], "description": "Recording action"},
        },
    },
    category="media",
)
def handle_microphone_record(data: dict) -> str:
    output = data.get("output", "/sdcard/DCIM/termux_recording.mp3").strip()
    limit = shell_quote_num(data.get("limit_seconds", 10))
    action = data.get("action", "start").strip()
    if action == "stop":
        return execute("termux-microphone-record -q 2>/dev/null && echo 'Recording stopped' || echo 'Stop failed'")
    return execute(
        f"termux-microphone-record -l {limit} -f {shell_quote(output)} 2>/dev/null && echo 'Recording started' || echo 'Mic failed'"
    )


@register_tool(
    name="speech_to_text",
    description="Capture voice input and convert to text using device speech recognition.",
    schema={"type": "object", "properties": {}},
    category="media",
)
def handle_speech_to_text(data: dict) -> str:
    return execute("termux-speech-to-text 2>/dev/null || echo 'STT unavailable'")


@register_tool(
    name="media_player",
    description="Control media playback: play, pause, stop, info, next, previous.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["play", "pause", "stop", "info", "next", "previous"], "description": "Player action"},
        },
        "required": ["action"],
    },
    category="media",
)
def handle_media_player(data: dict) -> str:
    action = data.get("action", "info").strip()
    valid = ("play", "pause", "stop", "info", "next", "previous")
    if action not in valid:
        return error_msg(f"Action must be one of: {', '.join(valid)}")
    return execute(f"termux-media-player {action} 2>/dev/null || echo 'Media player failed'")


# ── Storage Get / Telephony ───────────────────────────────────────────────

@register_tool(
    name="storage_get",
    description="Prompt the user to pick a location and save a file.",
    schema={
        "type": "object",
        "properties": {"output": {"type": "string", "description": "Output file path"}},
        "required": ["output"],
    },
    category="device",
)
def handle_storage_get(data: dict) -> str:
    output = data.get("output", "").strip()
    if not output:
        return error_msg("Missing 'output' path")
    return execute(f"termux-storage-get {shell_quote(output)} 2>/dev/null && echo 'File saved to {output}' || echo 'Storage get failed'")


@register_tool(
    name="telephony_device",
    description="Get telephony device info: IMEI, network type, carrier (JSON).",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_telephony_deviceinfo(data: dict) -> str:
    return execute("termux-telephony-deviceinfo 2>/dev/null || echo '{}'")


@register_tool(
    name="telephony_cell",
    description="Get current cell tower information (JSON).",
    schema={"type": "object", "properties": {}},
    category="device",
)
def handle_telephony_cellinfo(data: dict) -> str:
    return execute("termux-telephony-cellinfo 2>/dev/null || echo '[]'")


@register_tool(
    name="infrared",
    description="Transmit an infrared signal (requires IR blaster hardware).",
    schema={
        "type": "object",
        "properties": {
            "frequency": {"type": "integer", "description": "Carrier frequency in Hz"},
            "pattern": {"type": "string", "description": "IR signal pattern"},
        },
        "required": ["frequency", "pattern"],
    },
    category="device",
)
def handle_infrared(data: dict) -> str:
    frequency = shell_quote_num(data.get("frequency", 0))
    pattern = data.get("pattern", "").strip()
    if not frequency or not pattern:
        return error_msg("Missing 'frequency' or 'pattern'")
    return execute(
        f"termux-infrared-transmit -f {frequency} {shell_quote(pattern)} 2>/dev/null && "
        f"echo 'IR transmitted' || echo 'IR failed - install termux-infrared'"
    )
