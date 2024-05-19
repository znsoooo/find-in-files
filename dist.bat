@echo off

set name=FindInFiles
set build=py -m PyInstaller -yws --noupx

%build% %name%.py
echo.

dist\%name%\%name%.exe
pause
