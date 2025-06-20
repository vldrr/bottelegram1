@echo off
title VideoBot - Interface Web

echo ========================================
echo    Iniciando Interface Web do VideoBot
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

echo [OK] Configurações verificadas
echo.
echo Iniciando interface web...
echo Acesse: http://localhost:5000
echo Painel Admin: http://localhost:5000/admin
echo.
echo Pressione Ctrl+C para parar
echo.

python app.py

echo.
echo Interface web finalizada
pause

