# VideoBot para Windows 11 - Guia de Início Rápido

## 🚀 Instalação em 3 Passos

### 1. Preparação
- Baixe e instale **Python 3.9+** de [python.org](https://python.org)
- ✅ **IMPORTANTE**: Marque "Add Python to PATH" durante a instalação
- Extraia o arquivo `telegram_video_bot_windows_completo.tar.gz`

### 2. Instalação Automática
- Clique direito em `install.bat` → **"Executar como administrador"**
- Aguarde a instalação completa (pode demorar alguns minutos)

### 3. Configuração
- Execute `setup_wizard.bat` para configuração guiada
- Insira o token do seu bot (obtido via @BotFather no Telegram)
- Pronto! Seu sistema está funcionando

## 📁 Arquivos Principais

### Scripts de Execução (.bat)
- `install.bat` - Instalação automática
- `setup_wizard.bat` - Configuração inicial guiada
- `start_bot.bat` - Iniciar bot do Telegram
- `start_web.bat` - Iniciar interface web
- `start_scheduler.bat` - Iniciar agendador de tarefas
- `backup.bat` - Fazer backup manual
- `check_system.bat` - Verificar status do sistema
- `update_deps.bat` - Atualizar dependências

### Scripts PowerShell (.ps1)
- `install_service.ps1` - Instalar como serviço Windows
- `manage_service.ps1` - Gerenciar serviço
- `auto_update.ps1` - Atualização automática
- `monitor.ps1` - Monitoramento contínuo

### Documentação
- `manual_windows.pdf` - Manual completo para Windows
- `README_WINDOWS.md` - Instruções específicas Windows

## 🎯 Como Usar

### Primeira Execução
1. Execute `install.bat` como administrador
2. Execute `setup_wizard.bat` e siga as instruções
3. Use os atalhos criados na área de trabalho

### Operação Diária
- **Iniciar bot**: Duplo clique no atalho "VideoBot - Iniciar Bot"
- **Gerenciar produtos**: Duplo clique no atalho "VideoBot - Interface Web"
- **Acessar admin**: http://localhost:5000/admin

### Como Serviço Windows (Opcional)
```powershell
# Instalar como serviço (executar como admin)
.\install_service.ps1

# Gerenciar serviço
.\manage_service.ps1 -Action start
.\manage_service.ps1 -Action stop
.\manage_service.ps1 -Action status
```

## 🔧 Configurações Importantes

### Arquivo .env
Configurações principais no arquivo `.env`:
- `BOT_TOKEN` - Token do seu bot
- `DOWNLOAD_EXPIRY_HOURS` - Tempo de expiração dos links
- `MAX_DOWNLOADS_PER_PURCHASE` - Limite de downloads

### Firewall Windows
O sistema adiciona automaticamente regra para porta 5000.
Se necessário, configure manualmente:
- Porta: 5000 (TCP)
- Direção: Entrada
- Ação: Permitir

## 📊 Monitoramento

### Logs do Sistema
- `logs/bot.log` - Logs do bot
- `logs/service_*.log` - Logs do serviço Windows
- `logs/monitor.log` - Logs de monitoramento

### Verificação de Status
```batch
# Verificar sistema completo
check_system.bat

# Monitoramento contínuo
powershell .\monitor.ps1
```

## 🔄 Manutenção

### Backups Automáticos
- Executados diariamente via agendador
- Armazenados em `backups/`
- Retenção: 30 dias (configurável)

### Backup Manual
```batch
backup.bat
```

### Atualizações
```batch
# Atualizar dependências
update_deps.bat

# Atualização completa (PowerShell como admin)
powershell .\auto_update.ps1
```

## 🆘 Solução de Problemas

### Python não encontrado
1. Reinstale Python de [python.org](https://python.org)
2. Marque "Add Python to PATH"
3. Reinicie o prompt de comando

### Bot não responde
1. Verifique token no arquivo `.env`
2. Execute `check_system.bat`
3. Verifique logs em `logs/bot.log`

### Erro de permissões
1. Execute scripts como Administrador
2. Clique direito → "Executar como administrador"

### Interface web não abre
1. Verifique se porta 5000 está livre
2. Configure firewall se necessário
3. Acesse http://localhost:5000

## 📞 Suporte

- **Manual completo**: `manual_windows.pdf`
- **Logs do sistema**: Pasta `logs/`
- **Verificação**: `check_system.bat`

## 🎉 Pronto para Vender!

Após a configuração:
1. Adicione seus vídeos na pasta `videos/`
2. Configure produtos via interface web
3. Divulgue seu bot no Telegram
4. Comece a vender automaticamente!

---
**VideoBot Windows Edition** - Vendas automatizadas 24/7 no seu PC!

