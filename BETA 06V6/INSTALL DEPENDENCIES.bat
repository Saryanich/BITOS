@echo off
setlocal
cd /d "%~dp0"

chcp 65001 >nul

echo ==========================================
echo      Установка библиотек BITOS
echo ==========================================
echo.
echo Устанавливаются библиотеки:
echo   Pillow      - изображения и графика
echo   psutil     - диспетчер задач и ресурсы
echo   screeninfo  - обнаружение дополнительных экранов
echo   pygame     - встроенное воспроизведение аудио
echo   python-vlc - интеграция медиаплеера с VLC
echo.

where py.exe >nul 2>nul
if not errorlevel 1 (
    set "PYTHON_CMD=py -3"
) else (
    where python.exe >nul 2>nul
    if errorlevel 1 (
        echo ОШИБКА: Python не найден. Установите Python 3 и повторите запуск.
        pause
        exit /b 1
    )
    set "PYTHON_CMD=python"
)

%PYTHON_CMD% -m pip install --upgrade pip
if errorlevel 1 goto install_error

%PYTHON_CMD% -m pip install Pillow psutil screeninfo pygame python-vlc
if errorlevel 1 goto install_error

echo.
echo ==========================================
echo Библиотеки Python успешно установлены.
echo ==========================================
echo.
echo ВАЖНО: для встроенного воспроизведения видео и некоторых форматов
echo еще требуется установленный VLC Media Player (настольная программа).
echo Скачать VLC: https://www.videolan.org/vlc/
echo.
echo Запустите START BITOS.bat
pause
exit /b 0

:install_error
echo.
echo ОШИБКА: Не удалось установить одну или несколько библиотек.
echo Проверьте подключение к интернету и наличие Python 3.
pause
exit /b 1
