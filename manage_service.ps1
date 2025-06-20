# VideoBot Service Manager for Windows
# Script para gerenciar o serviço VideoBot

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("start", "stop", "restart", "status", "logs", "remove")]
    [string]$Action,
    
    [Parameter(Mandatory=$false)]
    [string]$ServiceName = "VideoBot"
)

function Show-ServiceStatus {
    param([string]$Name)
    
    try {
        $service = Get-Service -Name $Name -ErrorAction Stop
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host "    Status do Serviço VideoBot" -ForegroundColor Cyan
        Write-Host "========================================" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "Nome: $($service.Name)" -ForegroundColor White
        Write-Host "Status: $($service.Status)" -ForegroundColor $(if($service.Status -eq "Running") {"Green"} else {"Red"})
        Write-Host "Tipo de Início: $($service.StartType)" -ForegroundColor White
        
        # Verificar se é gerenciado pelo NSSM
        $nssmInfo = nssm status $Name 2>$null
        if ($nssmInfo) {
            Write-Host "Gerenciado por: NSSM" -ForegroundColor Yellow
        }
        
        Write-Host ""
    } catch {
        Write-Host "[ERRO] Serviço '$Name' não encontrado!" -ForegroundColor Red
    }
}

function Start-VideoBot {
    param([string]$Name)
    
    Write-Host "Iniciando serviço VideoBot..." -ForegroundColor Cyan
    try {
        nssm start $Name
        Start-Sleep -Seconds 3
        Show-ServiceStatus $Name
    } catch {
        Write-Host "[ERRO] Falha ao iniciar serviço: $_" -ForegroundColor Red
    }
}

function Stop-VideoBot {
    param([string]$Name)
    
    Write-Host "Parando serviço VideoBot..." -ForegroundColor Cyan
    try {
        nssm stop $Name
        Start-Sleep -Seconds 3
        Show-ServiceStatus $Name
    } catch {
        Write-Host "[ERRO] Falha ao parar serviço: $_" -ForegroundColor Red
    }
}

function Restart-VideoBot {
    param([string]$Name)
    
    Write-Host "Reiniciando serviço VideoBot..." -ForegroundColor Cyan
    try {
        nssm restart $Name
        Start-Sleep -Seconds 5
        Show-ServiceStatus $Name
    } catch {
        Write-Host "[ERRO] Falha ao reiniciar serviço: $_" -ForegroundColor Red
    }
}

function Show-Logs {
    param([string]$Name)
    
    $logDir = Join-Path $PSScriptRoot "logs"
    
    if (-not (Test-Path $logDir)) {
        Write-Host "[ERRO] Diretório de logs não encontrado: $logDir" -ForegroundColor Red
        return
    }
    
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host "    Logs do VideoBot" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Cyan
    Write-Host ""
    
    # Listar arquivos de log
    $logFiles = Get-ChildItem -Path $logDir -Filter "*.log" | Sort-Object LastWriteTime -Descending
    
    if ($logFiles.Count -eq 0) {
        Write-Host "Nenhum arquivo de log encontrado" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Arquivos de log disponíveis:" -ForegroundColor Yellow
    for ($i = 0; $i -lt $logFiles.Count; $i++) {
        $file = $logFiles[$i]
        Write-Host "  [$i] $($file.Name) - $($file.LastWriteTime)" -ForegroundColor White
    }
    
    Write-Host ""
    $choice = Read-Host "Digite o número do arquivo para visualizar (ou Enter para sair)"
    
    if ($choice -match '^\d+$' -and [int]$choice -lt $logFiles.Count) {
        $selectedFile = $logFiles[[int]$choice]
        Write-Host ""
        Write-Host "Conteúdo de $($selectedFile.Name) (últimas 50 linhas):" -ForegroundColor Cyan
        Write-Host "----------------------------------------" -ForegroundColor Gray
        Get-Content -Path $selectedFile.FullName -Tail 50
    }
}

function Remove-VideoBot {
    param([string]$Name)
    
    Write-Host "ATENÇÃO: Esta ação removerá permanentemente o serviço VideoBot!" -ForegroundColor Red
    $confirm = Read-Host "Digite 'CONFIRMAR' para continuar"
    
    if ($confirm -eq "CONFIRMAR") {
        try {
            nssm stop $Name 2>$null
            nssm remove $Name confirm
            Write-Host "[OK] Serviço removido com sucesso!" -ForegroundColor Green
        } catch {
            Write-Host "[ERRO] Falha ao remover serviço: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Operação cancelada" -ForegroundColor Yellow
    }
}

# Verificar se está executando como administrador para operações que requerem privilégios
$adminRequired = @("start", "stop", "restart", "remove")
if ($adminRequired -contains $Action) {
    if (-NOT ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
        Write-Host "Esta operação requer privilégios de administrador!" -ForegroundColor Red
        Write-Host "Execute o PowerShell como administrador" -ForegroundColor Yellow
        pause
        exit 1
    }
}

# Executar ação solicitada
switch ($Action) {
    "start" { Start-VideoBot $ServiceName }
    "stop" { Stop-VideoBot $ServiceName }
    "restart" { Restart-VideoBot $ServiceName }
    "status" { Show-ServiceStatus $ServiceName }
    "logs" { Show-Logs $ServiceName }
    "remove" { Remove-VideoBot $ServiceName }
}

if ($Action -ne "logs") {
    pause
}

