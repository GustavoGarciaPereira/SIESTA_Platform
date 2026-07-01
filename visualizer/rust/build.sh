#!/bin/bash
# Build script for siesta-field-wasm
# Requires: wasm-pack (https://rustwasm.github.io/wasm-pack/installer/)
#
# Usage: ./build.sh
# Output: pkg/ directory with .js + .wasm artifacts

set -e

cd "$(dirname "$0")"

echo "==> Building siesta-field-wasm with wasm-pack..."
wasm-pack build --target web --out-dir pkg --release

echo "==> Copying artifacts to static directory..."
mkdir -p ../static/visualizer/wasm
cp pkg/*.js pkg/*.wasm ../static/visualizer/wasm/ 2>/dev/null || true

echo "==> Done! WASM artifacts in visualizer/static/visualizer/wasm/"
ls -la ../static/visualizer/wasm/
