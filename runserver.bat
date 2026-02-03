@echo off
cd /d %~dp0

REM activar entorno virtual
call venv\Scripts\activate

REM abrir navegador en localhost
start http://127.0.0.1:8000/

REM ejecutar servidor Django en localhost
python manage.py runserver 127.0.0.1:8000

pause
