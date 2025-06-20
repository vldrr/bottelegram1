@echo off
title VideoBot - Telegram Bot

echo ========================================
echo    Iniciando VideoBot (Modo Polling)
echo ========================================
echo.

REM Verificar se ambiente virtual existe
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual não encontrado!
    echo Execute install.bat primeiro
    pause
    exit /b 1
)

REM Ativar ambiente virtual
call venv\Scripts\activate.bat

REM Verificar se arquivo .env existe
if not exist ".env" (
    echo [ERRO] Arquivo .env não encontrado!
    echo Configure suas variáveis de ambiente primeiro
    pause
    exit /b 1
)

REM Verificar se token está configurado
findstr /C:"BOT_TOKEN=" .env | findstr /V /C:"BOT_TOKEN=seu_token_aqui" >nul
if %errorlevel% neq 0 (
    echo [ERRO] Token do bot não configurado!
    echo Edite o arquivo .env e configure BOT_TOKEN
    pause
    exit /b 1
)

echo [OK] Configurações verificadas
echo.
echo Iniciando bot em modo polling...
echo Pressione Ctrl+C para parar
echo.

python run_bot.py

echo.
echo Bot finalizado
pause

