#!/data/data/com.termux/files/usr/bin/bash
set -e
PREFIX="${PREFIX:-/data/data/com.termux/files/usr}"
BIN="$PREFIX/bin"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python is required. Install it with: pkg install python"
  exit 1
fi

mkdir -p "$BIN"
cp "$SCRIPT_DIR/aayush_repl.py" "$BIN/aayush_repl.py"
cp "$SCRIPT_DIR/aayush-repl" "$BIN/aayush-repl"
chmod +x "$BIN/aayush-repl" "$BIN/aayush_repl.py"

echo
printf '\033[1;32mAayush REPL v3 installed!\033[0m\n'
echo 'Run: aayush-repl'
