#!/usr/bin/env bash
set -e
cd "$(dirname "$0")/.."
bash run.sh --script tests/stage1_repl.txt
