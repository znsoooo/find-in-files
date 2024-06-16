@echo off

set name=FindInFiles
set build=py -m PyInstaller -yws --noupx --icon icon.ico --add-data=icon.ico;.

%build% %name%.py
echo.

dist\%name%\%name%.exe
pause
