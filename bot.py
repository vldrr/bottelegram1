import os
import logging
import secrets
from typing import Optional, List, Dict, Any
from datetime import datetime
import telebot
from telebot import types
from database import DatabaseManager
from payment_processor import PaymentProcessor

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TelegramVideoBot:
    """Bot principal para vendas de vídeos no Telegram"""
    
    def __init__(self, token: str, db_manager: DatabaseManager):
        self.bot = telebot.TeleBot(token)
        self.db = db_manager
        self.payment_processor = PaymentProcessor(db_manager, token)
        self.setup_handlers()
    
    def setup_handlers(self):
        """Configura os handlers do bot"""
        
        @self.bot.message_handler(commands=['start'])
        def handle_start(message):
            self.handle_start_command(message)
        
        @self.bot.message_handler(commands=['help'])
        def handle_help(message):
            self.handle_help_command(message)
        
        @self.bot.message_handler(commands=['catalogo', 'catalog'])
        def handle_catalog(message):
            self.handle_catalog_command(message)
        
        @self.bot.callback_query_handler(func=lambda call: True)
        def handle_callback(call):
            self.handle_callback_query(call)
        
        @self.bot.pre_checkout_query_handler(func=lambda query: True)
        def handle_pre_checkout(query):
            self.handle_pre_checkout_query(query)
        
        @self.bot.message_handler(content_types=['successful_payment'])
        def handle_successful_payment(message):
            self.handle_successful_payment_message(message)
    
    def handle_start_command(self, message):
        """Handler para comando /start"""
        user = message.from_user
        
        # Buscar ou criar usuário no banco
        db_user = self.db.get_user_by_telegram_id(user.id)
        if not db_user:
            self.db.create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            logger.info(f"Novo usuário criado: {user.id} (@{user.username})")
        
        welcome_text = f"""
🎬 **Bem-vindo ao VideoBot!**

Olá {user.first_name}! 👋

Aqui você pode comprar vídeos exclusivos de forma rápida e segura usando Telegram Stars ⭐

**Comandos disponíveis:**
• /catalogo - Ver todos os vídeos disponíveis
• /help - Ajuda e suporte

**Como funciona:**
1. Navegue pelo catálogo
2. Escolha o vídeo desejado
3. Pague com Telegram Stars
4. Receba o link de download instantaneamente

Pronto para começar? Use /catalogo para ver nossos vídeos! 🚀
        """
        
        self.bot.send_message(
            message.chat.id, 
            welcome_text, 
            parse_mode='Markdown'
        )
    
    def handle_help_command(self, message):
        """Handler para comando /help"""
        help_text = """
🆘 **Central de Ajuda**

**Comandos:**
• `/start` - Iniciar o bot
• `/catalogo` - Ver vídeos disponíveis
• `/help` - Esta mensagem de ajuda

**Como comprar:**
1. Use `/catalogo` para ver os vídeos
2. Clique em "Comprar" no vídeo desejado
3. Pague com Telegram Stars ⭐
4. Receba o link de download

**Sobre os pagamentos:**
• Pagamentos são processados pelo Telegram
• Usamos Telegram Stars como moeda
• Transações são seguras e instantâneas

**Sobre os downloads:**
• Links válidos por 24 horas
• Máximo de 3 downloads por compra
• Vídeos em alta qualidade

**Suporte:**
Se tiver problemas, entre em contato conosco!
        """
        
        self.bot.send_message(
            message.chat.id,
            help_text,
            parse_mode='Markdown'
        )
    
    def handle_catalog_command(self, message):
        """Handler para comando /catalogo"""
        products = self.db.get_active_products()
        
        if not products:
            self.bot.send_message(
                message.chat.id,
                "📭 Ainda não temos vídeos disponíveis. Volte em breve!"
            )
            return
        
        self.bot.send_message(
            message.chat.id,
            f"🎬 **Catálogo de Vídeos** ({len(products)} disponíveis)\n\nEscolha um vídeo abaixo:",
            parse_mode='Markdown'
        )
        
        for product in products:
            self.send_product_card(message.chat.id, product)
    
    def send_product_card(self, chat_id: int, product: Dict[str, Any]):
        """Envia card do produto com botão de compra"""
        
        # Formatação do preço
        price_text = f"{product['price_stars']} ⭐"
        
        # Formatação da duração se disponível
        duration_text = ""
        if product.get('duration_seconds'):
            minutes = product['duration_seconds'] // 60
            seconds = product['duration_seconds'] % 60
            duration_text = f"\n⏱️ Duração: {minutes}:{seconds:02d}"
        
        # Formatação do tamanho se disponível
        size_text = ""
        if product.get('file_size'):
            size_mb = product['file_size'] / (1024 * 1024)
            size_text = f"\n📁 Tamanho: {size_mb:.1f} MB"
        
        product_text = f"""
🎬 **{product['name']}**

{product['description'] or 'Vídeo exclusivo de alta qualidade'}{duration_text}{size_text}

💰 Preço: {price_text}
        """
        
        # Keyboard com botão de compra
        keyboard = types.InlineKeyboardMarkup()
        buy_button = types.InlineKeyboardButton(
            f"💳 Comprar por {price_text}",
            callback_data=f"buy_{product['id']}"
        )
        keyboard.add(buy_button)
        
        # Enviar thumbnail se disponível
        if product.get('thumbnail_path') and os.path.exists(product['thumbnail_path']):
            with open(product['thumbnail_path'], 'rb') as photo:
                self.bot.send_photo(
                    chat_id,
                    photo,
                    caption=product_text,
                    parse_mode='Markdown',
                    reply_markup=keyboard
                )
        else:
            self.bot.send_message(
                chat_id,
                product_text,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
    
    def handle_callback_query(self, call):
        """Handler para callback queries (botões inline)"""
        try:
            if call.data.startswith('buy_'):
                product_id = int(call.data.split('_')[1])
                self.process_purchase_request(call, product_id)
            
            # Responder ao callback para remover loading
            self.bot.answer_callback_query(call.id)
            
        except Exception as e:
            logger.error(f"Erro no callback query: {e}")
            self.bot.answer_callback_query(call.id, "Erro interno. Tente novamente.")
    
    def process_purchase_request(self, call, product_id: int):
        """Processa solicitação de compra"""
        user = call.from_user
        product = self.db.get_product_by_id(product_id)
        
        if not product:
            self.bot.answer_callback_query(call.id, "Produto não encontrado!")
            return
        
        # Buscar ou criar usuário
        db_user = self.db.get_user_by_telegram_id(user.id)
        if not db_user:
            user_id = self.db.create_user(
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        else:
            user_id = db_user['id']
        
        # Criar transação
        transaction_id = self.db.create_transaction(
            user_id=user_id,
            product_id=product_id,
            amount_stars=product['price_stars']
        )
        
        # Criar fatura
        self.send_invoice(call.message.chat.id, product, transaction_id)
    
    def send_invoice(self, chat_id: int, product: Dict[str, Any], transaction_id: int):
        """Envia fatura para pagamento"""
        
        # Preços em formato da API (centavos de stars)
        prices = [types.LabeledPrice(
            label=product['name'],
            amount=product['price_stars']
        )]
        
        self.bot.send_invoice(
            chat_id=chat_id,
            title=product['name'],
            description=product['description'] or 'Vídeo exclusivo de alta qualidade',
            invoice_payload=str(transaction_id),  # ID da transação como payload
            provider_token="",  # Vazio para produtos digitais
            currency="XTR",  # Telegram Stars
            prices=prices,
            start_parameter=f"buy_{product['id']}",
            photo_url=None,  # Pode adicionar URL da thumbnail aqui
            photo_size=None,
            photo_width=None,
            photo_height=None,
            need_name=False,
            need_phone_number=False,
            need_email=False,
            need_shipping_address=False,
            send_phone_number_to_provider=False,
            send_email_to_provider=False,
            is_flexible=False
        )
    
    def handle_pre_checkout_query(self, query):
        """Handler para validação de pré-checkout"""
        try:
            # Usar o processador de pagamentos para validação
            result = self.payment_processor.process_pre_checkout({
                'id': query.id,
                'from': query.from_user.to_dict(),
                'currency': query.currency,
                'total_amount': query.total_amount,
                'invoice_payload': query.invoice_payload,
                'shipping_option_id': query.shipping_option_id,
                'order_info': query.order_info.to_dict() if query.order_info else None
            })
            
            # Responder ao Telegram
            self.bot.answer_pre_checkout_query(
                query.id,
                ok=result['ok'],
                error_message=result.get('error_message')
            )
            
            if result['ok']:
                logger.info(f"Pré-checkout aprovado para transação {query.invoice_payload}")
            else:
                logger.warning(f"Pré-checkout rejeitado: {result.get('error_message')}")
            
        except Exception as e:
            logger.error(f"Erro no pré-checkout: {e}")
            self.bot.answer_pre_checkout_query(
                query.id,
                ok=False,
                error_message="Erro interno. Tente novamente."
            )
    
    def handle_successful_payment_message(self, message):
        """Handler para pagamento bem-sucedido"""
        try:
            payment = message.successful_payment
            user = message.from_user
            
            # Preparar dados do pagamento
            payment_data = {
                'telegram_payment_charge_id': payment.telegram_payment_charge_id,
                'provider_payment_charge_id': payment.provider_payment_charge_id,
                'invoice_payload': payment.invoice_payload,
                'total_amount': payment.total_amount,
                'currency': payment.currency,
                'shipping_option_id': payment.shipping_option_id,
                'order_info': payment.order_info.to_dict() if payment.order_info else None
            }
            
            # Processar pagamento
            download_info = self.payment_processor.process_successful_payment(
                payment_data, 
                user.id
            )
            
            # Enviar confirmação com link de download
            self.send_download_confirmation(message.chat.id, download_info)
            
            logger.info(f"Pagamento processado com sucesso: {payment.telegram_payment_charge_id}")
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {e}")
            self.bot.send_message(
                message.chat.id,
                "❌ Erro ao processar pagamento. Entre em contato com o suporte.\n\n"
                f"ID do pagamento: `{payment.telegram_payment_charge_id if 'payment' in locals() else 'N/A'}`",
                parse_mode='Markdown'
            )
    
    def send_download_confirmation(self, chat_id: int, download_info: Dict[str, Any]):
        """Envia confirmação de pagamento com link de download"""
        
        # Formatação da data de expiração
        from datetime import datetime
        expires_at = datetime.fromisoformat(download_info['expires_at'].replace('Z', '+00:00'))
        expires_formatted = expires_at.strftime('%d/%m/%Y às %H:%M')
        
        success_message = f"""
✅ **Pagamento confirmado!**

Obrigado pela compra de: **{download_info['product_name']}**

🔗 **Link de download:**
{download_info['download_url']}

⚠️ **Informações importantes:**
• Link válido até: {expires_formatted}
• Máximo de downloads: {download_info['max_downloads']}
• Downloads utilizados: {download_info.get('download_count', 0)}

💡 **Dica:** Salve o arquivo em local seguro após o download!

Aproveite seu vídeo! 🎬
        """
        
        # Keyboard com botão para o link
        keyboard = types.InlineKeyboardMarkup()
        download_button = types.InlineKeyboardButton(
            "📥 Baixar Vídeo",
            url=download_info['download_url']
        )
        keyboard.add(download_button)
        
        self.bot.send_message(
            chat_id,
            success_message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    
    def start_polling(self):
        """Inicia o bot em modo polling"""
        logger.info("Bot iniciado em modo polling")
        self.bot.infinity_polling()
    
    def set_webhook(self, webhook_url: str):
        """Configura webhook para o bot"""
        self.bot.set_webhook(webhook_url)
        logger.info(f"Webhook configurado: {webhook_url}")


# Função para inicializar o bot
def create_bot(token: str, db_path: str = "bot_database.db") -> TelegramVideoBot:
    """Cria e configura o bot"""
    db_manager = DatabaseManager(db_path)
    return TelegramVideoBot(token, db_manager)

