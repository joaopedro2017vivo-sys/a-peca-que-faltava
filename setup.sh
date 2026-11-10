#!/usr/bin/env bash
# Baixa o Piper e as vozes em português (uma vez por máquina).
set -e
D="${CANAL_VOICES:-$HOME/.cache/canal}"
mkdir -p "$D"; cd "$D"
if [ ! -x piper/piper ]; then
  curl -sSL -o piper.tgz https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_linux_x86_64.tar.gz
  tar xzf piper.tgz && rm piper.tgz && chmod +x piper/piper piper/espeak-ng || true
fi
for v in cadu-medium faber-medium jeff-medium dii-high; do
  if [ ! -f "vits-piper-pt_BR-$v/pt_BR-$v.onnx" ]; then
    curl -sSL -o v.tar.bz2 "https://github.com/k2-fsa/sherpa-onnx/releases/download/tts-models/vits-piper-pt_BR-$v.tar.bz2"
    tar xjf v.tar.bz2 && rm v.tar.bz2
  fi
done
echo "vozes prontas em $D"
