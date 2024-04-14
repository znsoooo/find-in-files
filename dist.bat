@echo off

set name=FindInFiles
set build=py -m PyInstaller -yws --noupx
set quiet=1^>nul 2^>nul

%build% %name%.py
echo.

echo Remove unused files...
del dist\%name%\*.manifest %quiet%
del dist\%name%\*.pyd %quiet%
del dist\%name%\api*.dll %quiet%
del dist\%name%\_internal\*.pyd %quiet%
del dist\%name%\_internal\api*.dll %quiet%
move dist\%name%\wx*.dll dist\%name%\wx %quiet%
echo.

dist\%name%\%name%.exe
pause
