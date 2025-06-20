import os
import logging
import hashlib
import hmac
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from database import DatabaseManager

logger = logging.getLogger(__name__)

class PaymentProcessor:
    """Processador de pagamentos para Telegram Stars"""
    
    def __init__(self, db_manager: DatabaseManager, bot_token: str):
        self.db = db_manager
        self.bot_token = bot_token
    
    def validate_payment_data(self, payment_data: Dict[str, Any]) -> bool:
        """Valida dados de pagamento recebidos do Telegram"""
        try:
            required_fields = [
                'telegram_payment_charge_id',
                'provider_payment_charge_id',
                'invoice_payload',
                'total_amount',
                'currency'
            ]
            
            for field in required_fields:
                if field not in payment_data:
                    logger.error(f"Campo obrigatório ausente: {field}")
                    return False
            
            # Validar moeda (deve ser XTR para produtos digitais)
            if payment_data['currency'] != 'XTR':
                logger.error(f"Moeda inválida: {payment_data['currency']}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro na validação de pagamento: {e}")
            return False
    
    def process_pre_checkout(self, query_data: Dict[str, Any]) -> Dict[str, Any]:
        """Processa query de pré-checkout"""
        try:
            transaction_id = int(query_data.get('invoice_payload', 0))
            
            # Buscar transação no banco
            transaction = self.get_transaction_by_id(transaction_id)
            if not transaction:
                return {
                    'ok': False,
                    'error_message': 'Transação não encontrada'
                }
            
            # Verificar se transação já foi processada
            if transaction['status'] != 'pending':
                return {
                    'ok': False,
                    'error_message': 'Transação já processada'
                }
            
            # Buscar produto
            product = self.db.get_product_by_id(transaction['product_id'])
            if not product or not product['is_active']:
                return {
                    'ok': False,
                    'error_message': 'Produto não disponível'
                }
            
            # Validar valor
            if query_data.get('total_amount') != product['price_stars']:
                return {
                    'ok': False,
                    'error_message': 'Valor incorreto'
                }
            
            # Validações adicionais podem ser adicionadas aqui
            # Por exemplo: verificar estoque, limites de compra, etc.
            
            return {'ok': True}
            
        except Exception as e:
            logger.error(f"Erro no pré-checkout: {e}")
            return {
                'ok': False,
                'error_message': 'Erro interno do servidor'
            }
    
    def process_successful_payment(self, payment_data: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """Processa pagamento bem-sucedido"""
        try:
            # Validar dados do pagamento
            if not self.validate_payment_data(payment_data):
                raise ValueError("Dados de pagamento inválidos")
            
            transaction_id = int(payment_data['invoice_payload'])
            
            # Buscar transação
            transaction = self.get_transaction_by_id(transaction_id)
            if not transaction:
                raise ValueError("Transação não encontrada")
            
            # Verificar se já foi processada
            if transaction['status'] == 'completed':
                logger.warning(f"Transação {transaction_id} já foi processada")
                return self.get_existing_download_info(transaction_id)
            
            # Atualizar transação
            self.db.update_transaction_payment(
                transaction_id=transaction_id,
                telegram_payment_id=payment_data['telegram_payment_charge_id'],
                status='completed'
            )
            
            # Gerar acesso de download
            download_info = self.create_download_access(transaction)
            
            # Log da transação
            self.log_transaction(transaction_id, payment_data, 'completed')
            
            return download_info
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento: {e}")
            # Marcar transação como erro
            if 'transaction_id' in locals():
                self.db.update_transaction_payment(
                    transaction_id=transaction_id,
                    telegram_payment_id=payment_data.get('telegram_payment_charge_id', ''),
                    status='error'
                )
            raise
    
    def create_download_access(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Cria acesso de download para uma transação"""
        import secrets
        
        # Gerar token único
        download_token = secrets.token_urlsafe(32)
        
        # Configurações padrão
        expiry_hours = int(os.getenv('DOWNLOAD_EXPIRY_HOURS', 24))
        max_downloads = int(os.getenv('MAX_DOWNLOADS_PER_PURCHASE', 3))
        
        # Criar registro de download
        download_id = self.db.create_download_access(
            transaction_id=transaction['id'],
            user_id=transaction['user_id'],
            product_id=transaction['product_id'],
            download_token=download_token,
            expiry_hours=expiry_hours,
            max_downloads=max_downloads
        )
        
        # Buscar informações do produto
        product = self.db.get_product_by_id(transaction['product_id'])
        
        # Gerar URL de download
        base_url = os.getenv('WEBHOOK_URL', 'http://localhost:5000')
        download_url = f"{base_url}/download/{download_token}"
        
        return {
            'download_id': download_id,
            'download_token': download_token,
            'download_url': download_url,
            'product_name': product['name'],
            'expires_at': (datetime.now() + timedelta(hours=expiry_hours)).isoformat(),
            'max_downloads': max_downloads
        }
    
    def get_existing_download_info(self, transaction_id: int) -> Dict[str, Any]:
        """Busca informações de download existentes para uma transação"""
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT d.*, p.name as product_name
                FROM downloads d
                JOIN products p ON d.product_id = p.id
                WHERE d.transaction_id = ?
            ''', (transaction_id,))
            row = cursor.fetchone()
            
            if row:
                download = dict(row)
                base_url = os.getenv('WEBHOOK_URL', 'http://localhost:5000')
                download_url = f"{base_url}/download/{download['download_token']}"
                
                return {
                    'download_id': download['id'],
                    'download_token': download['download_token'],
                    'download_url': download_url,
                    'product_name': download['product_name'],
                    'expires_at': download['expires_at'],
                    'max_downloads': download['max_downloads'],
                    'download_count': download['download_count']
                }
        
        return None
    
    def get_transaction_by_id(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Busca transação por ID"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM transactions WHERE id = ?", (transaction_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def log_transaction(self, transaction_id: int, payment_data: Dict[str, Any], status: str):
        """Registra log da transação"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'transaction_id': transaction_id,
            'telegram_payment_id': payment_data.get('telegram_payment_charge_id'),
            'amount': payment_data.get('total_amount'),
            'currency': payment_data.get('currency'),
            'status': status
        }
        
        logger.info(f"Transação processada: {json.dumps(log_entry)}")
    
    def refund_payment(self, telegram_payment_id: str) -> bool:
        """Processa reembolso (funcionalidade futura)"""
        # Implementar lógica de reembolso quando necessário
        # Por enquanto, apenas log
        logger.info(f"Solicitação de reembolso para pagamento: {telegram_payment_id}")
        return False
    
    def get_payment_statistics(self, days: int = 30) -> Dict[str, Any]:
        """Retorna estatísticas de pagamento"""
        import sqlite3
        
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Total de vendas nos últimos X dias
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_sales,
                    SUM(amount_stars) as total_revenue,
                    AVG(amount_stars) as avg_sale_value
                FROM transactions 
                WHERE status = 'completed' 
                AND created_at >= datetime('now', '-{} days')
            '''.format(days))
            
            stats = cursor.fetchone()
            
            # Produtos mais vendidos
            cursor.execute('''
                SELECT 
                    p.name,
                    COUNT(*) as sales_count,
                    SUM(t.amount_stars) as revenue
                FROM transactions t
                JOIN products p ON t.product_id = p.id
                WHERE t.status = 'completed'
                AND t.created_at >= datetime('now', '-{} days')
                GROUP BY p.id, p.name
                ORDER BY sales_count DESC
                LIMIT 5
            '''.format(days))
            
            top_products = cursor.fetchall()
            
            return {
                'period_days': days,
                'total_sales': stats[0] or 0,
                'total_revenue': stats[1] or 0,
                'average_sale_value': stats[2] or 0,
                'top_products': [
                    {
                        'name': row[0],
                        'sales_count': row[1],
                        'revenue': row[2]
                    }
                    for row in top_products
                ]
            }

