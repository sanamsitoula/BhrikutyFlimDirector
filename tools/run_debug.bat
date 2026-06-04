@echo off
setlocal
echo ==========================================
echo   BHRIKUTY PIPELINE DEBUG SUITE
echo ==========================================
echo.

echo [1/3] System, Python deps, FFmpeg, Remotion, project structure...
python tools\debug_pipeline.py
if %errorlevel% neq 0 (
    echo.
    echo PIPELINE CHECKS FOUND ERRORS - review output above
    echo.
)

echo.
echo [2/3] FFmpeg deep operations (encode, cut, concat, scale, subtitles, audio)...
python tools\debug_ffmpeg.py
if %errorlevel% neq 0 (
    echo.
    echo FFMPEG CHECKS FOUND ERRORS - review output above
    echo.
)

echo.
echo [3/3] Remotion render test (bundle, still, video)...
cd remotion
node scripts\debug_render.js
cd ..

echo.
echo ==========================================
echo   DEBUG COMPLETE
echo ==========================================
echo Reports generated:
echo   debug_report.md
echo   _debug_test\remotion_output\remotion_report.json
echo   _debug_test\remotion_output\remotion_debug.log
echo.
pause
