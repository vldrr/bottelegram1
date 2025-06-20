@echo off
title VideoBot - Atualizar Dependências

echo ========================================
echo    Atualizando Dependências do VideoBot
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

REM Atualizar pip
echo Atualizando pip...
python -m pip install --upgrade pip

REM Atualizar dependências
echo.
echo Atualizando dependências...
pip install --upgrade -r requirements.txt

REM Verificar dependências
echo.
echo Verificando dependências...
pip check

echo.
echo ========================================
echo    Dependências atualizadas!
echo ========================================
echo.
pause

