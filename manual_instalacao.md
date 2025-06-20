# Manual de Instalação e Configuração - VideoBot

## Pré-requisitos do Sistema

Antes de iniciar a instalação do VideoBot, certifique-se de que seu ambiente atende aos seguintes requisitos mínimos:

### Requisitos de Hardware
- **CPU**: 2 cores (recomendado: 4+ cores)
- **RAM**: 2GB (recomendado: 4GB+)
- **Armazenamento**: 10GB livres (recomendado: 50GB+ para vídeos)
- **Rede**: Conexão estável com internet

### Requisitos de Software
- **Sistema Operacional**: Ubuntu 20.04+ / CentOS 8+ / Debian 11+
- **Python**: 3.9 ou superior
- **pip**: Gerenciador de pacotes Python
- **Git**: Para clonagem do repositório

### Dependências Opcionais
- **FFmpeg**: Para processamento de vídeo e geração de thumbnails
- **PostgreSQL**: Para ambiente de produção (SQLite para desenvolvimento)
- **Nginx**: Para proxy reverso em produção
- **SSL Certificate**: Para HTTPS em produção

## Instalação Passo a Passo

### 1. Preparação do Ambiente

```bash
# Atualizar sistema
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y python3 python3-pip python3-venv git curl wget

# Instalar FFmpeg (opcional, para processamento de vídeo)
sudo apt install -y ffmpeg

# Criar usuário dedicado (recomendado)
sudo useradd -m -s /bin/bash videobot
sudo usermod -aG sudo videobot
```

### 2. Download e Configuração

```bash
# Mudar para usuário videobot
sudo su - videobot

# Clonar repositório
git clone https://github.com/seu-usuario/telegram-video-bot.git
cd telegram-video-bot

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
```

### 3. Configuração do Bot no Telegram

1. **Criar Bot no BotFather**:
   - Abra o Telegram e procure por @BotFather
   - Envie `/newbot` e siga as instruções
   - Escolha um nome e username para seu bot
   - Salve o token fornecido

2. **Configurar Pagamentos** (se necessário):
   - No BotFather, use `/mybots`
   - Selecione seu bot → Bot Settings → Payments
   - Configure um provedor de pagamento

### 4. Configuração das Variáveis de Ambiente

```bash
# Copiar arquivo de exemplo
cp .env.example .env

# Editar configurações
nano .env
```

Configure as seguintes variáveis:

```env
# Token do Bot (obrigatório)
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz

# URL do Webhook (para produção)
WEBHOOK_URL=https://seu-dominio.com

# Configurações do Banco
DATABASE_URL=sqlite:///bot_database.db

# Configurações de Segurança
SECRET_KEY=sua_chave_secreta_muito_segura_aqui

# Configurações de Download
DOWNLOAD_EXPIRY_HOURS=24
MAX_DOWNLOADS_PER_PURCHASE=3

# Configurações de Armazenamento
STORAGE_PATH=/home/videobot/telegram-video-bot/videos
```

### 5. Inicialização do Banco de Dados

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Inicializar banco de dados
python3 -c "
from database import DatabaseManager
db = DatabaseManager()
print('Banco de dados inicializado com sucesso!')
"
```

### 6. Teste da Instalação

```bash
# Testar bot em modo polling (desenvolvimento)
python3 run_bot.py
```

Se tudo estiver configurado corretamente, você verá:
```
🤖 Iniciando Telegram Video Bot...
📋 Modo: Polling (desenvolvimento)
✅ Bot configurado com sucesso!
🚀 Bot iniciado! Pressione Ctrl+C para parar.
```

## Configuração para Produção

### 1. Configuração do Nginx

```bash
# Instalar Nginx
sudo apt install -y nginx

# Criar configuração do site
sudo nano /etc/nginx/sites-available/videobot
```

Conteúdo do arquivo:

```nginx
server {
    listen 80;
    server_name seu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    client_max_body_size 100M;
}
```

```bash
# Ativar site
sudo ln -s /etc/nginx/sites-available/videobot /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 2. Configuração SSL com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obter certificado SSL
sudo certbot --nginx -d seu-dominio.com

# Verificar renovação automática
sudo certbot renew --dry-run
```

### 3. Configuração do Systemd

```bash
# Criar arquivo de serviço
sudo nano /etc/systemd/system/videobot.service
```

Conteúdo do arquivo:

```ini
[Unit]
Description=VideoBot Telegram Service
After=network.target

[Service]
Type=simple
User=videobot
WorkingDirectory=/home/videobot/telegram-video-bot
Environment=PATH=/home/videobot/telegram-video-bot/venv/bin
ExecStart=/home/videobot/telegram-video-bot/venv/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Ativar e iniciar serviço
sudo systemctl daemon-reload
sudo systemctl enable videobot
sudo systemctl start videobot

# Verificar status
sudo systemctl status videobot
```

### 4. Configuração do Webhook

```bash
# Configurar webhook do Telegram
curl -X POST "https://api.telegram.org/bot<SEU_TOKEN>/setWebhook" \
     -H "Content-Type: application/json" \
     -d '{"url": "https://seu-dominio.com/webhook"}'
```

## Configuração do PostgreSQL (Produção)

### 1. Instalação

```bash
# Instalar PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Criar usuário e banco
sudo -u postgres psql
```

```sql
CREATE USER videobot WITH PASSWORD 'senha_segura';
CREATE DATABASE videobot_db OWNER videobot;
GRANT ALL PRIVILEGES ON DATABASE videobot_db TO videobot;
\q
```

### 2. Configuração

```bash
# Instalar driver Python
pip install psycopg2-binary

# Atualizar .env
nano .env
```

```env
DATABASE_URL=postgresql://videobot:senha_segura@localhost/videobot_db
```

## Monitoramento e Logs

### 1. Configuração de Logs

```bash
# Criar diretório de logs
mkdir -p /home/videobot/logs

# Configurar rotação de logs
sudo nano /etc/logrotate.d/videobot
```

```
/home/videobot/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 videobot videobot
}
```

### 2. Monitoramento com Systemd

```bash
# Ver logs em tempo real
sudo journalctl -u videobot -f

# Ver logs específicos
sudo journalctl -u videobot --since "1 hour ago"
```

## Backup e Recuperação

### 1. Script de Backup

```bash
# Criar script de backup
nano /home/videobot/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/videobot/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
if [[ $DATABASE_URL == *"postgresql"* ]]; then
    pg_dump $DATABASE_URL > $BACKUP_DIR/db_backup_$DATE.sql
else
    cp bot_database.db $BACKUP_DIR/db_backup_$DATE.db
fi

# Backup dos vídeos
tar -czf $BACKUP_DIR/videos_backup_$DATE.tar.gz videos/

# Manter apenas últimos 7 backups
find $BACKUP_DIR -name "*.sql" -o -name "*.db" -o -name "*.tar.gz" | sort | head -n -21 | xargs rm -f

echo "Backup concluído: $DATE"
```

```bash
# Tornar executável
chmod +x /home/videobot/backup.sh

# Agendar backup diário
crontab -e
```

```cron
0 3 * * * /home/videobot/backup.sh >> /home/videobot/logs/backup.log 2>&1
```

## Solução de Problemas Comuns

### 1. Bot não responde

**Problema**: Bot não recebe mensagens
**Solução**:
```bash
# Verificar token
curl "https://api.telegram.org/bot<SEU_TOKEN>/getMe"

# Verificar webhook
curl "https://api.telegram.org/bot<SEU_TOKEN>/getWebhookInfo"

# Reiniciar serviço
sudo systemctl restart videobot
```

### 2. Erro de permissões

**Problema**: Erro ao acessar arquivos
**Solução**:
```bash
# Corrigir permissões
sudo chown -R videobot:videobot /home/videobot/telegram-video-bot
sudo chmod -R 755 /home/videobot/telegram-video-bot
```

### 3. Erro de banco de dados

**Problema**: Erro de conexão com banco
**Solução**:
```bash
# Verificar status do PostgreSQL
sudo systemctl status postgresql

# Testar conexão
psql $DATABASE_URL -c "SELECT 1;"

# Reinicializar banco se necessário
python3 -c "from database import DatabaseManager; DatabaseManager()"
```

### 4. Downloads não funcionam

**Problema**: Links de download não funcionam
**Solução**:
```bash
# Verificar permissões dos arquivos
ls -la videos/

# Verificar configuração do Nginx
sudo nginx -t

# Verificar logs
sudo journalctl -u videobot -n 50
```

## Manutenção Regular

### 1. Tarefas Diárias
- Verificar logs de erro
- Monitorar uso de disco
- Verificar status dos serviços

### 2. Tarefas Semanais
- Atualizar dependências
- Verificar backups
- Analisar métricas de performance

### 3. Tarefas Mensais
- Atualizar sistema operacional
- Revisar configurações de segurança
- Otimizar banco de dados

## Comandos Úteis

```bash
# Status do sistema
sudo systemctl status videobot nginx postgresql

# Logs em tempo real
sudo journalctl -u videobot -f

# Reiniciar todos os serviços
sudo systemctl restart videobot nginx

# Verificar uso de disco
df -h
du -sh /home/videobot/telegram-video-bot/videos/

# Testar conectividade
curl -I https://seu-dominio.com/

# Backup manual
/home/videobot/backup.sh
```

## Suporte e Documentação

Para suporte adicional:
- Consulte os logs em `/home/videobot/logs/`
- Verifique a documentação técnica completa
- Entre em contato com o suporte técnico

Este manual cobre os aspectos essenciais da instalação e configuração. Para configurações avançadas ou cenários específicos, consulte a documentação técnica detalhada.

