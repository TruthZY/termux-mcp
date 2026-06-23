"""
MCP Tool Definitions for Termux-MCP
=====================================
Complete tool catalog in MCP format (inputSchema using JSON Schema).
These are served via tools/list and define what MiClaw (or any MCP client)
can call.
"""

MCP_TOOLS: list[dict] = [

    # ═══════════════════════════════════════════════════════════════════════
    # Shell & File Operations
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "shell_exec",
        "description": "Execute a shell command in Termux and return the output. Supports streaming output. Dangerous commands require confirmation.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "Shell command to execute"},
                "confirmed": {"type": "boolean", "description": "Confirm dangerous commands (set true after risk warning)"}
            },
            "required": ["cmd"]
        }
    },
    {
        "name": "shell_cancel",
        "description": "Cancel the currently running shell command (sends SIGTERM).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "file_list",
        "description": "List files and directories. Returns names, sizes, and permissions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path (default: current dir)"},
                "bare": {"type": "boolean", "description": "Show only names without details"},
                "no_dotfiles": {"type": "boolean", "description": "Hide hidden files"}
            }
        }
    },
    {
        "name": "file_read",
        "description": "Read the contents of a file (first 500 lines).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to read"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_write",
        "description": "Write content to a file (creates or overwrites).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path to write"},
                "content": {"type": "string", "description": "Content to write"}
            },
            "required": ["path", "content"]
        }
    },
    {
        "name": "file_mkdir",
        "description": "Create a directory (including parent directories).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Directory path to create"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_delete",
        "description": "Delete a file or directory. Requires confirmation for safety.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Path to delete"},
                "recursive": {"type": "boolean", "description": "Delete directories recursively"},
                "confirmed": {"type": "boolean", "description": "Must be true to confirm deletion"}
            },
            "required": ["path"]
        }
    },
    {
        "name": "file_search",
        "description": "Search for files by name pattern. Returns up to 30 results.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "Base directory to search (default: .)"},
                "pattern": {"type": "string", "description": "Glob pattern (default: *)"},
                "name": {"type": "string", "description": "Alternative name filter"}
            }
        }
    },

    # ═══════════════════════════════════════════════════════════════════════
    # Device & Sensors
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "battery_status",
        "description": "Get battery status: level, charging state, temperature, voltage (JSON).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "vibrate",
        "description": "Trigger device haptic vibration.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "duration_ms": {"type": "integer", "description": "Vibration duration in milliseconds (default: 500)"}
            }
        }
    },
    {
        "name": "torch",
        "description": "Turn the flashlight (torch) on or off.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "state": {"type": "string", "enum": ["on", "off"], "description": "Torch state (default: on)"}
            }
        }
    },
    {
        "name": "wallpaper",
        "description": "Set device wallpaper from a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "Image file path"},
                "lockscreen": {"type": "boolean", "description": "Set as lock screen wallpaper"}
            }
        }
    },
    {
        "name": "brightness",
        "description": "Get or set screen brightness (0-255). Omit 'level' to read current value.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "description": "Brightness level 0-255 (omit to read current)"}
            }
        }
    },
    {
        "name": "volume",
        "description": "Get or set audio stream volume. Streams: ring, alarm, music, notification, system, voice_call.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "stream": {"type": "string", "description": "Audio stream (default: music)"},
                "level": {"type": "string", "description": "Volume level (omit to read current)"}
            }
        }
    },
    {
        "name": "sensor_read",
        "description": "Read device sensor data (accelerometer, gyroscope, magnetometer, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sensor": {"type": "string", "description": "Sensor name (omit to list all sensors)"},
                "limit": {"type": "integer", "description": "Number of samples (default: 1)"}
            }
        }
    },
    {
        "name": "fingerprint",
        "description": "Authenticate using the device fingerprint scanner.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "infrared",
        "description": "Transmit an infrared signal (requires IR blaster hardware).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "frequency": {"type": "integer", "description": "Carrier frequency in Hz"},
                "pattern": {"type": "string", "description": "IR signal pattern"}
            },
            "required": ["frequency", "pattern"]
        }
    },

    # ═══════════════════════════════════════════════════════════════════════
    # Network & Location
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "wifi_info",
        "description": "Get current WiFi connection info: SSID, IP, signal strength, frequency (JSON).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "wifi_scan",
        "description": "Get recent WiFi scan results: available networks and signal strength (JSON array).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "location",
        "description": "Get device GPS/network location: latitude, longitude, accuracy, altitude.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "provider": {"type": "string", "enum": ["gps", "network", "passive"], "description": "Location provider (default: gps)"}
            }
        }
    },
    {
        "name": "public_ip",
        "description": "Get the device's public IP address.",
        "inputSchema": {"type": "object", "properties": {}}
    },

    # ═══════════════════════════════════════════════════════════════════════
    # Communication
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "clipboard_get",
        "description": "Read text from the system clipboard.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "clipboard_set",
        "description": "Write text to the system clipboard.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to write to clipboard"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "sms_send",
        "description": "Send an SMS message. ⚠️ This actually sends an SMS.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number": {"type": "string", "description": "Phone number"},
                "text": {"type": "string", "description": "Message content"}
            },
            "required": ["number", "text"]
        }
    },
    {
        "name": "sms_inbox",
        "description": "List recent SMS messages from inbox.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Number of messages (default: 10)"}
            }
        }
    },
    {
        "name": "contacts",
        "description": "List all contacts from the device address book (JSON array).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "phone_call",
        "description": "Dial a phone number. ⚠️ This actually initiates a call.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "number": {"type": "string", "description": "Phone number to call"}
            },
            "required": ["number"]
        }
    },
    {
        "name": "notify",
        "description": "Send a system notification with title, content, and optional priority.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Notification title"},
                "content": {"type": "string", "description": "Notification body text"},
                "priority": {"type": "string", "description": "Priority: low, default, high, max"},
                "id": {"type": "string", "description": "Notification ID for updates/removal"},
                "ongoing": {"type": "boolean", "description": "Make notification persistent"}
            },
            "required": ["content"]
        }
    },
    {
        "name": "notify_remove",
        "description": "Remove a notification by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string", "description": "Notification ID to remove"}
            },
            "required": ["id"]
        }
    },
    {
        "name": "share",
        "description": "Share text or a file via Android share sheet.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to share"},
                "file": {"type": "string", "description": "File path to share"}
            }
        }
    },
    {
        "name": "open_url",
        "description": "Open a URL in the default browser or appropriate app.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to open"}
            },
            "required": ["url"]
        }
    },

    # ═══════════════════════════════════════════════════════════════════════
    # Media & Camera
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "camera_photo",
        "description": "Take a photo using the device camera and save as JPEG.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "camera_id": {"type": "integer", "description": "Camera ID (0=rear, 1=front, default: 0)"},
                "output": {"type": "string", "description": "Output file path (default: auto-generated)"}
            }
        }
    },
    {
        "name": "camera_info",
        "description": "List device camera hardware specs (resolution, focus modes, etc.).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "screenshot",
        "description": "Take a screenshot of the current screen.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output": {"type": "string", "description": "Output file path (default: auto-generated)"}
            }
        }
    },
    {
        "name": "screen_record",
        "description": "Start or stop screen recording.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["start", "stop"], "description": "Recording action (default: start)"},
                "output": {"type": "string", "description": "Output file path"}
            }
        }
    },
    {
        "name": "tts_speak",
        "description": "Speak text aloud using the device TTS engine.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to speak"},
                "rate": {"type": "number", "description": "Speech rate (default: 1.0)"},
                "pitch": {"type": "number", "description": "Speech pitch (default: 1.0)"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "speech_to_text",
        "description": "Capture voice input and convert to text using device speech recognition.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "microphone_record",
        "description": "Record audio from the device microphone.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output": {"type": "string", "description": "Output audio file path"},
                "limit_seconds": {"type": "integer", "description": "Recording duration in seconds (default: 10)"},
                "action": {"type": "string", "enum": ["start", "stop"], "description": "Recording action"}
            }
        }
    },
    {
        "name": "media_player",
        "description": "Control media playback: play, pause, stop, info, next, previous.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["play", "pause", "stop", "info", "next", "previous"], "description": "Player action"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "qrcode",
        "description": "Generate a QR code image from text.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to encode in QR code"},
                "output": {"type": "string", "description": "Output image path (default: qrcode.png)"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "scan_barcode",
        "description": "Scan a barcode using the device camera.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "camera_id": {"type": "integer", "description": "Camera ID (default: 0)"},
                "output": {"type": "string", "description": "Output image path"}
            }
        }
    },

    # ═══════════════════════════════════════════════════════════════════════
    # System & Process Management
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "system_info",
        "description": "Get system info: CPU usage, RAM, disk, temperature, uptime (JSON).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "process_list",
        "description": "List running processes with CPU/memory usage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Max processes to show (default: 20)"}
            }
        }
    },
    {
        "name": "process_kill",
        "description": "Kill a process by PID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pid": {"type": "integer", "description": "Process ID to kill"},
                "signal": {"type": "integer", "description": "Signal number (default: 15 SIGTERM)"}
            },
            "required": ["pid"]
        }
    },
    {
        "name": "health",
        "description": "Run a full system health diagnostic check.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "env",
        "description": "Get current environment: working directory, home path, PIDs.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "ping",
        "description": "Health check / ping. Returns server status and current working directory.",
        "inputSchema": {"type": "object", "properties": {}}
    },

    # ═══════════════════════════════════════════════════════════════════════
    # Tools & Utilities
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "download",
        "description": "Download a file using Android's download manager.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "URL to download"},
                "description": {"type": "string", "description": "Download description"},
                "title": {"type": "string", "description": "Download title"}
            },
            "required": ["url"]
        }
    },
    {
        "name": "list_apps",
        "description": "List installed applications on the device (JSON).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "speedtest",
        "description": "Run a network speed test.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "image_process",
        "description": "Process images: get info, resize, crop, rotate. Requires ImageMagick.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["info", "resize", "crop", "rotate"], "description": "Processing action"},
                "input": {"type": "string", "description": "Input image file path"},
                "output": {"type": "string", "description": "Output file path"},
                "width": {"type": "integer", "description": "Target width (resize)"},
                "height": {"type": "integer", "description": "Target height (resize)"},
                "x": {"type": "integer", "description": "Crop X offset"},
                "y": {"type": "integer", "description": "Crop Y offset"},
                "degrees": {"type": "number", "description": "Rotation degrees"}
            },
            "required": ["action", "input"]
        }
    },
    {
        "name": "video_process",
        "description": "Process videos: get info, compress, extract audio, trim. Requires FFmpeg.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["info", "compress", "extract-audio", "trim"], "description": "Processing action"},
                "input": {"type": "string", "description": "Input video file path"},
                "output": {"type": "string", "description": "Output file path"},
                "crf": {"type": "integer", "description": "Compression quality (0-51, lower=better)"},
                "start": {"type": "string", "description": "Start time for trim (HH:MM:SS)"},
                "duration": {"type": "string", "description": "Duration for trim (HH:MM:SS)"}
            },
            "required": ["action", "input"]
        }
    },
    {
        "name": "text_extract",
        "description": "Extract text from images using OCR. Requires Tesseract.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "input": {"type": "string", "description": "Input image file path"},
                "lang": {"type": "string", "description": "OCR language (default: eng)"}
            },
            "required": ["input"]
        }
    },
    {
        "name": "weather",
        "description": "Get current weather information for a city.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name (optional, uses IP geolocation if omitted)"}
            }
        }
    },
    {
        "name": "translate",
        "description": "Translate text between languages.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "text": {"type": "string", "description": "Text to translate"},
                "target_lang": {"type": "string", "description": "Target language code (default: en)"},
                "source_lang": {"type": "string", "description": "Source language code (default: auto)"}
            },
            "required": ["text"]
        }
    },
    {
        "name": "db_query",
        "description": "Execute a SQL query on a SQLite database.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "database": {"type": "string", "description": "SQLite database file path"},
                "query": {"type": "string", "description": "SQL query to execute"}
            },
            "required": ["database", "query"]
        }
    },
    {
        "name": "web_server",
        "description": "Start/stop a simple HTTP file server.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["start", "stop", "status"], "description": "Server action"},
                "port": {"type": "integer", "description": "Port number (default: 8080)"},
                "directory": {"type": "string", "description": "Directory to serve"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "git_op",
        "description": "Git operations: clone, status, log, diff, pull, push, branch.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["clone", "status", "log", "diff", "pull", "push", "branch"], "description": "Git action"},
                "url": {"type": "string", "description": "Repository URL (for clone)"},
                "directory": {"type": "string", "description": "Local directory path"},
                "repo_dir": {"type": "string", "description": "Repository directory"},
                "limit": {"type": "integer", "description": "Limit log entries"}
            },
            "required": ["action"]
        }
    },

    # ═══════════════════════════════════════════════════════════════════════
    # Terminal Power-Tools
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "diagnose",
        "description": "Diagnose development environment issues (Python, Node, Git, packages, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": ["python", "pip", "node", "git", "storage", "packages", "all"], "description": "What to diagnose (default: python)"}
            }
        }
    },
    {
        "name": "pkg_smart",
        "description": "Smart package installation with dependency resolution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "description": "Package name or description of what to install"},
                "install": {"type": "boolean", "description": "Actually install (false = dry run)"}
            },
            "required": ["intent"]
        }
    },
    {
        "name": "explain",
        "description": "Explain what a shell command does in plain language.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "cmd": {"type": "string", "description": "Command to explain"}
            },
            "required": ["cmd"]
        }
    },
    {
        "name": "dev_env",
        "description": "Set up a development environment for a specific language/framework.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "intent": {"type": "string", "enum": ["python", "bot", "react", "node", "c", "rust", "data", "termux"], "description": "Environment type"},
                "name": {"type": "string", "description": "Project name (default: myproject)"}
            },
            "required": ["intent"]
        }
    },
    {
        "name": "review",
        "description": "Review a code file: syntax check, linting, suggestions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "File path to review"}
            },
            "required": ["file"]
        }
    },
    {
        "name": "log_analyze",
        "description": "Analyze a log file and extract errors/warnings.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "Log file path to analyze"}
            },
            "required": ["file"]
        }
    },
    {
        "name": "script_gen",
        "description": "Generate a shell or Python script from a description.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "description": {"type": "string", "description": "What the script should do"},
                "type": {"type": "string", "enum": ["sh", "py"], "description": "Script type (sh or py)"},
                "output": {"type": "string", "description": "Output file path"}
            },
            "required": ["description"]
        }
    },
    {
        "name": "deps_tree",
        "description": "Show dependency tree for a package.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "package": {"type": "string", "description": "Package name (optional)"}
            }
        }
    },
    {
        "name": "storage_audit",
        "description": "Audit storage usage: disk usage, caches, cleanup suggestions.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "config_fix",
        "description": "Fix common configuration issues (bashrc, zshrc, termux settings, fonts, etc.).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "config": {"type": "string", "enum": ["bashrc", "zshrc", "termux", "font", "colors", "storage", "path", "env", "all"], "description": "Config to fix"}
            }
        }
    },
    {
        "name": "git_smart",
        "description": "Smart Git operations: diff summary, recent log, commit suggestions, conflict resolution.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "description": "diff-summary, log-recent, suggest-commit, fix-conflict, or raw git command"},
                "repo_dir": {"type": "string", "description": "Repository directory"},
                "limit": {"type": "integer", "description": "Limit results"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "regex_test",
        "description": "Test a regular expression pattern against sample text.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regular expression pattern"},
                "test": {"type": "string", "description": "Test string to match against"}
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "db_design",
        "description": "Design a database schema from a description and generate SQL.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schema": {"type": "string", "description": "Schema description"},
                "output": {"type": "string", "description": "Output SQL file path"}
            },
            "required": ["schema"]
        }
    },
    {
        "name": "backup",
        "description": "Backup Termux home, packages, or configs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "enum": ["home", "packages", "configs"], "description": "What to backup"},
                "output": {"type": "string", "description": "Output archive path"},
                "include": {"type": "string", "description": "Comma-separated extra paths to include"}
            },
            "required": ["target"]
        }
    },
    {
        "name": "restore",
        "description": "Restore from a backup archive.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "Backup archive file path"},
                "target": {"type": "string", "enum": ["home", "packages", "configs", "info"], "description": "What to restore"}
            },
            "required": ["file"]
        }
    },

    # ═══════════════════════════════════════════════════════════════════════
    # AI Power Features
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "smart_install",
        "description": "Intelligently install packages with auto-detection of package manager.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "packages": {"type": "string", "description": "Packages to install (space or comma separated)"},
                "manager": {"type": "string", "enum": ["auto", "pkg", "pip", "npm"], "description": "Package manager (default: auto)"},
                "dry_run": {"type": "boolean", "description": "Preview without installing"}
            },
            "required": ["packages"]
        }
    },
    {
        "name": "permission_fix",
        "description": "Diagnose and fix common permission issues.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string", "enum": ["storage", "files", "api", "network", "termux", "all"], "description": "Permission area to fix"}
            }
        }
    },
    {
        "name": "profile",
        "description": "Apply a Termux profile preset (dev, python, web, hacker, writer, minimal).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "profile": {"type": "string", "enum": ["dev", "python", "web", "hacker", "writer", "minimal"], "description": "Profile to apply"},
                "dry_run": {"type": "boolean", "description": "Preview changes without applying"}
            }
        }
    },
    {
        "name": "error_explain",
        "description": "Explain an error message and suggest fixes.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "error": {"type": "string", "description": "Error message text"},
                "command": {"type": "string", "description": "Command that produced the error"}
            }
        }
    },
    {
        "name": "ssh_wizard",
        "description": "Set up, check, or stop SSH server on Termux.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["setup", "status", "stop"], "description": "SSH action"}
            }
        }
    },
    {
        "name": "service_guard",
        "description": "Manage background services: list, start, stop, wake lock.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "start", "stop", "wake-lock", "wake-release"], "description": "Service action"},
                "name": {"type": "string", "description": "Service name"},
                "cmd": {"type": "string", "description": "Command to run as service (for start)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "history_insight",
        "description": "Analyze shell command history for patterns and insights.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "History file path (default: ~/.bash_history)"},
                "limit": {"type": "integer", "description": "Number of entries to analyze (default: 100)"}
            }
        }
    },
    {
        "name": "optimize",
        "description": "Analyze and optimize Termux: memory, CPU, disk usage, and recommendations.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "quick_cmd",
        "description": "Manage quick command aliases: list, add, remove, export.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "add", "remove", "export"], "description": "Quick command action"},
                "name": {"type": "string", "description": "Command alias name"},
                "cmd": {"type": "string", "description": "Command to alias (for add)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "port_manage",
        "description": "Manage network ports: list active, check specific port, show IP info.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "check", "ip"], "description": "Port action"},
                "port": {"type": "string", "description": "Port number to check"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "migrate",
        "description": "Backup/restore Termux environment for migration to another device.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["backup", "restore", "preview"], "description": "Migration action"},
                "output": {"type": "string", "description": "Output file path (for backup)"},
                "file": {"type": "string", "description": "Input file path (for restore)"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "tutorial",
        "description": "Show interactive Termux tutorials.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "topic": {"type": "string", "enum": ["basics", "python", "ssh", "storage", "customize"], "description": "Tutorial topic"}
            }
        }
    },

    # ═══════════════════════════════════════════════════════════════════════
    # Extended Features
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "cron_add",
        "description": "Schedule a recurring command using Termux cron.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "schedule": {"type": "string", "description": "Cron schedule expression"},
                "command": {"type": "string", "description": "Command to run"},
                "label": {"type": "string", "description": "Job label for identification"}
            },
            "required": ["schedule", "command"]
        }
    },
    {
        "name": "cron_list",
        "description": "List all scheduled cron jobs.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "cron_remove",
        "description": "Remove a scheduled cron job by label.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "description": "Job label to remove"}
            }
        }
    },
    {
        "name": "diff_files",
        "description": "Show differences between two files (or a file and its backup).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "First file path"},
                "file2": {"type": "string", "description": "Second file path (optional)"}
            },
            "required": ["file"]
        }
    },
    {
        "name": "patch_file",
        "description": "Apply a unified diff patch to a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "file": {"type": "string", "description": "File to patch"},
                "patch": {"type": "string", "description": "Patch content (unified diff format)"}
            },
            "required": ["file", "patch"]
        }
    },
    {
        "name": "cloud_sync",
        "description": "Sync files to/from cloud storage.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["backup", "restore", "list"], "description": "Sync action"},
                "target": {"type": "string", "description": "Target path"},
                "output": {"type": "string", "description": "Output path"},
                "file": {"type": "string", "description": "File path for restore"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "git_pr",
        "description": "Manage GitHub pull requests: list, view, diff, merge, approve, create.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "action": {"type": "string", "enum": ["list", "view", "diff", "merge", "approve", "status", "create"], "description": "PR action"},
                "repo": {"type": "string", "description": "Repository (owner/name)"},
                "number": {"type": "integer", "description": "PR number"},
                "state": {"type": "string", "description": "PR state filter (open/closed/all)"},
                "limit": {"type": "integer", "description": "Limit results"},
                "title": {"type": "string", "description": "PR title (for create)"},
                "body": {"type": "string", "description": "PR body (for create)"},
                "base": {"type": "string", "description": "Base branch (for create)"},
                "draft": {"type": "boolean", "description": "Create as draft PR"}
            },
            "required": ["action"]
        }
    },
    {
        "name": "recipe_list",
        "description": "List saved automation recipes.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "recipe_run",
        "description": "Run a saved automation recipe by name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe": {"type": "string", "description": "Recipe name to run"}
            }
        }
    },
    {
        "name": "recipe_save",
        "description": "Save a multi-step automation recipe.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "recipe": {"type": "string", "description": "Recipe identifier"},
                "name": {"type": "string", "description": "Display name"},
                "desc": {"type": "string", "description": "Description"},
                "steps": {"type": "array", "items": {"type": "string"}, "description": "List of shell commands to execute"}
            },
            "required": ["recipe", "name", "steps"]
        }
    },
    {
        "name": "context",
        "description": "Get current Termux context: hostname, packages, environment info.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "context_save",
        "description": "Save current context snapshot for later reference.",
        "inputSchema": {"type": "object", "properties": {}}
    },

    # ═══════════════════════════════════════════════════════════════════════
    # History
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "history_list",
        "description": "List command execution history.",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "history_save",
        "description": "Save a command execution record to history.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "raw_input": {"type": "string", "description": "Command that was run"},
                "output": {"type": "string", "description": "Command output"},
                "success": {"type": "boolean", "description": "Whether the command succeeded"}
            }
        }
    },
    {
        "name": "history_clear",
        "description": "Clear all command execution history.",
        "inputSchema": {"type": "object", "properties": {}}
    },

    # ═══════════════════════════════════════════════════════════════════════
    # Telephony Extended
    # ═══════════════════════════════════════════════════════════════════════

    {
        "name": "telephony_device",
        "description": "Get telephony device info: IMEI, network type, carrier (JSON).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "telephony_cell",
        "description": "Get current cell tower information (JSON).",
        "inputSchema": {"type": "object", "properties": {}}
    },
    {
        "name": "storage_get",
        "description": "Prompt the user to pick a location and save a file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "output": {"type": "string", "description": "Output file path"}
            },
            "required": ["output"]
        }
    },
]
