#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "Usage: $0 input.glb output.glb" >&2
  exit 1
fi

npx --yes @gltf-transform/cli optimize "$1" "$2" --compress draco --texture-compress webp
echo "Wrote optimized GLB to $2"
