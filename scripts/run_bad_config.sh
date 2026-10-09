#!/usr/bin/env bash
set +e
cd "$(dirname "$0")/.."
bash run.sh --config config/broken.json
echo "exit code: $?"
