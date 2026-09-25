#!/bin/sh
set -eu
ROOT=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
BIN_DIR=${1:-"$HOME/.local/bin"}
mkdir -p "$BIN_DIR"
ln -sf "$ROOT/iccplus-local" "$BIN_DIR/iccplus-local"
ln -sf "$ROOT/cyoa-compress" "$BIN_DIR/cyoa-compress"
printf 'Installed %s and %s\n' "$BIN_DIR/iccplus-local" "$BIN_DIR/cyoa-compress"
