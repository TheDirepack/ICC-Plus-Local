#!/bin/sh
set -eu
SCRIPT=$0
while [ -h "$SCRIPT" ]; do
  LINK=$(readlink "$SCRIPT")
  case "$LINK" in
    /*) SCRIPT=$LINK ;;
    *) SCRIPT=$(dirname -- "$SCRIPT")/$LINK ;;
  esac
done
ROOT=$(CDPATH= cd -- "$(dirname -- "$SCRIPT")" && pwd)
BIN_DIR=${1:-"$HOME/.local/bin"}
mkdir -p "$BIN_DIR"
chmod +x "$ROOT/iccplus-local" "$ROOT/cyoa-compress"
ln -sf "$ROOT/iccplus-local" "$BIN_DIR/iccplus-local"
ln -sf "$ROOT/cyoa-compress" "$BIN_DIR/cyoa-compress"
printf 'Installed %s and %s\n' "$BIN_DIR/iccplus-local" "$BIN_DIR/cyoa-compress"
case ":$PATH:" in
  *":$BIN_DIR:"*) ;;
  *) printf 'Note: %s is not on PATH. Add it, or call the full path.\n' "$BIN_DIR" ;;
esac
