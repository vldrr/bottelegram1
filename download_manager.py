import os
import logging
import sqlite3
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from flask import Flask, request, jsonify, send_file, abort, render_template_string
from flask_cors import CORS
from database import DatabaseManager
from payment_processor import PaymentProcessor

logger = logging.getLogger(__name__)

class DownloadManager:
    """Gerenciador de downloads e entrega de vídeos"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
    
    def validate_download_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Valida token de download e retorna informações"""
        try:
            download_access = self.db.get_download_access(token)
            
            if not download_access:
                logger.warning(f"Token de download inválido: {token}")
                return None
            
            # Verificar expiração
            expires_at = datetime.fromisoformat(download_access['expires_at'])
            if datetime.now() > expires_at:
                logger.warning(f"Token de download expirado: {token}")
                return None
            
            # Verificar limite de downloads
            if download_access['download_count'] >= download_access['max_downloads']:
                logger.warning(f"Limite de downloads excedido: {token}")
                return None
            
            return download_access
            
        except Exception as e:
            logger.error(f"Erro na validação do token: {e}")
            return None
    
    def process_download(self, token: str, user_ip: str = None) -> Dict[str, Any]:
        """Processa download e retorna informações do arquivo"""
        try:
            # Validar token
            download_access = self.validate_download_token(token)
            if not download_access:
                return {
                    'success': False,
                    'error': 'Token inválido, expirado ou limite excedido'
                }
            
            # Verificar se arquivo existe
            file_path = download_access['file_path']
            if not os.path.exists(file_path):
                logger.error(f"Arquivo não encontrado: {file_path}")
                return {
                    'success': False,
                    'error': 'Arquivo não encontrado no servidor'
                }
            
            # Incrementar contador de downloads
            if not self.db.increment_download_count(token):
                return {
                    'success': False,
                    'error': 'Não foi possível processar o download'
                }
            
            # Log do download
            self.log_download(download_access, user_ip)
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': f"{download_access['product_name']}.mp4",
                'download_count': download_access['download_count'] + 1,
                'max_downloads': download_access['max_downloads']
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento do download: {e}")
            return {
                'success': False,
                'error': 'Erro interno do servidor'
            }
    
    def log_download(self, download_access: Dict[str, Any], user_ip: str = None):
        """Registra log do download"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'download_token': download_access['download_token'],
            'user_id': download_access['user_id'],
            'product_id': download_access['product_id'],
            'user_ip': user_ip,
            'download_count': download_access['download_count'] + 1
        }
        
        logger.info(f"Download realizado: {log_entry}")
    
    def get_download_stats(self, days: int = 30) -> Dict[str, Any]:
        """Retorna estatísticas de downloads"""
        with sqlite3.connect(self.db.db_path) as conn:
            cursor = conn.cursor()
            
            # Downloads por período
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_downloads,
                    COUNT(DISTINCT user_id) as unique_users,
                    COUNT(DISTINCT product_id) as products_downloaded
                FROM downloads 
                WHERE last_access >= datetime('now', '-{} days')
                AND download_count > 0
            '''.format(days))
            
            stats = cursor.fetchone()
            
            # Produtos mais baixados
            cursor.execute('''
                SELECT 
                    p.name,
                    SUM(d.download_count) as total_downloads
                FROM downloads d
                JOIN products p ON d.product_id = p.id
                WHERE d.last_access >= datetime('now', '-{} days')
                AND d.download_count > 0
                GROUP BY p.id, p.name
                ORDER BY total_downloads DESC
                LIMIT 5
            '''.format(days))
            
            top_downloads = cursor.fetchall()
            
            return {
                'period_days': days,
                'total_downloads': stats[0] or 0,
                'unique_users': stats[1] or 0,
                'products_downloaded': stats[2] or 0,
                'top_downloads': [
                    {
                        'product_name': row[0],
                        'download_count': row[1]
                    }
                    for row in top_downloads
                ]
            }
    
    def cleanup_expired_tokens(self):
        """Remove tokens expirados do banco de dados"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM downloads 
                    WHERE expires_at < datetime('now')
                ''')
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    logger.info(f"Removidos {deleted_count} tokens expirados")
                
                return deleted_count
                
        except Exception as e:
            logger.error(f"Erro na limpeza de tokens: {e}")
            return 0
    
    def generate_download_page(self, download_info: Dict[str, Any]) -> str:
        """Gera página HTML para download"""
        
        template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Download - {{ product_name }}</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
        }
        .success {
            color: #28a745;
            font-size: 48px;
            margin-bottom: 20px;
        }
        .product-name {
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #333;
        }
        .download-info {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 5px;
            margin: 20px 0;
            text-align: left;
        }
        .download-btn {
            background: #007bff;
            color: white;
            padding: 15px 30px;
            border: none;
            border-radius: 5px;
            font-size: 18px;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
            margin: 20px 0;
        }
        .download-btn:hover {
            background: #0056b3;
        }
        .warning {
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
        }
        .footer {
            margin-top: 30px;
            font-size: 14px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="success">✅</div>
        <h1>Download Autorizado</h1>
        <div class="product-name">{{ product_name }}</div>
        
        <div class="download-info">
            <strong>Informações do Download:</strong><br>
            • Downloads restantes: {{ remaining_downloads }}<br>
            • Válido até: {{ expires_at }}<br>
            • Tamanho do arquivo: {{ file_size }}<br>
        </div>
        
        <a href="{{ download_url }}" class="download-btn">📥 Baixar Vídeo</a>
        
        <div class="warning">
            <strong>⚠️ Importante:</strong><br>
            • Salve o arquivo em local seguro<br>
            • Este link tem uso limitado<br>
            • Não compartilhe este link
        </div>
        
        <div class="footer">
            Obrigado por sua compra! 🎬
        </div>
    </div>
</body>
</html>
        """
        
        return render_template_string(template, **download_info)

