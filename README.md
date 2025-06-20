# Telegram Video Bot

Sistema completo para vendas automatizadas de vídeos no Telegram usando Telegram Stars.

## Características

- ✅ Bot Telegram com interface amigável
- ✅ Pagamentos via Telegram Stars (sem comissão)
- ✅ Entrega automatizada de vídeos
- ✅ Links de download temporários e seguros
- ✅ Controle de acesso e limite de downloads
- ✅ Interface web de administração
- ✅ Banco de dados SQLite/PostgreSQL

## Instalação

### 1. Clonar e configurar

```bash
git clone <seu-repositorio>
cd telegram_video_bot
pip install -r requirements.txt
```

### 2. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```bash
cp .env.example .env
```

Edite o arquivo `.env` com suas configurações:

```env
BOT_TOKEN=seu_token_do_botfather
WEBHOOK_URL=https://seu-dominio.com
SECRET_KEY=sua_chave_secreta
```

### 3. Criar bot no Telegram

1. Converse com [@BotFather](https://t.me/BotFather)
2. Use `/newbot` para criar um novo bot
3. Copie o token fornecido para `BOT_TOKEN`

## Uso

### Modo Desenvolvimento (Polling)

```bash
python run_bot.py
```

### Modo Produção (Webhook)

```bash
python app.py
```

## Estrutura do Projeto

```
telegram_video_bot/
├── app.py              # Aplicação Flask principal
├── bot.py              # Lógica do bot Telegram
├── database.py         # Gerenciamento do banco de dados
├── run_bot.py          # Script para modo polling
├── requirements.txt    # Dependências Python
├── .env.example        # Exemplo de configuração
└── videos/            # Diretório para armazenar vídeos
```

## API Endpoints

- `GET /` - Status da API
- `POST /webhook` - Webhook do Telegram
- `GET /download/<token>` - Download de vídeos
- `GET /api/products` - Listar produtos
- `POST /api/products` - Criar produto
- `GET /api/stats` - Estatísticas

## Comandos do Bot

- `/start` - Iniciar bot e criar conta
- `/catalogo` - Ver vídeos disponíveis
- `/help` - Ajuda e suporte

## Fluxo de Compra

1. Usuário navega no catálogo (`/catalogo`)
2. Seleciona vídeo e clica em "Comprar"
3. Bot gera fatura com Telegram Stars
4. Usuário paga via interface do Telegram
5. Bot valida pagamento automaticamente
6. Sistema gera link temporário de download
7. Usuário recebe link e baixa o vídeo

## Segurança

- Links de download expiram em 24h
- Máximo de 3 downloads por compra
- Tokens únicos e seguros
- Validação de usuário no download
- Logs de acesso completos

## Deploy

### Heroku

```bash
git init
git add .
git commit -m "Initial commit"
heroku create seu-app-name
git push heroku main
```

### VPS/Servidor

```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar variáveis de ambiente
export BOT_TOKEN="seu_token"
export WEBHOOK_URL="https://seu-dominio.com"

# Executar
python app.py
```

## Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## Licença

MIT License - veja LICENSE para detalhes.

## Suporte

Para dúvidas e suporte, abra uma issue no GitHub.

