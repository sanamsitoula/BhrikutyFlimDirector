#!/bin/bash
set -e

echo "=========================================="
echo "  BHRIKUTY PIPELINE DEBUG SUITE"
echo "=========================================="

echo "[1/3] System, Python deps, FFmpeg, Remotion, project structure..."
python3 tools/debug_pipeline.py || true

echo ""
echo "[2/3] FFmpeg deep operations..."
python3 tools/debug_ffmpeg.py || true

echo ""
echo "[3/3] Remotion render test..."
cd remotion
node scripts/debug_render.js || true
cd ..

echo ""
echo "=========================================="
echo "  DEBUG COMPLETE"
echo "=========================================="
echo "Reports:"
echo "  debug_report.md"
echo "  _debug_test/remotion_output/remotion_report.json"
echo "  _debug_test/remotion_output/remotion_debug.log"
