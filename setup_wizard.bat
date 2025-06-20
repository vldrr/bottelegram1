@echo off
title VideoBot - Configuração Inicial

echo ========================================
echo    VideoBot - Configuração Inicial
echo ========================================
echo.

REM Verificar se está executando como administrador
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Executando sem privilégios de administrador
    echo Algumas funcionalidades podem não estar disponíveis
    echo.
)

echo Este assistente irá ajudá-lo a configurar o VideoBot
echo.

REM Verificar se arquivo .env já existe
if exist ".env" (
    echo [INFO] Arquivo .env já existe
    set /p overwrite="Deseja reconfigurar? (s/N): "
    if /i not "%overwrite%"=="s" goto :skip_config
)

echo.
echo === Configuração do Bot do Telegram ===
echo.
echo 1. Acesse @BotFather no Telegram
echo 2. Envie /newbot e siga as instruções
echo 3. Copie o token fornecido
echo.
set /p bot_token="Cole o token do bot aqui: "

if "%bot_token%"=="" (
    echo [ERRO] Token não pode estar vazio!
    pause
    exit /b 1
)

echo.
echo === Configuração de Segurança ===
echo.
echo Gerando chave secreta...
python -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(32))" > temp_secret.txt
set /p secret_key=<temp_secret.txt
del temp_secret.txt

echo.
echo === Configurações de Download ===
echo.
set /p expiry_hours="Tempo de expiração dos links (horas) [24]: "
if "%expiry_hours%"=="" set expiry_hours=24

set /p max_downloads="Máximo de downloads por compra [3]: "
if "%max_downloads%"=="" set max_downloads=3

echo.
echo === Configurações Avançadas ===
echo.
set /p webhook_url="URL do webhook (deixe vazio para modo polling): "

echo.
echo Criando arquivo de configuração...

REM Criar arquivo .env
(
echo # Configurações do VideoBot para Windows
echo BOT_TOKEN=%bot_token%
echo.
echo # URL do Webhook ^(deixe vazio para modo polling^)
echo WEBHOOK_URL=%webhook_url%
echo.
echo # Configurações do Banco de Dados
echo DATABASE_URL=sqlite:///bot_database.db
echo.
echo # Chave secreta para segurança
echo %secret_key%
echo.
echo # Configurações de Download
echo DOWNLOAD_EXPIRY_HOURS=%expiry_hours%
echo MAX_DOWNLOADS_PER_PURCHASE=%max_downloads%
echo.
echo # Configurações de Armazenamento
echo STORAGE_PATH=videos
echo UPLOAD_PATH=uploads
echo.
echo # Configurações de Logs
echo LOG_LEVEL=INFO
echo LOG_FILE=logs/bot.log
echo.
echo # Configurações do Flask
echo FLASK_ENV=production
echo FLASK_DEBUG=False
echo FLASK_HOST=0.0.0.0
echo FLASK_PORT=5000
echo.
echo # Configurações de Backup
echo BACKUP_PATH=backups
echo BACKUP_RETENTION_DAYS=30
echo.
echo # Configurações de Segurança
echo ALLOWED_EXTENSIONS=mp4,avi,mov,mkv,wmv
echo MAX_FILE_SIZE=104857600
echo.
echo # Configurações do Agendador
echo SCHEDULER_ENABLED=True
echo CLEANUP_INTERVAL_HOURS=1
echo BACKUP_INTERVAL_HOURS=24
) > .env

:skip_config

echo.
echo === Inicialização do Banco de Dados ===
echo.

REM Ativar ambiente virtual
if not exist "venv\Scripts\activate.bat" (
    echo [ERRO] Ambiente virtual não encontrado!
    echo Execute install.bat primeiro
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

echo Inicializando banco de dados...
python -c "from database import DatabaseManager; db = DatabaseManager(); print('[OK] Banco inicializado')"

if %errorlevel% neq 0 (
    echo [ERRO] Falha na inicialização do banco
    pause
    exit /b 1
)

echo.
echo === Teste de Conectividade ===
echo.

echo Testando conectividade com Telegram...
python -c "
import requests
try:
    response = requests.get('https://api.telegram.org', timeout=10)
    print('[OK] Conectividade com Telegram funcionando')
except Exception as e:
    print(f'[ERRO] Falha na conectividade: {e}')
"

echo.
echo === Configuração de Firewall ===
echo.

echo Verificando regras de firewall...
netsh advfirewall firewall show rule name="VideoBot HTTP" >nul 2>&1
if %errorlevel% neq 0 (
    echo Adicionando regra de firewall para porta 5000...
    netsh advfirewall firewall add rule name="VideoBot HTTP" dir=in action=allow protocol=TCP localport=5000 >nul 2>&1
    if %errorlevel% equ 0 (
        echo [OK] Regra de firewall adicionada
    ) else (
        echo [AVISO] Não foi possível adicionar regra de firewall
        echo Configure manualmente se necessário
    )
) else (
    echo [OK] Regra de firewall já existe
)

echo.
echo === Criação de Atalhos ===
echo.

echo Criando atalhos na área de trabalho...

REM Criar atalho para iniciar bot
powershell -Command "
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\VideoBot - Iniciar Bot.lnk')
$Shortcut.TargetPath = '%CD%\start_bot.bat'
$Shortcut.WorkingDirectory = '%CD%'
$Shortcut.IconLocation = 'shell32.dll,25'
$Shortcut.Description = 'Iniciar VideoBot Telegram'
$Shortcut.Save()
"

REM Criar atalho para interface web
powershell -Command "
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\VideoBot - Interface Web.lnk')
$Shortcut.TargetPath = '%CD%\start_web.bat'
$Shortcut.WorkingDirectory = '%CD%'
$Shortcut.IconLocation = 'shell32.dll,14'
$Shortcut.Description = 'Abrir Interface Web do VideoBot'
$Shortcut.Save()
"

echo [OK] Atalhos criados na área de trabalho

echo.
echo === Teste Final ===
echo.

echo Executando verificação final do sistema...
call check_system.bat

echo.
echo ========================================
echo    Configuração Concluída!
echo ========================================
echo.
echo Próximos passos:
echo.
echo 1. Use os atalhos na área de trabalho para iniciar o sistema
echo 2. Acesse http://localhost:5000/admin para gerenciar produtos
echo 3. Teste seu bot enviando /start no Telegram
echo.
echo Arquivos importantes:
echo - .env: Configurações do sistema
echo - logs/: Arquivos de log
echo - videos/: Seus vídeos para venda
echo - backups/: Backups automáticos
echo.
echo Para suporte, consulte manual_windows.pdf
echo.
pause

