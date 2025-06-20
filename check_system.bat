@echo off
title VideoBot - Verificação do Sistema

echo ========================================
echo    Verificação do Sistema VideoBot
echo ========================================
echo.

REM Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado
    goto :error
) else (
    echo [OK] Python encontrado
    python --version
)

REM Verificar pip
echo.
echo Verificando pip...
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] pip não encontrado
    goto :error
) else (
    echo [OK] pip encontrado
    pip --version
)

REM Verificar ambiente virtual
echo.
echo Verificando ambiente virtual...
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual não encontrado
    echo Execute install.bat primeiro
    goto :error
) else (
    echo [OK] Ambiente virtual encontrado
)

REM Ativar ambiente virtual
call venv\Scripts\activate.bat

REM Verificar dependências
echo.
echo Verificando dependências...
pip check >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Algumas dependências podem ter conflitos
    pip check
) else (
    echo [OK] Dependências verificadas
)

REM Verificar arquivo .env
echo.
echo Verificando configurações...
if not exist ".env" (
    echo [ERRO] Arquivo .env não encontrado
    echo Configure suas variáveis de ambiente
    goto :error
) else (
    echo [OK] Arquivo .env encontrado
)

REM Verificar token do bot
findstr /C:"BOT_TOKEN=" .env | findstr /V /C:"BOT_TOKEN=seu_token_aqui" >nul
if %errorlevel% neq 0 (
    echo [AVISO] Token do bot não configurado
    echo Configure BOT_TOKEN no arquivo .env
) else (
    echo [OK] Token do bot configurado
)

REM Verificar diretórios
echo.
echo Verificando diretórios...
if not exist "videos" (
    echo [AVISO] Diretório videos não encontrado
    mkdir videos
    echo [OK] Diretório videos criado
) else (
    echo [OK] Diretório videos encontrado
)

if not exist "uploads" (
    echo [AVISO] Diretório uploads não encontrado
    mkdir uploads
    echo [OK] Diretório uploads criado
) else (
    echo [OK] Diretório uploads encontrado
)

REM Testar banco de dados
echo.
echo Testando banco de dados...
python -c "from database import DatabaseManager; db = DatabaseManager(); print('[OK] Banco de dados funcionando')" 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Problema com banco de dados
    goto :error
)

REM Testar importações principais
echo.
echo Testando módulos principais...
python -c "from bot import create_bot; from payment_processor import PaymentProcessor; from delivery_system import SecureDeliverySystem; print('[OK] Módulos principais funcionando')" 2>nul
if %errorlevel% neq 0 (
    echo [ERRO] Problema com módulos principais
    goto :error
)

echo.
echo ========================================
echo    Sistema verificado com sucesso!
echo ========================================
echo.
echo Tudo está funcionando corretamente.
echo Você pode iniciar o bot com start_bot.bat
echo.
goto :end

:error
echo.
echo ========================================
echo    Problemas encontrados!
echo ========================================
echo.
echo Verifique os erros acima e execute install.bat
echo se necessário.
echo.

:end
pause

