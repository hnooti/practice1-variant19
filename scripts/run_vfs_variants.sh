#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for archive in minimal_vfs sample_vfs alt_vfs; do
  printf 'ls /\ncd /\nexit\n' | bash run.sh --vfs "vfs/$archive.zip"
done
