"""Development and utility tools."""

from ..registry import register_tool
from ..shell import execute, get_current_dir
from ..utils import error_msg, is_safe_path, shell_quote, shell_quote_num


@register_tool(
    name="speedtest",
    description="Run a network speed test.",
    schema={"type": "object", "properties": {}},
    category="tools",
    requires=[{"pkg": "speedtest-cli", "install": "pkg install speedtest-cli"}],
)
def handle_speedtest(data: dict) -> str:
    return execute("speedtest-cli --simple 2>/dev/null || echo 'Install: pkg install speedtest-cli'")


@register_tool(
    name="image_process",
    description="Process images: get info, resize, crop, rotate. Requires ImageMagick.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["info", "resize", "crop", "rotate"], "description": "Processing action"},
            "input": {"type": "string", "description": "Input image file path"},
            "output": {"type": "string", "description": "Output file path"},
            "width": {"type": "integer", "description": "Target width (resize)"},
            "height": {"type": "integer", "description": "Target height (resize)"},
            "x": {"type": "integer", "description": "Crop X offset"},
            "y": {"type": "integer", "description": "Crop Y offset"},
            "degrees": {"type": "number", "description": "Rotation degrees"},
        },
        "required": ["action", "input"],
    },
    category="tools",
    requires=[{"pkg": "identify", "install": "pkg install imagemagick"}],
)
def handle_image_process(data: dict) -> str:
    action = data.get("action", "info").strip()
    input_file = data.get("input", "").strip()
    output_file = data.get("output", "").strip()
    if not input_file:
        return error_msg("Missing 'input' path")
    if not is_safe_path(input_file):
        return error_msg("Path not allowed")
    safe_in = shell_quote(input_file)
    safe_out = shell_quote(output_file) if output_file else ""

    if action == "info":
        return execute(f"identify -verbose {safe_in} 2>/dev/null || echo 'Install: pkg install imagemagick'")
    elif action == "resize" and output_file:
        w = data.get("width", 800)
        h = data.get("height", 600)
        return execute(f"convert {safe_in} -resize {w}x{h}! {safe_out} 2>/dev/null && echo 'Resized to {w}x{h}' || echo 'Failed'")
    elif action == "crop" and output_file:
        w = data.get("width", 100)
        h = data.get("height", 100)
        x = data.get("x", 0)
        y = data.get("y", 0)
        return execute(f"convert {safe_in} -crop {w}x{h}+{x}+{y} {safe_out} 2>/dev/null && echo 'Cropped' || echo 'Failed'")
    elif action == "rotate" and output_file:
        degrees = data.get("degrees", 90)
        return execute(f"convert {safe_in} -rotate {degrees} {safe_out} 2>/dev/null && echo 'Rotated {degrees}°' || echo 'Failed'")
    return error_msg("Unknown action or missing output")


@register_tool(
    name="video_process",
    description="Process videos: get info, compress, extract audio, trim. Requires FFmpeg.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["info", "compress", "extract-audio", "trim"], "description": "Processing action"},
            "input": {"type": "string", "description": "Input video file path"},
            "output": {"type": "string", "description": "Output file path"},
            "crf": {"type": "integer", "description": "Compression quality (0-51, lower=better)"},
            "start": {"type": "string", "description": "Start time for trim (HH:MM:SS)"},
            "duration": {"type": "string", "description": "Duration for trim (HH:MM:SS)"},
        },
        "required": ["action", "input"],
    },
    category="tools",
    requires=[{"pkg": "ffmpeg", "install": "pkg install ffmpeg"}],
)
def handle_video_process(data: dict) -> str:
    action = data.get("action", "info").strip()
    input_file = data.get("input", "").strip()
    output_file = data.get("output", "").strip()
    if not input_file:
        return error_msg("Missing 'input' path")
    if not is_safe_path(input_file):
        return error_msg("Path not allowed")
    safe_in = shell_quote(input_file)
    safe_out = shell_quote(output_file) if output_file else ""

    if action == "info":
        return execute(f"ffprobe -v quiet -print_format json -show_format -show_streams {safe_in} 2>/dev/null || echo 'Install: pkg install ffmpeg'")
    elif action == "compress" and output_file:
        crf = data.get("crf", 28)
        return execute(f"ffmpeg -i {safe_in} -vcodec libx264 -crf {crf} {safe_out} 2>&1 | tail -5 || echo 'Failed'")
    elif action == "extract-audio" and output_file:
        return execute(f"ffmpeg -i {safe_in} -q:a 0 -map a {safe_out} 2>&1 | tail -3 || echo 'Failed'")
    elif action == "trim" and output_file:
        start = data.get("start", "00:00:00")
        duration = data.get("duration", 10)
        return execute(f"ffmpeg -i {safe_in} -ss {start} -t {duration} -c copy {safe_out} 2>&1 | tail -3 || echo 'Failed'")
    return error_msg("Unknown action or missing output")


@register_tool(
    name="text_extract",
    description="Extract text from images using OCR. Requires Tesseract.",
    schema={
        "type": "object",
        "properties": {
            "input": {"type": "string", "description": "Input image file path"},
            "lang": {"type": "string", "description": "OCR language (default: eng)"},
        },
        "required": ["input"],
    },
    category="tools",
    requires=[{"pkg": "tesseract", "install": "pkg install tesseract"}],
)
def handle_text_extract(data: dict) -> str:
    input_file = data.get("input", "").strip()
    lang = data.get("lang", "eng").strip()
    if not input_file:
        return error_msg("Missing 'input' path")
    if not is_safe_path(input_file):
        return error_msg("Path not allowed")
    return execute(f"tesseract {shell_quote(input_file)} stdout -l {lang} 2>/dev/null || echo 'Install: pkg install tesseract'")


@register_tool(
    name="public_ip",
    description="Get the device's public IP address.",
    schema={"type": "object", "properties": {}},
    category="tools",
    requires=[{"pkg": "curl", "install": "pkg install curl"}],
)
def handle_public_ip(data: dict) -> str:
    return execute("curl -s https://api.ipify.org 2>/dev/null || curl -s https://ifconfig.me 2>/dev/null || echo 'No internet'")


@register_tool(
    name="weather",
    description="Get current weather information for a city.",
    schema={
        "type": "object",
        "properties": {"city": {"type": "string", "description": "City name (optional, uses IP geolocation if omitted)"}},
    },
    category="tools",
    requires=[{"pkg": "curl", "install": "pkg install curl"}],
)
def handle_weather(data: dict) -> str:
    city = data.get("city", "").strip()
    if city:
        return execute(f"curl -s wttr.in/{shell_quote(city)}?format=3 2>/dev/null || echo 'Install curl: pkg install curl'")
    return execute("curl -s 'wttr.in/?format=3' 2>/dev/null || echo 'Install curl: pkg install curl'")


@register_tool(
    name="translate",
    description="Translate text between languages.",
    schema={
        "type": "object",
        "properties": {
            "text": {"type": "string", "description": "Text to translate"},
            "target_lang": {"type": "string", "description": "Target language code (default: en)"},
            "source_lang": {"type": "string", "description": "Source language code (default: auto)"},
        },
        "required": ["text"],
    },
    category="tools",
    requires=[{"pkg": "curl", "install": "pkg install curl"}],
)
def handle_translate(data: dict) -> str:
    text = data.get("text", "").strip()
    target = data.get("target_lang", "en").strip()
    source = data.get("source_lang", "auto").strip()
    if not text:
        return error_msg("Missing 'text'")
    return execute(
        f"curl -s \"https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl={source}&tl={target}&dt=t&q={shell_quote(text)}\" "
        f"2>/dev/null | python3 -c \"import sys,json; print(json.load(sys.stdin)[0][0][0])\" "
        f"2>/dev/null || echo 'Translation failed'"
    )


@register_tool(
    name="db_query",
    description="Execute a SQL query on a SQLite database.",
    schema={
        "type": "object",
        "properties": {
            "database": {"type": "string", "description": "SQLite database file path"},
            "query": {"type": "string", "description": "SQL query to execute"},
        },
        "required": ["database", "query"],
    },
    category="tools",
    requires=[{"pkg": "sqlite3", "install": "pkg install sqlite"}],
)
def handle_db_query(data: dict) -> str:
    db_path = data.get("database", "").strip()
    query = data.get("query", "").strip()
    if not db_path or not query:
        return error_msg("Missing 'database' or 'query'")
    if not is_safe_path(db_path):
        return error_msg("Path not allowed")
    return execute(f"sqlite3 {shell_quote(db_path)} {shell_quote(query)} 2>/dev/null || echo 'Install: pkg install sqlite'")


@register_tool(
    name="web_server",
    description="Start/stop a simple HTTP file server.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["start", "stop", "status"], "description": "Server action"},
            "port": {"type": "integer", "description": "Port number (default: 8080)"},
            "directory": {"type": "string", "description": "Directory to serve"},
        },
        "required": ["action"],
    },
    category="tools",
)
def handle_web_server(data: dict) -> str:
    action = data.get("action", "start").strip()
    port = shell_quote_num(data.get("port", 8080))
    directory = data.get("directory", get_current_dir()).strip()
    if action == "stop":
        return execute(f"pkill -f 'python3 -m http.server {port}' 2>/dev/null && echo 'Server stopped' || echo 'No server running'")
    elif action == "status":
        return execute(f"pgrep -f 'python3 -m http.server' >/dev/null 2>&1 && echo 'Server running' || echo 'Server not running'")
    return execute(f"cd {shell_quote(directory)} && python3 -m http.server {port} 2>&1")


@register_tool(
    name="git_op",
    description="Git operations: clone, status, log, diff, pull, push, branch.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["clone", "status", "log", "diff", "pull", "push", "branch"], "description": "Git action"},
            "url": {"type": "string", "description": "Repository URL (for clone)"},
            "directory": {"type": "string", "description": "Local directory path"},
            "repo_dir": {"type": "string", "description": "Repository directory"},
            "limit": {"type": "integer", "description": "Limit log entries"},
        },
        "required": ["action"],
    },
    category="tools",
)
def handle_git_op(data: dict) -> str:
    action = data.get("action", "clone").strip()
    repo_url = data.get("url", "").strip()
    directory = data.get("directory", "").strip()
    repo_dir = data.get("repo_dir", get_current_dir()).strip()

    if action == "clone":
        if not repo_url:
            return error_msg("Missing 'url' for clone")
        if directory:
            return execute(f"git clone {shell_quote(repo_url)} {shell_quote(directory)} 2>&1 | tail -10 || echo 'Clone failed'")
        return execute(f"git clone {shell_quote(repo_url)} 2>&1 | tail -10 || echo 'Clone failed'")
    elif action in ("status", "log", "diff", "pull", "push", "branch"):
        if not is_safe_path(repo_dir):
            return error_msg("Path not allowed")
        if action == "log":
            n = data.get("limit", 5)
            return execute(f"cd {shell_quote(repo_dir)} && git log --oneline -{n} 2>&1 || echo 'Git failed'")
        elif action == "branch":
            return execute(f"cd {shell_quote(repo_dir)} && git branch -a 2>&1 || echo 'Git failed'")
        return execute(f"cd {shell_quote(repo_dir)} && git {action} 2>&1 | tail -20 || echo 'Git failed'")
    return error_msg(f"Unknown action: {action}")
