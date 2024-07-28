@echo off

set name=FindInFiles

pyinstaller -yws --noupx %name%.py --icon icon.ico --add-data=icon.ico;.
echo.

dist\%name%\%name%.exe
pause
