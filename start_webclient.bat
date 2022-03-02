if not DEFINED IS_MINIMIZED set IS_MINIMIZED=1 && start "" /min "%~dpnx0" %* && exit

@echo off
cd /D "%~dp0"
python "C:\Users\Tanja\Desktop\Trilution Webclient Integration (V1.1)\main.py" %*
pause

exit