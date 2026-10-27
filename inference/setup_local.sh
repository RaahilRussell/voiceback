#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PYTHON="${PYTHON:-python3.11}"

"$PYTHON" -m venv "$ROOT/.venv-local"
"$ROOT/.venv-local/bin/python" -m pip install --upgrade pip
"$ROOT/.venv-local/bin/python" -m pip install \
  torch torchvision torchaudio lightning sentencepiece av \
  scikit-image gdown mediapipe==0.10.21 transformers>=4.45,<5

"$ROOT/.venv-local/bin/python" -m pip install -e "$ROOT/backend[dev]"

if [[ ! -d "$ROOT/.local/auto_avsr/.git" ]]; then
  mkdir -p "$ROOT/.local"
  git clone --depth 1 https://github.com/mpc001/auto_avsr.git "$ROOT/.local/auto_avsr"
fi

echo "Local runtime installed. Put the authorized Auto-AVSR checkpoint at:"
echo "  $ROOT/checkpoints/vsr_trlrs2lrs3vox2avsp_base.pth"
