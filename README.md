# Termux-MCP

[中文](README_CN.md) | English

A standalone MCP (Model Context Protocol) server for Termux on Android. Exposes 88+ tools covering shell execution, file operations, device control, media, and developer utilities via the standard MCP Streamable HTTP protocol. Designed for AI agents like MiClaw, Claude Desktop, Cursor, and any MCP-compatible client.

```text
MCP Client ──JSON-RPC 2.0──> POST /mcp ──> Termux-MCP ──> Tool Handler
  (MiClaw, Claude, etc.)       <── result ──     │
                                                  ├── shell_exec()
                                                  ├── file_read()
                                                  ├── battery_status()
                                                  └── ...88 tools
```

## Architecture

```
termux_mcp/
├── __main__.py          # Entry point (argparse + handler import)
├── mcp_server.py        # MCP Streamable HTTP server (JSON-RPC 2.0)
├── registry.py          # Central tool registry (@register_tool decorator)
├── config.py            # Environment-based configuration
├── shell.py             # Shell execution engine (streaming output)
├── utils.py             # Path safety, shell quoting, JSON helpers
└── handlers/
    ├── basic.py         # Shell, file, system basics
    ├── device.py        # Device, sensors, communication, media
    ├── tools.py         # Dev tools, git, diagnostics, utilities
    ├── ai_power.py      # AI-enhanced power features
    ├── terminal.py      # Terminal power-tools
    ├── features.py      # System, cron, backup, recipes
    └── history.py       # Command history
```

Tools are registered via the `@register_tool` decorator in each handler module. The registry auto-generates both MCP and OpenAI function-calling schemas from a single source of truth. No external dependencies — pure Python standard library.

## Quick Start

```bash
# One-time setup
pkg install python git -y
git clone -b main https://github.com/TruthZY/termux-mcp.git
cd termux-mcp
chmod +x start-mcp.sh
./start-mcp.sh
```

After the first run, just type `mcp` in any Termux session to start the server.

## Manual Start

```bash
cd ~/termux-mcp
python -m termux_mcp                    # Default: port 3000, bind 0.0.0.0
python -m termux_mcp --port 3000        # Custom port
python -m termux_mcp --host 127.0.0.1   # Local-only binding
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TERMUX_MCP_PORT` | `3000` | MCP server listen port |
| `TERMUX_MCP_HOST` | `0.0.0.0` | Bind address |
| `TERMUX_MCP_TIMEOUT` | `120` | Shell command timeout (seconds) |
| `TERMUX_MCP_AUTH_TOKEN` | *(none)* | API key for authentication |

Set `TERMUX_MCP_AUTH_TOKEN` (16+ characters) to require `X-API-Key` or `Authorization: Bearer` authentication on all requests.

## MCP Protocol

The server implements the [Model Context Protocol](https://modelcontextprotocol.io) over Streamable HTTP:

- **Endpoint**: `POST /mcp`
- **Protocol**: JSON-RPC 2.0
- **Methods**: `initialize`, `tools/list`, `tools/call`, `notifications/initialized`
- **Health check**: `GET /health`

### MiClaw Configuration

```json
{
  "mcpServers": {
    "termux-mcp": {
      "url": "http://127.0.0.1:3000/mcp"
    }
  }
}
```

### Claude Desktop / Cursor

```json
{
  "mcpServers": {
    "termux-mcp": {
      "url": "http://<phone-ip>:3000/mcp"
    }
  }
}
```

## Tools (88+)

### Shell & File

| Tool | Description |
|------|-------------|
| `shell_exec` | Execute shell command, streaming output |
| `shell_cancel` | Cancel running command |
| `file_list` | List directory contents |
| `file_read` | Read file (first 500 lines) |
| `file_write` | Write/create file |
| `file_mkdir` | Create directory (recursive) |
| `file_delete` | Delete file/directory (with confirmation) |
| `file_search` | Search files by pattern |

### Device & Sensors

| Tool | Description |
|------|-------------|
| `battery_status` | Battery level, charging, temperature |
| `vibrate` | Trigger haptic vibration |
| `torch` | Toggle flashlight |
| `wallpaper` | Set device wallpaper |
| `brightness` | Get/set screen brightness (0-255) |
| `volume` | Get/set audio stream volume |
| `sensor_read` | Read accelerometer, gyroscope, etc. |
| `fingerprint` | Fingerprint authentication |
| `infrared` | Transmit IR signal |

### Network & Location

| Tool | Description |
|------|-------------|
| `wifi_info` | Current WiFi connection details |
| `wifi_scan` | Scan nearby WiFi networks |
| `location` | GPS/network location |
| `public_ip` | Public IP address |

### Communication

| Tool | Description |
|------|-------------|
| `clipboard_get` / `clipboard_set` | Read/write system clipboard |
| `sms_send` / `sms_inbox` | Send/read SMS |
| `contacts` | List address book |
| `phone_call` | Dial a number |
| `notify` / `notify_remove` | System notifications |
| `share` | Android share sheet |
| `open_url` | Open URL in browser |

### Media & Camera

| Tool | Description |
|------|-------------|
| `camera_photo` / `camera_info` | Take photo / list cameras |
| `screenshot` | Capture screen |
| `screen_record` | Start/stop screen recording |
| `tts_speak` | Text-to-speech |
| `speech_to_text` | Voice recognition |
| `microphone_record` | Record audio |
| `media_player` | Playback control |
| `qrcode` / `scan_barcode` | Generate/scan QR codes |

### System & Process

| Tool | Description |
|------|-------------|
| `system_info` | CPU, RAM, disk, temperature, uptime |
| `process_list` / `process_kill` | Process management |
| `health` | Full system diagnostic |
| `env` / `ping` | Environment info / health check |

### Developer Tools

| Tool | Description |
|------|-------------|
| `git_op` | Git clone/status/log/diff/pull/push |
| `git_smart` | AI-friendly git (suggest commit, fix conflict) |
| `git_pr` | GitHub PR management |
| `review` | Code review (syntax check, lint) |
| `script_gen` | Generate shell/Python scripts |
| `regex_test` | Test regex patterns |
| `db_query` / `db_design` | SQLite queries / schema design |
| `explain` | Explain shell commands |
| `dev_env` | One-click dev environment setup |

### Utilities

| Tool | Description |
|------|-------------|
| `image_process` | Image operations (requires ImageMagick) |
| `video_process` | Video operations (requires FFmpeg) |
| `text_extract` | OCR text extraction (requires Tesseract) |
| `translate` | Text translation |
| `weather` | Weather query |
| `speedtest` | Network speed test |
| `download` | Download via system manager |
| `web_server` | Start/stop HTTP file server |
| `smart_install` | Smart package installation |
| `diagnose` | Environment diagnostics |
| `ssh_wizard` | SSH server setup |
| `backup` / `restore` | Backup and restore |
| `migrate` | Environment migration |
| `cron_add` / `cron_list` / `cron_remove` | Scheduled tasks |
| `recipe_save` / `recipe_run` | Automation recipes |

## Security

- Shell commands checked against risk patterns (fork bombs, `rm -rf /`, etc.)
- File paths validated against `/dev/`, `/proc/`, `/sys/` access
- API key authentication supported via `X-API-Key` or `Authorization: Bearer`
- Request body capped at 5 MB
- Dangerous operations require explicit confirmation

## License

MIT
