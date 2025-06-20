@echo off
title VideoBot - Backup Manual

echo ========================================
echo    Backup Manual do VideoBot
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

REM Criar diretório de backup se não existir
if not exist "backups" mkdir backups

REM Gerar timestamp
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "timestamp=%YYYY%%MM%%DD%_%HH%%Min%%Sec%"

echo Criando backup em: backups\backup_%timestamp%
echo.

REM Backup do banco de dados
echo Fazendo backup do banco de dados...
copy bot_database.db backups\database_backup_%timestamp%.db

REM Backup dos vídeos (se existirem)
if exist "videos\*.*" (
    echo Fazendo backup dos vídeos...
    powershell Compress-Archive -Path "videos\*" -DestinationPath "backups\videos_backup_%timestamp%.zip" -Force
)

REM Backup das configurações
echo Fazendo backup das configurações...
copy .env backups\config_backup_%timestamp%.env 2>nul

echo.
echo ========================================
echo    Backup concluído com sucesso!
echo ========================================
echo.
echo Arquivos criados:
echo - backups\database_backup_%timestamp%.db
if exist "videos\*.*" echo - backups\videos_backup_%timestamp%.zip
echo - backups\config_backup_%timestamp%.env
echo.
pause

