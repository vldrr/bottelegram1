# VideoBot para Windows 11

Sistema completo de vendas automatizadas de vídeos no Telegram, adaptado especificamente para Windows 11.

## 🚀 Instalação Rápida

1. **Baixe e extraia** o arquivo do projeto
2. **Execute** `install.bat` como Administrador
3. **Configure** o arquivo `.env` com seu token do bot
4. **Execute** `start_bot.bat` para iniciar o bot

## 📋 Pré-requisitos

- **Windows 11** (ou Windows 10)
- **Python 3.9+** instalado do [python.org](https://python.org)
- **Conexão com internet**
- **Token do bot** do Telegram (obtido via @BotFather)

## 🛠️ Scripts Disponíveis

### Scripts Principais
- `install.bat` - Instalação automática do sistema
- `start_bot.bat` - Iniciar bot do Telegram
- `start_web.bat` - Iniciar interface web (http://localhost:5000)
- `start_scheduler.bat` - Iniciar agendador de tarefas

### Scripts de Manutenção
- `check_system.bat` - Verificar status do sistema
- `backup.bat` - Fazer backup manual
- `update_deps.bat` - Atualizar dependências

## 📁 Estrutura de Diretórios

```
telegram_video_bot_windows/
├── install.bat              # Script de instalação
├── start_bot.bat           # Iniciar bot
├── start_web.bat           # Iniciar interface web
├── start_scheduler.bat     # Iniciar agendador
├── backup.bat              # Backup manual
├── check_system.bat        # Verificação do sistema
├── .env.example            # Configurações de exemplo
├── requirements.txt        # Dependências Python
├── videos/                 # Vídeos para venda
├── uploads/                # Uploads temporários
├── backups/                # Backups automáticos
├── logs/                   # Arquivos de log
├── templates/              # Templates HTML
├── static/                 # Arquivos estáticos
└── venv/                   # Ambiente virtual Python
```

## ⚙️ Configuração

1. **Copie** `.env.example` para `.env`
2. **Edite** `.env` e configure:
   - `BOT_TOKEN` - Token do seu bot do Telegram
   - `SECRET_KEY` - Chave secreta única
   - Outras configurações conforme necessário

## 🔧 Uso

### Iniciar o Sistema
```batch
# Instalar (primeira vez)
install.bat

# Iniciar bot
start_bot.bat

# Iniciar interface web (opcional)
start_web.bat
```

### Acessar Interface Web
- **Dashboard**: http://localhost:5000
- **Painel Admin**: http://localhost:5000/admin

### Verificar Sistema
```batch
check_system.bat
```

## 📊 Monitoramento

- **Logs**: Pasta `logs/`
- **Backups**: Pasta `backups/`
- **Status**: Execute `check_system.bat`

## 🆘 Solução de Problemas

### Python não encontrado
1. Instale Python do [python.org](https://python.org)
2. Marque "Add Python to PATH" durante instalação
3. Reinicie o prompt de comando

### Erro de permissões
1. Execute scripts como Administrador
2. Clique direito → "Executar como administrador"

### Bot não responde
1. Verifique token no arquivo `.env`
2. Teste conectividade: `check_system.bat`
3. Verifique logs em `logs/bot.log`

## 📚 Documentação

- `manual_windows.pdf` - Manual completo para Windows
- `guia_usuario.pdf` - Guia para vendedores
- `documentacao_tecnica.pdf` - Documentação técnica

## 🔄 Atualizações

Para atualizar o sistema:
1. Faça backup: `backup.bat`
2. Substitua arquivos do projeto
3. Execute: `install.bat`

## 📞 Suporte

Para suporte técnico, consulte:
- Manual completo em PDF
- Logs do sistema em `logs/`
- Documentação técnica incluída

---

**Desenvolvido por Manus AI** - Sistema profissional para vendas automatizadas no Telegram

