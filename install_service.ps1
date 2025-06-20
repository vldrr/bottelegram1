# VideoBot Service Installer for Windows
# Este script instala o VideoBot como serviço do Windows

param(
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "VideoBot",
    
    [Parameter(Mandatory=$false)]
    [string]$DisplayName = "VideoBot Telegram Service",
    
    [Parameter(Mandatory=$false)]
    [string]$Description = "Serviço automatizado de vendas de vídeos no Telegram",
    
    [Parameter(Mandatory=$false)]
    [string]$InstallPath = $PSScriptRoot
)

# Verificar se está executando como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Este script deve ser executado como Administrador!" -ForegroundColor Red
    Write-Host "Clique direito no PowerShell e selecione 'Executar como administrador'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    VideoBot Service Installer" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se Python está instalado
try {
    $pythonVersion = python --version 2>&1
    Write-Host "[OK] Python encontrado: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "[ERRO] Python não encontrado!" -ForegroundColor Red
    Write-Host "Instale o Python 3.9+ antes de continuar" -ForegroundColor Yellow
    pause
    exit 1
}

# Verificar se o diretório de instalação existe
if (-not (Test-Path $InstallPath)) {
    Write-Host "[ERRO] Diretório de instalação não encontrado: $InstallPath" -ForegroundColor Red
    pause
    exit 1
}

# Verificar se ambiente virtual existe
$venvPath = Join-Path $InstallPath "venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "[ERRO] Ambiente virtual não encontrado!" -ForegroundColor Red
    Write-Host "Execute install.bat primeiro" -ForegroundColor Yellow
    pause
    exit 1
}

# Criar script wrapper para o serviço
$wrapperScript = @"
@echo off
cd /d "$InstallPath"
call venv\Scripts\activate.bat
python app.py
"@

$wrapperPath = Join-Path $InstallPath "service_wrapper.bat"
$wrapperScript | Out-File -FilePath $wrapperPath -Encoding ASCII

Write-Host "[OK] Script wrapper criado: $wrapperPath" -ForegroundColor Green

# Verificar se NSSM está disponível
$nssmPath = Get-Command nssm -ErrorAction SilentlyContinue
if (-not $nssmPath) {
    Write-Host "[AVISO] NSSM não encontrado. Baixando..." -ForegroundColor Yellow
    
    # Criar diretório temporário
    $tempDir = Join-Path $env:TEMP "nssm"
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
    
    # Download NSSM
    $nssmUrl = "https://nssm.cc/release/nssm-2.24.zip"
    $nssmZip = Join-Path $tempDir "nssm.zip"
    
    try {
        Invoke-WebRequest -Uri $nssmUrl -OutFile $nssmZip
        Expand-Archive -Path $nssmZip -DestinationPath $tempDir -Force
        
        # Copiar NSSM para diretório do sistema
        $nssmExe = Join-Path $tempDir "nssm-2.24\win64\nssm.exe"
        $systemPath = Join-Path $env:SystemRoot "System32\nssm.exe"
        Copy-Item $nssmExe $systemPath -Force
        
        Write-Host "[OK] NSSM instalado com sucesso" -ForegroundColor Green
    } catch {
        Write-Host "[ERRO] Falha ao baixar NSSM: $_" -ForegroundColor Red
        Write-Host "Baixe manualmente de https://nssm.cc e coloque nssm.exe no PATH" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# Parar serviço se já existir
$existingService = Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if ($existingService) {
    Write-Host "[AVISO] Serviço $ServiceName já existe. Removendo..." -ForegroundColor Yellow
    nssm stop $ServiceName
    nssm remove $ServiceName confirm
}

# Instalar serviço
Write-Host "Instalando serviço $ServiceName..." -ForegroundColor Cyan

nssm install $ServiceName $wrapperPath
nssm set $ServiceName DisplayName "$DisplayName"
nssm set $ServiceName Description "$Description"
nssm set $ServiceName Start SERVICE_AUTO_START
nssm set $ServiceName AppDirectory "$InstallPath"

# Configurar logs
$logDir = Join-Path $InstallPath "logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$stdoutLog = Join-Path $logDir "service_stdout.log"
$stderrLog = Join-Path $logDir "service_stderr.log"

nssm set $ServiceName AppStdout "$stdoutLog"
nssm set $ServiceName AppStderr "$stderrLog"
nssm set $ServiceName AppRotateFiles 1
nssm set $ServiceName AppRotateOnline 1
nssm set $ServiceName AppRotateSeconds 86400
nssm set $ServiceName AppRotateBytes 1048576

Write-Host "[OK] Serviço instalado com sucesso!" -ForegroundColor Green

# Iniciar serviço
Write-Host "Iniciando serviço..." -ForegroundColor Cyan
nssm start $ServiceName

Start-Sleep -Seconds 3

# Verificar status
$serviceStatus = Get-Service -Name $ServiceName
if ($serviceStatus.Status -eq "Running") {
    Write-Host "[OK] Serviço iniciado com sucesso!" -ForegroundColor Green
    Write-Host "Status: $($serviceStatus.Status)" -ForegroundColor Green
} else {
    Write-Host "[ERRO] Falha ao iniciar serviço" -ForegroundColor Red
    Write-Host "Status: $($serviceStatus.Status)" -ForegroundColor Red
    Write-Host "Verifique os logs em: $logDir" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Instalação do Serviço Concluída" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Comandos úteis:" -ForegroundColor Yellow
Write-Host "  Iniciar:  nssm start $ServiceName" -ForegroundColor White
Write-Host "  Parar:    nssm stop $ServiceName" -ForegroundColor White
Write-Host "  Status:   Get-Service $ServiceName" -ForegroundColor White
Write-Host "  Remover:  nssm remove $ServiceName" -ForegroundColor White
Write-Host ""
Write-Host "Logs do serviço: $logDir" -ForegroundColor Cyan
Write-Host ""

pause

