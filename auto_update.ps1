# VideoBot Auto-Updater for Windows
# Script para atualização automática do sistema

param(
    [Parameter(Mandatory=$false)]
    [switch]$Force,
    
    [Parameter(Mandatory=$false)]
    [switch]$BackupFirst = $true,
    
    [Parameter(Mandatory=$false)]
    [string]$UpdateSource = "https://github.com/seu-usuario/videobot/releases/latest"
)

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    VideoBot Auto-Updater" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Verificar se está executando como administrador
if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Este script deve ser executado como Administrador!" -ForegroundColor Red
    pause
    exit 1
}

$installPath = $PSScriptRoot
$backupPath = Join-Path $installPath "backups"
$tempPath = Join-Path $env:TEMP "videobot_update"

# Função para criar backup
function New-Backup {
    Write-Host "Criando backup antes da atualização..." -ForegroundColor Cyan
    
    if (-not (Test-Path $backupPath)) {
        New-Item -ItemType Directory -Path $backupPath -Force | Out-Null
    }
    
    $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $backupName = "update_backup_$timestamp"
    $fullBackupPath = Join-Path $backupPath $backupName
    
    # Criar diretório de backup
    New-Item -ItemType Directory -Path $fullBackupPath -Force | Out-Null
    
    # Backup de arquivos críticos
    $criticalFiles = @(
        "*.py",
        "*.bat",
        "*.ps1",
        ".env",
        "requirements.txt",
        "bot_database.db"
    )
    
    foreach ($pattern in $criticalFiles) {
        $files = Get-ChildItem -Path $installPath -Filter $pattern -ErrorAction SilentlyContinue
        foreach ($file in $files) {
            Copy-Item $file.FullName $fullBackupPath -Force
        }
    }
    
    # Backup de diretórios importantes
    $criticalDirs = @("templates", "static", "videos")
    foreach ($dir in $criticalDirs) {
        $sourcePath = Join-Path $installPath $dir
        if (Test-Path $sourcePath) {
            $destPath = Join-Path $fullBackupPath $dir
            Copy-Item $sourcePath $destPath -Recurse -Force
        }
    }
    
    Write-Host "[OK] Backup criado: $fullBackupPath" -ForegroundColor Green
    return $fullBackupPath
}

# Função para verificar versão atual
function Get-CurrentVersion {
    $versionFile = Join-Path $installPath "VERSION"
    if (Test-Path $versionFile) {
        return Get-Content $versionFile -Raw
    }
    return "unknown"
}

# Função para baixar atualização
function Get-Update {
    param([string]$Source)
    
    Write-Host "Verificando atualizações disponíveis..." -ForegroundColor Cyan
    
    # Simular verificação de atualização (implementar lógica real conforme necessário)
    Write-Host "[INFO] Esta é uma versão de demonstração do auto-updater" -ForegroundColor Yellow
    Write-Host "[INFO] Implementar lógica de download real conforme necessário" -ForegroundColor Yellow
    
    return $false  # Retornar true quando atualização estiver disponível
}

# Função para aplicar atualização
function Install-Update {
    param([string]$UpdatePath)
    
    Write-Host "Aplicando atualização..." -ForegroundColor Cyan
    
    # Parar serviços se estiverem rodando
    $services = @("VideoBot")
    foreach ($service in $services) {
        try {
            $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
            if ($svc -and $svc.Status -eq "Running") {
                Write-Host "Parando serviço $service..." -ForegroundColor Yellow
                nssm stop $service
                Start-Sleep -Seconds 3
            }
        } catch {
            Write-Host "[AVISO] Não foi possível parar serviço $service" -ForegroundColor Yellow
        }
    }
    
    # Aplicar arquivos de atualização
    # (Implementar lógica de cópia de arquivos aqui)
    
    # Atualizar dependências
    Write-Host "Atualizando dependências..." -ForegroundColor Cyan
    & "$installPath\venv\Scripts\activate.bat"
    pip install --upgrade -r "$installPath\requirements.txt"
    
    # Reiniciar serviços
    foreach ($service in $services) {
        try {
            $svc = Get-Service -Name $service -ErrorAction SilentlyContinue
            if ($svc) {
                Write-Host "Iniciando serviço $service..." -ForegroundColor Yellow
                nssm start $service
                Start-Sleep -Seconds 3
            }
        } catch {
            Write-Host "[AVISO] Não foi possível iniciar serviço $service" -ForegroundColor Yellow
        }
    }
    
    Write-Host "[OK] Atualização aplicada com sucesso!" -ForegroundColor Green
}

# Função para rollback
function Restore-Backup {
    param([string]$BackupPath)
    
    Write-Host "Restaurando backup..." -ForegroundColor Yellow
    
    if (-not (Test-Path $BackupPath)) {
        Write-Host "[ERRO] Backup não encontrado: $BackupPath" -ForegroundColor Red
        return $false
    }
    
    # Parar serviços
    nssm stop VideoBot 2>$null
    
    # Restaurar arquivos
    $backupFiles = Get-ChildItem -Path $BackupPath -File
    foreach ($file in $backupFiles) {
        $destPath = Join-Path $installPath $file.Name
        Copy-Item $file.FullName $destPath -Force
    }
    
    # Restaurar diretórios
    $backupDirs = Get-ChildItem -Path $BackupPath -Directory
    foreach ($dir in $backupDirs) {
        $destPath = Join-Path $installPath $dir.Name
        if (Test-Path $destPath) {
            Remove-Item $destPath -Recurse -Force
        }
        Copy-Item $dir.FullName $destPath -Recurse -Force
    }
    
    # Reiniciar serviços
    nssm start VideoBot 2>$null
    
    Write-Host "[OK] Backup restaurado com sucesso!" -ForegroundColor Green
    return $true
}

# Processo principal de atualização
try {
    $currentVersion = Get-CurrentVersion
    Write-Host "Versão atual: $currentVersion" -ForegroundColor White
    
    # Criar backup se solicitado
    $backupLocation = $null
    if ($BackupFirst) {
        $backupLocation = New-Backup
    }
    
    # Verificar atualizações
    $updateAvailable = Get-Update $UpdateSource
    
    if (-not $updateAvailable -and -not $Force) {
        Write-Host "[INFO] Nenhuma atualização disponível" -ForegroundColor Green
        Write-Host "Use -Force para forçar reinstalação" -ForegroundColor Yellow
    } else {
        if ($Force) {
            Write-Host "[INFO] Forçando atualização..." -ForegroundColor Yellow
        }
        
        # Confirmar atualização
        if (-not $Force) {
            $confirm = Read-Host "Atualização disponível. Continuar? (s/N)"
            if ($confirm -ne "s" -and $confirm -ne "S") {
                Write-Host "Atualização cancelada" -ForegroundColor Yellow
                exit 0
            }
        }
        
        # Aplicar atualização
        Install-Update $tempPath
        
        # Verificar se atualização foi bem-sucedida
        Write-Host "Verificando integridade pós-atualização..." -ForegroundColor Cyan
        $checkResult = & "$installPath\check_system.bat"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "[ERRO] Verificação pós-atualização falhou!" -ForegroundColor Red
            if ($backupLocation) {
                Write-Host "Restaurando backup..." -ForegroundColor Yellow
                Restore-Backup $backupLocation
            }
        } else {
            Write-Host "[OK] Atualização concluída com sucesso!" -ForegroundColor Green
        }
    }
    
} catch {
    Write-Host "[ERRO] Falha durante atualização: $_" -ForegroundColor Red
    if ($backupLocation) {
        Write-Host "Restaurando backup..." -ForegroundColor Yellow
        Restore-Backup $backupLocation
    }
} finally {
    # Limpeza
    if (Test-Path $tempPath) {
        Remove-Item $tempPath -Recurse -Force -ErrorAction SilentlyContinue
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    Processo de Atualização Finalizado" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

pause

