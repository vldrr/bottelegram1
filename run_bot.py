import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Adicionar diretório atual ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot import create_bot

def main():
    """Função principal para executar o bot em modo polling"""
    
    # Verificar token
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token or bot_token == 'SEU_TOKEN_AQUI':
        print("❌ Erro: Token do bot não configurado!")
        print("Configure BOT_TOKEN no arquivo .env")
        return
    
    print("🤖 Iniciando Telegram Video Bot...")
    print("📋 Modo: Polling (desenvolvimento)")
    
    try:
        # Criar e iniciar bot
        bot = create_bot(bot_token)
        print("✅ Bot configurado com sucesso!")
        print("🚀 Bot iniciado! Pressione Ctrl+C para parar.")
        
        # Iniciar polling
        bot.start_polling()
        
    except KeyboardInterrupt:
        print("\n⏹️ Bot interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro ao iniciar bot: {e}")

if __name__ == '__main__':
    main()

