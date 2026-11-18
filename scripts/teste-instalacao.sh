#!/bin/bash
# Renderiza um vídeo de teste de 5 segundos para confirmar que o HyperFrames + navegador + FFmpeg funcionam.
set -e
cd "$(dirname "$0")/.."
if [ -z "${HYPERFRAMES_BROWSER_PATH:-}" ]; then
  for c in /opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell /opt/pw-browsers/chromium-*/chrome-linux/chrome; do
    [ -x "$c" ] && { export HYPERFRAMES_BROWSER_PATH="$c"; break; }
  done
fi
T=video-projects/teste-instalacao
mkdir -p "$T" meus-videos
cp teste-instalacao/index.html "$T/"
cp node_modules/gsap/dist/gsap.min.js "$T/"
npx hyperframes render "$T" -o meus-videos/teste-instalacao.mp4 --quiet
[ -f meus-videos/teste-instalacao.mp4 ] && echo "  ok: vídeo de teste em meus-videos/teste-instalacao.mp4 ($(ffprobe -v error -show_entries format=duration -of csv=p=0 meus-videos/teste-instalacao.mp4)s)"
