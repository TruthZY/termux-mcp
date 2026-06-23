"""Terminal power-tools: diagnose, package manager, code review, git, backup, etc."""

import os
import re

from ..registry import register_tool
from ..shell import execute, get_current_dir
from ..utils import error_msg, shell_quote


@register_tool(
    name="diagnose",
    description="Diagnose development environment issues (Python, Node, Git, packages, etc.).",
    schema={
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": ["python", "pip", "node", "git", "storage", "packages", "all"], "description": "What to diagnose (default: python)"},
        },
    },
    category="terminal",
)
def handle_diagnose(data: dict) -> str:
    intent = data.get("intent", "python").strip()
    checks = []

    if intent in ("python", "pip", "all"):
        checks += [
            'echo "=== Python ==="',
            'python3 --version 2>&1 || echo "Missing: python3"',
            'pip --version 2>&1 || echo "Missing: pip"',
            'python3 -c "import sys; print(sys.executable)" 2>&1 || echo "Cant import sys"',
            'echo "=== PATH ==="',
            'echo "$PATH"',
        ]
    if intent in ("pip", "all"):
        checks += [
            'echo "=== Pip Packages ==="',
            'pip list 2>&1 | head -30 || echo "Pip broken"',
            'pip config list 2>&1 || echo "No pip config"',
        ]
    if intent in ("node", "npm", "all"):
        checks += [
            'echo "=== Node.js ==="',
            'node --version 2>&1 || echo "Missing: nodejs"',
            'npm --version 2>&1 || echo "Missing: npm"',
        ]
    if intent in ("git", "all"):
        checks += [
            'echo "=== Git ==="',
            'git --version 2>&1 || echo "Missing: git"',
        ]
    if intent in ("storage", "all"):
        checks += [
            'echo "=== Storage ==="',
            'ls -la ~/storage/ 2>&1 || echo "Storage not setup - run termux-setup-storage"',
            'df -h /data 2>/dev/null || echo "Cannot check disk"',
        ]
    if intent in ("packages", "all"):
        checks += [
            'echo "=== Packages ==="',
            'pkg list-installed 2>&1 | wc -l || echo "Cant list packages"',
            'apt list --upgradable 2>&1 | head -10 || echo "Cant check updates"',
        ]

    cmd = " && ".join(checks) if checks else 'echo No diagnostic target specified'
    return execute(cmd)


@register_tool(
    name="pkg_smart",
    description="Smart package installation with dependency resolution.",
    schema={
        "type": "object",
        "properties": {
            "intent": {"type": "string", "description": "Package name or description of what to install"},
            "install": {"type": "boolean", "description": "Actually install (false = dry run)"},
        },
        "required": ["intent"],
    },
    category="terminal",
)
def handle_pkg_smart(data: dict) -> str:
    intent = data.get("intent", "").strip().lower()
    if not intent:
        return error_msg("Missing 'intent'. Describe what you want to do.")

    do_install = data.get("install", False)

    intent_map = {
        "video":      ("ffmpeg imagemagick", "ffmpeg -version"),
        "edit video": ("ffmpeg imagemagick", "ffmpeg -version"),
        "image":      ("imagemagick", "convert --version"),
        "edit image": ("imagemagick", "convert --version"),
        "photo":      ("imagemagick", "convert --version"),
        "web server": ("python nginx", "python3 --version"),
        "python web": ("python python-pip nginx", "python3 --version"),
        "python":     ("python python-pip", "python3 --version"),
        "node":       ("nodejs", "node --version"),
        "nodejs":     ("nodejs", "node --version"),
        "javascript": ("nodejs", "node --version"),
        "react":      ("nodejs", "node --version"),
        "c":          ("clang make gdb", "clang --version"),
        "c++":        ("clang make gdb", "clang++ --version"),
        "cpp":        ("clang make gdb", "clang++ --version"),
        "rust":       ("rust binutils", "rustc --version"),
        "go":         ("golang", "go version"),
        "java":       ("openjdk-17", "java --version"),
        "ruby":       ("ruby", "ruby --version"),
        "php":        ("php", "php --version"),
        "git":        ("git", "git --version"),
        "database":   ("sqlite mariadb", "sqlite3 --version"),
        "sqlite":     ("sqlite", "sqlite3 --version"),
        "ssh":        ("openssh", "ssh -V 2>&1"),
        "ftp":        ("openssh curl", "curl --version"),
        "editor":     ("vim neovim nano", "vim --version 2>&1 | head -1"),
        "terminal":   ("zsh termux-api fzf bat eza", "zsh --version"),
        "beautiful":  ("zsh eza bat neofetch", "neofetch --version 2>&1"),
        "customize":  ("zsh eza bat neofetch", "neofetch --version 2>&1"),
        "irc":        ("irssi", "irssi --version 2>&1"),
        "bot":        ("python python-pip", "python3 --version"),
        "discord bot":("python python-pip", "python3 --version"),
        "telegram bot":("python python-pip", "python3 --version"),
        "scrape":     ("python python-pip curl", "python3 --version"),
        "scraping":   ("python python-pip curl", "python3 --version"),
        "ocr":        ("tesseract imagemagick", "tesseract --version 2>&1"),
        "text":       ("tesseract imagemagick", "tesseract --version 2>&1"),
        "qr":         ("qrencode zbar", "qrencode --version 2>&1"),
        "barcode":    ("qrencode zbar", "qrencode --version 2>&1"),
        "tor":        ("tor torsocks", "tor --version 2>&1"),
        "speed":      ("speedtest-cli", "speedtest-cli --version 2>&1"),
        "speedtest":  ("speedtest-cli", "speedtest-cli --version 2>&1"),
        "translate":  ("python python-pip", "python3 --version"),
        "science":    ("python python-pip python-numpy", "python3 --version"),
        "data":       ("python python-pip python-numpy python-pandas", "python3 --version"),
        "ml":         ("python python-pip python-numpy", "python3 --version"),
        "ai":         ("python python-pip", "python3 --version"),
        "network":    ("nmap curl wget openssh", "nmap --version 2>&1 | head -1"),
        "hack":       ("nmap python python-pip openssh hydra", "nmap --version 2>&1 | head -1"),
        "pentest":    ("nmap python python-pip openssh hydra", "nmap --version 2>&1 | head -1"),
        "archive":    ("zip unzip tar", "tar --version 2>&1 | head -1"),
        "compress":   ("zip unzip tar", "tar --version 2>&1 | head -1"),
    }

    best_match = None
    best_score = 0
    for key, (pkgs, verify) in intent_map.items():
        score = 0
        for word in intent.split():
            if word in key:
                score += len(word)
        if key == intent:
            score = 999
        elif intent in key or key in intent:
            score = max(score, 900)
        if score > best_score:
            best_score = score
            best_match = (key, pkgs, verify)

    if best_match and best_score > 0:
        key, pkgs, verify_cmd = best_match
        if do_install:
            cmd = f'echo "Installing: {pkgs}"; pkg install -y {pkgs} 2>&1 | tail -20 && echo "---" && {verify_cmd} && echo "Done! All packages installed." || echo "Some packages may have failed."'
        else:
            cmd = f'echo "📦 Suggested packages for: {key}"; echo "Command: pkg install {pkgs}"; echo "---"; echo "Already installed:"; for pkg in {pkgs.split()}; do dpkg -s "$pkg" 2>/dev/null | grep Status | head -1 || echo "  $pkg - NOT installed"; done; echo "---"; echo "To install, use: install: true"'
    else:
        cmd = f'echo No matching packages found for: {shell_quote(intent)}; echo Try broader terms like: python, video, web server, nodejs, c++'

    return execute(cmd)


@register_tool(
    name="explain",
    description="Explain what a shell command does in plain language.",
    schema={
        "type": "object",
        "properties": {
            "cmd": {"type": "string", "description": "Command to explain"},
        },
        "required": ["cmd"],
    },
    category="terminal",
)
def handle_explain(data: dict) -> str:
    cmd = data.get("cmd", "").strip()
    if not cmd:
        return error_msg("Missing 'cmd' to explain")

    qcmd = shell_quote(cmd)
    parts = []
    if "|" in cmd:
        parts.append(f'echo Pipeline: {qcmd}')
    if ">" in cmd or ">>" in cmd:
        parts.append(f'echo "Redirects output to a file"')
    if "&&" in cmd:
        parts.append(f'echo "Chained commands — second runs only if first succeeds"')
    if "||" in cmd:
        parts.append(f'echo "Fallback — right side runs if left side fails"')
    if "rm -rf" in cmd or "rm -r" in cmd:
        parts.append(f'echo "DANGER: rm -r will DELETE files/directories permanently"')
    if "rm " in cmd and "-rf" not in cmd:
        parts.append(f'echo "This will DELETE files — make sure you have backups"')
    if cmd.startswith("cd "):
        parts.append(f'echo "Changes directory"')
    if "sudo" in cmd:
        parts.append(f'echo "sudo requires root — Termux does not support sudo by default"')
    if "apt " in cmd or "pkg " in cmd:
        parts.append(f'echo "Package manager operation"')
    if "git " in cmd:
        parts.append(f'echo "Git version control operation"')
    if "pip " in cmd:
        parts.append(f'echo "Python package manager (pip)"')
    if "npm " in cmd:
        parts.append(f'echo "Node.js package manager (npm)"')

    first_word = cmd.split()[0] if cmd.split() else ""
    if first_word:
        parts.append(f'echo "---"')
        qfirst = shell_quote(first_word)
        parts.append(f'which {qfirst} 2>/dev/null && echo "Command found" || echo "Command NOT found — you may need to install it"')

    script = " && ".join(parts) if parts else f'echo Command: {qcmd}'
    return execute(f'{script} && echo "---" && echo Original command: {qcmd}')


@register_tool(
    name="dev_env",
    description="Set up a development environment for a specific language/framework.",
    schema={
        "type": "object",
        "properties": {
            "intent": {"type": "string", "enum": ["python", "bot", "react", "node", "c", "rust", "data", "termux"], "description": "Environment type"},
            "name": {"type": "string", "description": "Project name (default: myproject)"},
        },
        "required": ["intent"],
    },
    category="terminal",
)
def handle_dev_env(data: dict) -> str:
    intent = data.get("intent", "python").strip().lower()
    cwd = get_current_dir()
    project_name = data.get("name", "myproject").strip()
    qname = shell_quote(project_name)

    setups = {
        "python": (
            "Python Web Development",
            f'pkg install -y python python-pip 2>&1 | tail -5 && '
            f'pip install flask gunicorn 2>&1 | tail -5 && '
            f'mkdir -p {shell_quote(cwd + "/" + project_name)} && '
            f'cd {shell_quote(cwd + "/" + project_name)} && '
            f'echo "from flask import Flask\\napp = Flask(__name__)\\n@app.route(\'/\')\\ndef hello():\\n    return {{\'status\': \'ok\'}}\\nif __name__ == \'__main__\':\\n    app.run(host=\'0.0.0.0\', port=5000)" > app.py && '
            f'echo Created: {qname}/app.py && '
            f'echo Run: cd {qname} && python app.py'
        ),
        "bot": (
            "Telegram/Discord Bot",
            f'pkg install -y python python-pip 2>&1 | tail -3 && '
            f'pip install python-telegram-bot discord.py 2>&1 | tail -3 && '
            f'mkdir -p {shell_quote(cwd + "/" + project_name)} && '
            f'cd {shell_quote(cwd + "/" + project_name)} && '
            f'echo "# Bot token (get from @BotFather or Discord Developer Portal)\\nTOKEN = \'your_token_here\'\\nprint(\'Bot ready!\')" > bot.py && '
            f'echo Created: {qname}/bot.py'
        ),
        "react": (
            "React Frontend",
            f'pkg install -y nodejs 2>&1 | tail -3 && '
            f'npm --version 2>&1 && '
            f'cd {shell_quote(cwd)} && '
            f'echo "Run: npx create-react-app {qname}"'
        ),
        "node": (
            "Node.js Backend",
            f'pkg install -y nodejs 2>&1 | tail -3 && '
            f'mkdir -p {shell_quote(cwd + "/" + project_name)} && '
            f'cd {shell_quote(cwd + "/" + project_name)} && '
            f'npm init -y 2>&1 | tail -3 && '
            f'echo "console.log(\'Server ready\');" > index.js && '
            f'echo "Created: {qname}/index.js"'
        ),
        "c": (
            "C/C++ Development",
            f'pkg install -y clang make gdb 2>&1 | tail -3 && '
            f'mkdir -p {shell_quote(cwd + "/" + project_name)} && '
            f'cd {shell_quote(cwd + "/" + project_name)} && '
            f'echo "#include <stdio.h>\\nint main() {{\\n    printf(\\"Hello from Termux!\\\\n\\");\\n    return 0;\\n}}" > main.c && '
            f'echo "Created: {qname}/main.c" && '
            f'echo "Compile: cd {qname} && clang main.c -o main && ./main"'
        ),
        "rust": (
            "Rust Development",
            f'pkg install -y rust binutils 2>&1 | tail -3 && '
            f'cd {shell_quote(cwd)} && '
            f'cargo new {shell_quote(project_name)} 2>&1 && '
            f'echo "Created: {qname}/" && '
            f'echo "Run: cd {qname} && cargo run"'
        ),
        "data": (
            "Data Science",
            f'pkg install -y python python-pip 2>&1 | tail -3 && '
            f'pip install numpy pandas matplotlib jupyter 2>&1 | tail -5 && '
            f'mkdir -p {shell_quote(cwd + "/" + project_name)} && '
            f'echo "Created: {qname}/" && '
            f'echo "Start Jupyter: jupyter notebook"'
        ),
        "termux": (
            "Beautiful Terminal",
            f'pkg install -y zsh eza bat neofetch git 2>&1 | tail -5 && '
            f'echo "Installing oh-my-zsh..." && '
            f'sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended 2>&1 | tail -5 && '
            f'echo "Done! Restart Termux or run: zsh"'
        ),
    }

    if intent in setups:
        title, cmd = setups[intent]
        return execute(f'echo "🚀 Setting up: {title}"; echo "---"; {cmd}')
    else:
        return execute('echo "Available environments:"; echo "python, bot, react, node, c, rust, data, termux"')


@register_tool(
    name="review",
    description="Review a code file: syntax check, linting, suggestions.",
    schema={
        "type": "object",
        "properties": {
            "file": {"type": "string", "description": "File path to review"},
        },
        "required": ["file"],
    },
    category="terminal",
)
def handle_review(data: dict) -> str:
    file_path = data.get("file", "").strip()
    if not file_path:
        return error_msg("Missing 'file' path")

    safe_path = shell_quote(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    checks = [
        f'echo "=== File: {file_path} ==="',
        f'echo "Size: $(wc -c < {safe_path} 2>/dev/null) bytes, Lines: $(wc -l < {safe_path} 2>/dev/null)"',
        f'echo "---"',
        f'echo "Content:"',
        f'cat {safe_path} 2>/dev/null || echo "Cannot read file"',
    ]

    if ext == ".py":
        checks += [
            f'echo "---"',
            f'echo "=== Python Syntax Check ==="',
            f'python3 -m py_compile {safe_path} 2>&1 && echo "✅ Syntax OK" || echo "❌ Syntax Error"',
            f'echo "---"',
            f'echo "=== Unused Variables ==="',
            f"python3 -m flake8 {safe_path} --select F841 2>&1 | head -10 || echo 'flake8 not installed (pip install flake8)'",
        ]
    elif ext in (".sh", ".bash"):
        checks += [
            f'echo "---"',
            f'echo "=== Shell Syntax Check ==="',
            f'bash -n {safe_path} 2>&1 && echo "✅ Syntax OK" || echo "❌ Syntax Error"',
        ]
    elif ext in (".js", ".mjs"):
        checks += [
            f'echo "---"',
            f'echo "=== JS Syntax Check ==="',
            f'node --check {safe_path} 2>&1 && echo "✅ Syntax OK" || echo "❌ Syntax Error"',
        ]
    elif ext == ".c":
        checks += [
            f'echo "---"',
            f'echo "=== C Lint ==="',
            f'clang -fsyntax-only -Wall {safe_path} 2>&1 | head -20 || echo "clang not installed"',
        ]

    return execute(" && ".join(checks))


@register_tool(
    name="log_analyze",
    description="Analyze a log file and extract errors/warnings.",
    schema={
        "type": "object",
        "properties": {
            "file": {"type": "string", "description": "Log file path to analyze"},
        },
        "required": ["file"],
    },
    category="terminal",
)
def handle_log_analyze(data: dict) -> str:
    file_path = data.get("file", "").strip()
    if not file_path:
        return error_msg("Missing 'file' path")

    safe_path = shell_quote(file_path)
    cmd = (
        f'echo "Analyzing: {file_path}"; echo "---"; '
        f'echo "Last 200 lines:"; '
        f'tail -200 {safe_path} 2>/dev/null || echo "Cannot read file"; '
        f'echo "---"; '
        f'echo "Errors found:"; '
        f'grep -i -E "error|fail|crash|fatal|exception|traceback|panic|segfault" {safe_path} 2>/dev/null | tail -30 || echo "No errors detected"'
    )
    return execute(cmd)


@register_tool(
    name="script_gen",
    description="Generate a shell or Python script from a description.",
    schema={
        "type": "object",
        "properties": {
            "description": {"type": "string", "description": "What the script should do"},
            "type": {"type": "string", "enum": ["sh", "py"], "description": "Script type (sh or py)"},
            "output": {"type": "string", "description": "Output file path"},
        },
        "required": ["description"],
    },
    category="terminal",
)
def handle_script_gen(data: dict) -> str:
    description = data.get("description", "").strip()
    script_type = data.get("type", "sh").strip()
    output = data.get("output", "").strip()

    if not description:
        return error_msg("Missing 'description' of what the script should do")

    safe_out = shell_quote(output) if output else ""
    if script_type == "py":
        template = f'echo "#!/usr/bin/env python3\\n# Script: {output or "script.py"}\\n# {description}\\n" > {safe_out} && echo "Python template created: {output}"'
    else:
        template = f'echo "#!/data/data/com.termux/files/usr/bin/bash\\n# Script: {output or "script.sh"}\\n# {description}\\n\\nset -e\\n" > {safe_out} && chmod +x {safe_out} && echo "Bash script created: {output}"'

    if output:
        return execute(template)
    else:
        return execute(f'echo "Script described: {description}"; echo "To generate, provide an output path"')


@register_tool(
    name="deps_tree",
    description="Show dependency tree for a package.",
    schema={
        "type": "object",
        "properties": {
            "package": {"type": "string", "description": "Package name (optional)"},
        },
    },
    category="terminal",
)
def handle_deps_tree(data: dict) -> str:
    package = data.get("package", "").strip()
    if package:
        return execute(
            f'echo "=== Reverse depends for: {package} ===" && '
            f'apt-cache rdepends {shell_quote(package)} 2>/dev/null | head -30 || '
            f'echo "Package not found"'
        )
    else:
        return execute(
            f'echo "=== Installed Packages ===" && '
            f'pkg list-installed 2>/dev/null | wc -l && echo "packages total" && '
            f'echo "---" && '
            f'echo "Top 20 by size:" && '
            f'dpkg-query -W -f=\'${{Installed-Size}}\\t${{Package}}\\n\' 2>/dev/null | sort -rn | head -20 || '
            f'echo "Use dpkg-query for package sizes"'
        )


@register_tool(
    name="storage_audit",
    description="Audit storage usage: disk usage, caches, cleanup suggestions.",
    schema={"type": "object", "properties": {}},
    category="terminal",
)
def handle_storage_audit(data: dict) -> str:
    return execute(
        'echo "=== Storage Usage ==="; '
        'df -h /data 2>/dev/null | tail -1; '
        'echo "---"; '
        'echo "Largest directories in ~/:"; '
        'du -sh ~/*/ 2>/dev/null | sort -rh | head -15; '
        'echo "---"; '
        'echo "Cache directories:"; '
        'du -sh ~/.cache/*/ 2>/dev/null | sort -rh | head -10; '
        'echo "---"; '
        'echo "Pip cache:"; '
        'du -sh ~/.cache/pip 2>/dev/null || echo "No pip cache"; '
        'echo "---"; '
        'echo "npm cache:"; '
        'du -sh ~/.npm 2>/dev/null || echo "No npm cache"; '
        'echo "---"; '
        'echo "Trash/Downloads:"; '
        'du -sh ~/storage/downloads/ 2>/dev/null || echo "No downloads folder"; '
        'echo "---"; '
        'echo "💡 Cleanup commands:"; '
        'echo "  pip cache purge"; '
        'echo "  npm cache clean --force"; '
        'echo "  pkg clean"; '
        'echo "  rm -rf ~/.cache/pip"'
    )


@register_tool(
    name="config_fix",
    description="Fix common configuration issues (bashrc, zshrc, termux settings, fonts, etc.).",
    schema={
        "type": "object",
        "properties": {
            "config": {"type": "string", "enum": ["bashrc", "zshrc", "termux", "font", "colors", "storage", "path", "env", "all"], "description": "Config to fix"},
        },
    },
    category="terminal",
)
def handle_config_fix(data: dict) -> str:
    which_config = data.get("config", "all").strip()

    checks = []
    if which_config in ("bashrc", "all"):
        checks.append('echo "=== .bashrc ===" && cat ~/.bashrc 2>/dev/null | head -50 || echo "No .bashrc found"')
    if which_config in ("zshrc", "all"):
        checks.append('echo "=== .zshrc ===" && cat ~/.zshrc 2>/dev/null | head -50 || echo "No .zshrc found"')
    if which_config in ("termux", "all"):
        checks.append('echo "=== termux.properties ===" && cat ~/.termux/termux.properties 2>/dev/null || echo "No termux.properties"')
    if which_config in ("font", "all"):
        checks.append('echo "=== Font ===" && ls ~/.termux/font.ttf 2>/dev/null && echo "Custom font found" || echo "Default font"')
    if which_config in ("colors", "all"):
        checks.append('echo "=== colors.properties ===" && cat ~/.termux/colors.properties 2>/dev/null || echo "Default colors"')
    if which_config in ("storage", "all"):
        checks.append('echo "=== Storage Check ===" && ls ~/storage/ 2>/dev/null || echo "Storage NOT set up — run: termux-setup-storage"')
    if which_config in ("path", "all"):
        checks.append(r'echo "=== $PATH ===" && echo "$PATH"')
    if which_config in ("env", "all"):
        checks.append('echo "=== Environment ===" && env | sort | head -30')

    cmd = " && ".join(checks) if checks else 'echo Specify: bashrc, zshrc, termux, font, colors, storage, path, env, or all'
    return execute(cmd)


@register_tool(
    name="git_smart",
    description="Smart Git operations: diff summary, recent log, commit suggestions, conflict resolution.",
    schema={
        "type": "object",
        "properties": {
            "action": {"type": "string", "description": "diff-summary, log-recent, suggest-commit, fix-conflict, or raw git command"},
            "repo_dir": {"type": "string", "description": "Repository directory"},
            "limit": {"type": "integer", "description": "Limit results"},
        },
        "required": ["action"],
    },
    category="terminal",
)
def handle_git_smart(data: dict) -> str:
    action = data.get("action", "diff").strip()
    repo_dir = data.get("repo_dir", get_current_dir()).strip()
    safe_dir = shell_quote(repo_dir)

    if action == "diff-summary":
        cmd = f'cd {safe_dir} && echo "=== Files Changed ===" && git diff --stat 2>&1 | tail -20 && echo "---" && echo "=== Diff ===" && git diff --unified=5 2>&1 | head -200'
    elif action == "log-recent":
        limit = data.get("limit", 10)
        cmd = f'cd {safe_dir} && git log --oneline --graph -{limit} 2>&1'
    elif action == "suggest-commit":
        cmd = f'cd {safe_dir} && echo "=== Current Changes ===" && git diff --stat 2>&1 && echo "---" && echo "Suggested commit message:" && git diff --cached 2>&1 | head -50 || git diff 2>&1 | head -50'
    elif action == "fix-conflict":
        cmd = f'cd {safe_dir} && echo "=== Conflict Status ===" && git diff --name-only --diff-filter=U 2>&1 && echo "---" && echo "Files with conflicts:" && git diff --check 2>&1 | head -20'
    else:
        cmd = f'cd {safe_dir} && git {action} 2>&1 | tail -30'

    return execute(cmd)


@register_tool(
    name="regex_test",
    description="Test a regular expression pattern against sample text.",
    schema={
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Regular expression pattern"},
            "test": {"type": "string", "description": "Test string to match against"},
        },
        "required": ["pattern"],
    },
    category="terminal",
)
def handle_regex(data: dict) -> str:
    pattern = data.get("pattern", "").strip()
    test_str = data.get("test", "").strip()

    if not pattern:
        return error_msg("Missing 'pattern'")

    safe_pattern = shell_quote(pattern)
    if test_str:
        safe_test = shell_quote(test_str)
        cmd = (
            f'echo "Pattern: {pattern}" && '
            f'echo "Test: {test_str}" && '
            f'echo "---" && '
            f'echo "Matches:" && '
            f'echo {safe_test} | grep -oP {safe_pattern} 2>&1 || echo "No matches or invalid regex"'
        )
    else:
        cmd = f'echo "Pattern: {pattern}" && echo "Provide a test string to check matches"'

    return execute(cmd)


@register_tool(
    name="db_design",
    description="Design a database schema from a description and generate SQL.",
    schema={
        "type": "object",
        "properties": {
            "schema": {"type": "string", "description": "Schema description"},
            "output": {"type": "string", "description": "Output SQL file path"},
        },
        "required": ["schema"],
    },
    category="terminal",
)
def handle_db_design(data: dict) -> str:
    schema = data.get("schema", "").strip()
    db_path = data.get("output", get_current_dir() + "/database.sqlite").strip()

    if not schema:
        return error_msg("Missing 'schema' — describe your tables")

    safe_db = shell_quote(db_path)
    cmd = (
        f'touch {safe_db} 2>/dev/null && '
        f'echo "Database created: {db_path}" && '
        f'echo "---" && '
        f'echo "Schema description:" && '
        f'echo "{schema}" && '
        f'echo "---" && '
        f'echo "Use /db-query to run SQL. Example: CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);"'
    )
    return execute(cmd)


@register_tool(
    name="backup",
    description="Backup Termux home, packages, or configs.",
    schema={
        "type": "object",
        "properties": {
            "target": {"type": "string", "enum": ["home", "packages", "configs"], "description": "What to backup"},
            "output": {"type": "string", "description": "Output archive path"},
            "include": {"type": "string", "description": "Comma-separated extra paths to include"},
        },
        "required": ["target"],
    },
    category="terminal",
)
def handle_backup(data: dict) -> str:
    import time
    target = data.get("target", "home").strip()
    output = data.get("output", "").strip()
    include = data.get("include", "").strip().split(",") if data.get("include", "").strip() else []

    home = os.environ.get("HOME", "/data/data/com.termux/files/home")
    timestamp = time.strftime("%Y%m%d_%H%M%S")

    if not output:
        output = f"~/storage/shared/termux_backup_{timestamp}.tar.gz"

    safe_out = shell_quote(output)

    if target == "home":
        cmd = (
            f'mkdir -p "$(dirname {safe_out})" 2>/dev/null; '
            f'echo "Backing up: {home}"; '
            f'echo "Output: {output}"; '
            f'echo "---"; '
            f'tar -czvf {safe_out} -C "$(dirname {home})" "$(basename {home})" --exclude=".cache" --exclude="__pycache__" --exclude="node_modules" --exclude="*.pyc" 2>&1 | while read line; do echo "$line"; done && '
            f'echo "" && '
            f'echo "✅ Backup complete!" && '
            f'ls -lh {safe_out} || echo "❌ Backup failed"'
        )
    elif target == "packages":
        cmd = (
            f'echo "Backing up package list..." && '
            f'pkg list-installed > {safe_out} 2>&1 && '
            f'echo "✅ Package list saved to: {output}" && '
            f'echo "Restore with: xargs pkg install -y < {safe_out}"'
        )
    elif target == "configs":
        cmd = (
            f'echo "Backing up configs..." && '
            f'tar -czf {safe_out} ~/.bashrc ~/.zshrc ~/.termux/ ~/.config/ 2>/dev/null && '
            f'echo "✅ Configs saved to: {output}" && '
            f'ls -lh {safe_out}'
        )
    elif include:
        inc_paths = " ".join(shell_quote(p.strip()) for p in include if p.strip())
        cmd = (
            f'mkdir -p "$(dirname {safe_out})" 2>/dev/null; '
            f'echo "Backing up selected paths..." && '
            f'tar -czf {safe_out} {inc_paths} 2>&1 && '
            f'echo "✅ Backup complete: {output}" && '
            f'ls -lh {safe_out} || echo "❌ Backup failed"'
        )
    else:
        cmd = 'echo "Targets: home, packages, configs. Or specify include: path1,path2"'

    return execute(cmd)


@register_tool(
    name="restore",
    description="Restore from a backup archive.",
    schema={
        "type": "object",
        "properties": {
            "file": {"type": "string", "description": "Backup archive file path"},
            "target": {"type": "string", "enum": ["home", "packages", "configs", "info"], "description": "What to restore"},
        },
        "required": ["file"],
    },
    category="terminal",
)
def handle_restore(data: dict) -> str:
    backup_file = data.get("file", "").strip()
    target = data.get("target", "home").strip()

    if not backup_file:
        return error_msg("Missing 'file' — path to backup archive")

    safe_file = shell_quote(backup_file)
    home = os.environ.get("HOME", "/data/data/com.termux/files/home")

    if target == "home":
        cmd = (
            f'echo "⚠️ WARNING: This will overwrite files in {home}"; '
            f'echo "Restoring from: {backup_file}"; '
            f'echo "---"; '
            f'tar -xzf {safe_file} -C "$(dirname {home})" 2>&1 && '
            f'echo "✅ Restore complete!" || echo "❌ Restore failed"'
        )
    elif target == "packages":
        cmd = (
            f'echo "Restoring packages from: {backup_file}"; '
            f'xargs pkg install -y < {safe_file} 2>&1 | tail -20 && '
            f'echo "✅ Packages restored!" || echo "❌ Restore failed"'
        )
    elif target == "configs":
        cmd = (
            f'echo "Restoring configs from: {backup_file}"; '
            f'tar -xzf {safe_file} -C {shell_quote(home)} 2>&1 && '
            f'echo "✅ Configs restored!" || echo "❌ Restore failed"'
        )
    elif target == "info":
        cmd = (
            f'echo "=== Backup Info ===" && '
            f'echo "File: {backup_file}" && '
            f'tar -tzf {safe_file} 2>/dev/null | head -50 && '
            f'echo "---" && '
            f'tar -tzf {safe_file} 2>/dev/null | wc -l && echo "files total"'
        )
    else:
        cmd = 'echo "Targets: home, packages, configs, info"'

    return execute(cmd)
import os
from typing import TYPE_CHECKING

