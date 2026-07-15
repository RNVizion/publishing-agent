#!/usr/bin/env bash
set -euo pipefail

pip install --upgrade pip
pip install -r /workspaces/publishing-agent/requirements.txt

clone_or_update () {
  local slug="$1"
  local dir="/workspaces/${slug##*/}"
  if [ -d "$dir/.git" ]; then
    git -C "$dir" fetch --all --prune
    git -C "$dir" checkout main
    git -C "$dir" pull --ff-only origin main
  else
    git clone "https://github.com/${slug}.git" "$dir"
  fi
}

clone_or_update "RNVizion/rnvizion.github.io"
clone_or_update "RNVizion/ask-the-corpus"

echo "post-create: site and corpus repos ready under /workspaces"
