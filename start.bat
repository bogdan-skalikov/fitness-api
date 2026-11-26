@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo Окружение .venv не найдено, создаю...
    python -m venv .venv
    if errorlevel 1 goto :error
    .venv\Scripts\python.exe -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

echo.
echo Сервер запускается: http://127.0.0.1:8000/docs
echo Чтобы остановить - закройте это окно или нажмите Ctrl+C.
echo.

start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:8000/docs"

.venv\Scripts\python.exe -m uvicorn app.main:app --reload
goto :eof

:error
echo.
echo Не удалось подготовить окружение. Проверьте, что установлен Python 3.12
echo и есть доступ в интернет.
pause
