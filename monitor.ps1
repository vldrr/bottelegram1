# VideoBot System Monitor for Windows
# Script para monitoramento contínuo do sistema

param(
    [Parameter(Mandatory=$false)]
    [int]$IntervalSeconds = 300,  # 5 minutos
    
    [Parameter(Mandatory=$false)]
    [switch]$EmailAlerts,
    
    [Parameter(Mandatory=$false)]
    [string]$EmailTo = "",
    
    [Parameter(Mandatory=$false)]
    [switch]$LogToFile = $true
)

# Configurações de monitoramento
$thresholds = @{
    CpuPercent = 80
    MemoryPercent = 85
    DiskPercent = 90
    ResponseTimeMs = 5000
}

$installPath = $PSScriptRoot
$logPath = Join-Path $installPath "logs\monitor.log"

# Função para log
function Write-Log {
    param([string]$Message, [string]$Level = "INFO")
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    Write-Host $logEntry -ForegroundColor $(
        switch ($Level) {
            "ERROR" { "Red" }
            "WARN" { "Yellow" }
            "INFO" { "White" }
            default { "Gray" }
        }
    )
    
    if ($LogToFile) {
        $logEntry | Out-File -FilePath $logPath -Append -Encoding UTF8
    }
}

# Função para verificar uso de CPU
function Get-CpuUsage {
    $cpu = Get-WmiObject -Class Win32_Processor | Measure-Object -Property LoadPercentage -Average
    return [math]::Round($cpu.Average, 2)
}

# Função para verificar uso de memória
function Get-MemoryUsage {
    $os = Get-WmiObject -Class Win32_OperatingSystem
    $totalMemory = $os.TotalVisibleMemorySize
    $freeMemory = $os.FreePhysicalMemory
    $usedMemory = $totalMemory - $freeMemory
    return [math]::Round(($usedMemory / $totalMemory) * 100, 2)
}

# Função para verificar uso de disco
function Get-DiskUsage {
    $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
    $usedSpace = $disk.Size - $disk.FreeSpace
    return [math]::Round(($usedSpace / $disk.Size) * 100, 2)
}

# Função para verificar status do serviço
function Get-ServiceStatus {
    param([string]$ServiceName)
    
    try {
        $service = Get-Service -Name $ServiceName -ErrorAction Stop
        return @{
            Status = $service.Status
            StartType = $service.StartType
            Running = ($service.Status -eq "Running")
        }
    } catch {
        return @{
            Status = "NotFound"
            StartType = "Unknown"
            Running = $false
        }
    }
}

# Função para verificar conectividade
function Test-Connectivity {
    try {
        $response = Invoke-WebRequest -Uri "https://api.telegram.org" -TimeoutSec 10 -UseBasicParsing
        return @{
            Success = $true
            ResponseTime = $response.Headers["X-Response-Time"]
            StatusCode = $response.StatusCode
        }
    } catch {
        return @{
            Success = $false
            Error = $_.Exception.Message
            StatusCode = 0
        }
    }
}

# Função para verificar integridade do banco
function Test-Database {
    try {
        $dbPath = Join-Path $installPath "bot_database.db"
        if (-not (Test-Path $dbPath)) {
            return @{ Success = $false; Error = "Database file not found" }
        }
        
        # Verificar se arquivo não está corrompido (verificação básica)
        $fileInfo = Get-Item $dbPath
        if ($fileInfo.Length -eq 0) {
            return @{ Success = $false; Error = "Database file is empty" }
        }
        
        return @{ Success = $true; Size = $fileInfo.Length }
    } catch {
        return @{ Success = $false; Error = $_.Exception.Message }
    }
}

# Função para enviar alerta por email
function Send-Alert {
    param([string]$Subject, [string]$Body)
    
    if (-not $EmailAlerts -or -not $EmailTo) {
        return
    }
    
    try {
        # Configurar SMTP (ajustar conforme necessário)
        $smtpServer = "smtp.gmail.com"
        $smtpPort = 587
        $smtpUser = "seu-email@gmail.com"
        $smtpPass = "sua-senha-app"
        
        $message = New-Object System.Net.Mail.MailMessage
        $message.From = $smtpUser
        $message.To.Add($EmailTo)
        $message.Subject = $Subject
        $message.Body = $Body
        
        $smtp = New-Object System.Net.Mail.SmtpClient($smtpServer, $smtpPort)
        $smtp.EnableSsl = $true
        $smtp.Credentials = New-Object System.Net.NetworkCredential($smtpUser, $smtpPass)
        $smtp.Send($message)
        
        Write-Log "Alerta enviado por email: $Subject"
    } catch {
        Write-Log "Falha ao enviar email: $($_.Exception.Message)" "ERROR"
    }
}

# Função principal de monitoramento
function Start-Monitoring {
    Write-Log "Iniciando monitoramento do VideoBot"
    Write-Log "Intervalo: $IntervalSeconds segundos"
    Write-Log "Alertas por email: $EmailAlerts"
    
    while ($true) {
        try {
            # Coletar métricas
            $cpuUsage = Get-CpuUsage
            $memoryUsage = Get-MemoryUsage
            $diskUsage = Get-DiskUsage
            $serviceStatus = Get-ServiceStatus "VideoBot"
            $connectivity = Test-Connectivity
            $database = Test-Database
            
            # Log das métricas
            Write-Log "CPU: $cpuUsage% | Memória: $memoryUsage% | Disco: $diskUsage% | Serviço: $($serviceStatus.Status)"
            
            # Verificar thresholds e gerar alertas
            $alerts = @()
            
            if ($cpuUsage -gt $thresholds.CpuPercent) {
                $alerts += "CPU usage high: $cpuUsage%"
            }
            
            if ($memoryUsage -gt $thresholds.MemoryPercent) {
                $alerts += "Memory usage high: $memoryUsage%"
            }
            
            if ($diskUsage -gt $thresholds.DiskPercent) {
                $alerts += "Disk usage high: $diskUsage%"
            }
            
            if (-not $serviceStatus.Running) {
                $alerts += "VideoBot service is not running"
            }
            
            if (-not $connectivity.Success) {
                $alerts += "Telegram API connectivity failed: $($connectivity.Error)"
            }
            
            if (-not $database.Success) {
                $alerts += "Database check failed: $($database.Error)"
            }
            
            # Enviar alertas se necessário
            if ($alerts.Count -gt 0) {
                $alertMessage = "VideoBot System Alert`n`n" + ($alerts -join "`n")
                Write-Log "ALERTA: $($alerts -join '; ')" "WARN"
                Send-Alert "VideoBot System Alert" $alertMessage
            }
            
            # Aguardar próximo ciclo
            Start-Sleep -Seconds $IntervalSeconds
            
        } catch {
            Write-Log "Erro no monitoramento: $($_.Exception.Message)" "ERROR"
            Start-Sleep -Seconds 60  # Aguardar 1 minuto em caso de erro
        }
    }
}

# Verificar se diretório de logs existe
$logDir = Split-Path $logPath -Parent
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "    VideoBot System Monitor" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Configurações:" -ForegroundColor Yellow
Write-Host "  Intervalo: $IntervalSeconds segundos" -ForegroundColor White
Write-Host "  Log: $logPath" -ForegroundColor White
Write-Host "  Email: $EmailAlerts" -ForegroundColor White
Write-Host ""
Write-Host "Pressione Ctrl+C para parar o monitoramento" -ForegroundColor Yellow
Write-Host ""

# Iniciar monitoramento
Start-Monitoring

