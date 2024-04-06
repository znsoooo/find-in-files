@echo off

set name=FindText
set root=dist\%name%
set libs=%root%\wx

pyinstaller -ywsF --noupx %name%.py
echo.

pyinstaller -yws --noupx %name%.py
echo.

move %root%\*.pyd %libs%
move %root%\*.dll %libs%
move %libs%\python*.dll %root%
echo.

%root%\%name%.exe
pause
