@echo off
REM ==========================================================================
REM  Build raycaster.exe on Windows.
REM  Needs NASM (https://nasm.us) and a linker.  Two options below.
REM ==========================================================================

nasm -f win64 raycaster.asm -o raycaster.obj
if errorlevel 1 goto :err

REM --- Option A: GoLink (tiny, free: https://godevtool.com) --------------------
where golink >nul 2>nul
if %errorlevel%==0 (
    golink /entry start /console raycaster.obj kernel32.dll user32.dll gdi32.dll
    REM NOTE: swap /console for a GUI subsystem if you don't want a console window.
    goto :done
)

REM --- Option B: MSVC link.exe (from a "x64 Native Tools" prompt) -------------
where link >nul 2>nul
if %errorlevel%==0 (
    link /subsystem:windows /entry:start /nodefaultlib ^
        raycaster.obj kernel32.lib user32.lib gdi32.lib
    goto :done
)

echo Could not find golink or link.exe on PATH.
echo Install GoLink, or run this from a Visual Studio "x64 Native Tools" prompt.
goto :err

:done
echo Built raycaster.exe
goto :eof
:err
echo Build failed.
exit /b 1
