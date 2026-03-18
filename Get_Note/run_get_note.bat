
@echo off

:: UTF-8 fix
chcp 65001 > nul

set LOG_FILE=D:\Code\Cheese\Get_Note\run_log.txt

echo ------------------------------------------------ >> %LOG_FILE%
echo [start] %date% %time% >> %LOG_FILE%

python D:\Code\Cheese\Get_Note\get_note.py >> %LOG_FILE% 2>&1

echo. >> %LOG_FILE%
echo [done] %date% %time% >> %LOG_FILE%
echo ------------------------------------------------ >> %LOG_FILE%
echo. >> %LOG_FILE%

:: query task in cmd:
:: schtasks /query /tn "Cheese_Get_Note"
:: schtasks /query /tn "Cheese_Get_Note" /v /fo list
