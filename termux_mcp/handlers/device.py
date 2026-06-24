"""Device, media, and communication tools (complex logic only).

Simple termux-* command wrappers have been removed — use shell_exec instead.
See docs/removed-tools.md for the full list of removed tools and their
equivalent shell commands.
"""

from ..registry import register_tool
from ..shell import execute
from ..utils import error_msg, is_safe_path, shell_quote, shell_quote_num


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


# ── Storage Get / Telephony / IR ──────────────────────────────────────────

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
