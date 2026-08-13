#!/usr/bin/env bash
# Phase 1: capture byte-identical baseline of every source file.
# Usage: capture_source_sha256.sh <output-dir> <source-file> [<source-file> ...]
# Writes: <output-dir>/.source-sha256-pre-merge.txt

set -euo pipefail

if [ "$#" -lt 2 ]; then
  echo "Usage: $0 <output-dir> <source-file> [<source-file> ...]" >&2
  exit 2
fi

OUTPUT_DIR="$1"
shift

if [ ! -d "$OUTPUT_DIR" ]; then
  echo "Output directory does not exist: $OUTPUT_DIR" >&2
  exit 1
fi

if command -v shasum >/dev/null 2>&1; then
  HASHER="shasum -a 256"
elif command -v sha256sum >/dev/null 2>&1; then
  HASHER="sha256sum"
else
  echo "Neither shasum nor sha256sum is available." >&2
  exit 1
fi

OUT_FILE="$OUTPUT_DIR/.source-sha256-pre-merge.txt"
$HASHER "$@" | sort > "$OUT_FILE"

count=$(wc -l < "$OUT_FILE" | tr -d ' ')
echo "Wrote $count SHA-256 entries to $OUT_FILE"
