@echo off
echo ========================================
echo    VideoBot - Instalador para Windows
echo ========================================
echo.

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python não encontrado!
    echo Por favor, instale o Python 3.9+ do site oficial: https://python.org
    echo Certifique-se de marcar "Add Python to PATH" durante a instalação
    pause
    exit /b 1
)

echo [OK] Python encontrado
python --version

REM Verificar se pip está disponível
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] pip não encontrado!
    echo Reinstale o Python com pip incluído
    pause
    exit /b 1
)

echo [OK] pip encontrado
pip --version

REM Criar ambiente virtual
echo.
echo Criando ambiente virtual...
python -m venv venv
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao criar ambiente virtual
    pause
    exit /b 1
)

echo [OK] Ambiente virtual criado

REM Ativar ambiente virtual
echo.
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao ativar ambiente virtual
    pause
    exit /b 1
)

echo [OK] Ambiente virtual ativado

REM Atualizar pip
echo.
echo Atualizando pip...
python -m pip install --upgrade pip

REM Instalar dependências
echo.
echo Instalando dependências...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ERRO] Falha ao instalar dependências
    pause
    exit /b 1
)

echo [OK] Dependências instaladas

REM Criar diretórios necessários
echo.
echo Criando diretórios...
if not exist "videos" mkdir videos
if not exist "uploads" mkdir uploads
if not exist "static" mkdir static
if not exist "templates" mkdir templates
if not exist "backups" mkdir backups
if not exist "logs" mkdir logs

echo [OK] Diretórios criados

REM Verificar se arquivo .env existe
if not exist ".env" (
    echo.
    echo Copiando arquivo de configuração...
    copy .env.example .env
    echo [AVISO] Configure o arquivo .env com suas informações antes de executar o bot
)

REM Testar importações
echo.
echo Testando instalação...
python -c "from database import DatabaseManager; db = DatabaseManager(); print('[OK] Banco de dados inicializado')"
if %errorlevel% neq 0 (
    echo [ERRO] Falha no teste de instalação
    pause
    exit /b 1
)

echo.
echo ========================================
echo    Instalação concluída com sucesso!
echo ========================================
echo.
echo Próximos passos:
echo 1. Configure o arquivo .env com seu token do bot
echo 2. Execute: start_bot.bat para iniciar o bot
echo 3. Execute: start_web.bat para iniciar a interface web
echo.
echo Para mais informações, consulte o manual_windows.pdf
echo.
pause

