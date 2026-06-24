#!/data/data/com.termux/files/usr/bin/bash
# ──────────────────────────────────────────────────────────
# Termux-MCP Quick Start Script
# Usage: ./start-mcp.sh  (first time)
#        mcp             (after setup, from any session)
# ──────────────────────────────────────────────────────────

TERMUX_MCP_DIR="$HOME/termux-mcp"
ALIAS_NAME="mcp"
BRANCH="main"

# ── Color helpers ──
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
err()   { echo -e "${RED}[✗]${NC} $1"; }

# ── Check Python ──
if ! command -v python &>/dev/null; then
    warn "Python not found, installing..."
    pkg install python -y
fi

# ── Clone or update ──
if [ ! -d "$TERMUX_MCP_DIR/.git" ]; then
    info "Cloning termux-mcp..."
    cd "$HOME"
    git clone -b "$BRANCH" https://github.com/TruthZY/termux-mcp.git "$TERMUX_MCP_DIR"
else
    info "Updating termux-mcp..."
    cd "$TERMUX_MCP_DIR"
    git fetch origin "$BRANCH" --quiet
    git reset --hard "origin/$BRANCH" --quiet
fi

cd "$TERMUX_MCP_DIR" || { err "Cannot cd to $TERMUX_MCP_DIR"; exit 1; }

# ── Restore execute permission (git may strip it) ──
chmod +x "$TERMUX_MCP_DIR/start-mcp.sh"

# ── Set up alias (first time only) ──
ALIAS_LINE="alias $ALIAS_NAME=\"$TERMUX_MCP_DIR/start-mcp.sh\""
BASHRC="$HOME/.bashrc"

if ! grep -qF "alias $ALIAS_NAME=" "$BASHRC" 2>/dev/null; then
    echo "" >> "$BASHRC"
    echo "# Termux-MCP quick start" >> "$BASHRC"
    echo "$ALIAS_LINE" >> "$BASHRC"
    info "Added '$ALIAS_NAME' alias to ~/.bashrc"
    info "From next session, just type: mcp"
fi

# Also set up for zsh if it exists
ZSHRC="$HOME/.zshrc"
if [ -f "$ZSHRC" ] && ! grep -qF "alias $ALIAS_NAME=" "$ZSHRC" 2>/dev/null; then
    echo "" >> "$ZSHRC"
    echo "$ALIAS_LINE" >> "$ZSHRC"
fi

# ── Launch ──
info "Starting MCP server..."
echo ""
python -m termux_mcp "$@"
