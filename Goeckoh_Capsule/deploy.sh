#!/bin/bash
set -euo pipefail

echo "=== Goeckoh Self-Contained Deployment ==="

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT"

mkdir -p models

fetch_models() {
  echo ">> Fetching Neuro-Assets..."

  if [ ! -f models/encoder.onnx ]; then
    echo "-> Downloading streaming Zipformer (ASR)..."
    wget -q -O /tmp/sherpa_asr.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/asr-models/sherpa-onnx-streaming-zipformer-en-2023-06-26.tar.bz2
    tar -xvf /tmp/sherpa_asr.tar.bz2 -C models/ --strip-components=1 --exclude=test_wavs
    for src in models/encoder-epoch-99-avg-1-chunk-16-left-128.onnx models/encoder-epoch-99-avg-1*.onnx; do
      [ -e "$src" ] || continue
      mv "$src" models/encoder.onnx
      break
    done
    for src in models/decoder-epoch-99-avg-1-chunk-16-left-128.onnx models/decoder-epoch-99-avg-1*.onnx; do
      [ -e "$src" ] || continue
      mv "$src" models/decoder.onnx
      break
    done
    for src in models/joiner-epoch-99-avg-1-chunk-16-left-128.onnx models/joiner-epoch-99-avg-1*.onnx; do
      [ -e "$src" ] || continue
      mv "$src" models/joiner.onnx
      break
    done
    rm -f /tmp/sherpa_asr.tar.bz2
  else
    echo "-> ASR model already present."
  fi

  if [ ! -f models/tts_model.onnx ]; then
    echo "-> Downloading VITS Piper (TTS)..."
    wget -q -O /tmp/sherpa_tts.tar.bz2 https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-en_US-lessac-medium.tar.bz2
    tar -xvf /tmp/sherpa_tts.tar.bz2 -C models/ --strip-components=1 --exclude=es_MX
    mv models/en_US-lessac-medium.onnx models/tts_model.onnx || true
    rm -f /tmp/sherpa_tts.tar.bz2
  else
    echo "-> TTS model already present."
  fi

  echo ">> Assets secured."
}

ensure_cython() {
  if python3 - <<'PY' >/dev/null 2>&1
import importlib.util
import sys

sys.exit(0 if importlib.util.find_spec("Cython") else 1)
PY
  then
    echo "-> Cython already present."
  else
    echo "-> Installing Cython (required by Buildozer)..."
    python3 -m pip install --upgrade cython
  fi
}

build_android() {
  echo ">> Buildozer found. Starting Android compile..."
  ensure_cython
  buildozer android debug
  echo "=== DONE: Check 'bin/' for your APK ==="
}

run_desktop() {
  echo ">> Running Desktop mode..."
  python3 -m pip install --upgrade pip
  python3 -m pip install numpy sounddevice sherpa-onnx plyer kivy
  python3 main.py
}

fetch_models

if command -v buildozer >/dev/null 2>&1; then
  build_android
else
  echo "!! Buildozer not found. Install with 'pip install buildozer cython' then rerun for APK."
  run_desktop
fi
