@echo off
title VideoBot - Agendador de Tarefas

echo ========================================
echo    Iniciando Agendador do VideoBot
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

echo [OK] Ambiente virtual ativado
echo.
echo Iniciando agendador de tarefas...
echo - Limpeza automática de downloads expirados
echo - Backup automático do banco de dados
echo - Relatórios periódicos
echo.
echo Pressione Ctrl+C para parar
echo.

python scheduler.py

echo.
echo Agendador finalizado
pause

