import os
import logging
import hashlib
import hmac
import secrets
import mimetypes
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from urllib.parse import quote
from flask import Flask, request, jsonify, send_file, abort, Response, render_template_string

logger = logging.getLogger(__name__)

class SecureDeliverySystem:
    """Sistema seguro de entrega de vídeos"""
    
    def __init__(self, db_manager, secret_key: str):
        self.db = db_manager
        self.secret_key = secret_key
    
    def generate_signed_url(self, file_path: str, token: str, expires_in: int = 3600) -> str:
        """Gera URL assinada para download seguro"""
        try:
            # Timestamp de expiração
            expires_at = int((datetime.now() + timedelta(seconds=expires_in)).timestamp())
            
            # Dados para assinatura
            data = f"{token}:{expires_at}:{file_path}"
            
            # Gerar assinatura HMAC
            signature = hmac.new(
                self.secret_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # URL assinada
            base_url = os.getenv('WEBHOOK_URL', 'http://localhost:5000')
            signed_url = f"{base_url}/secure-download/{token}?expires={expires_at}&signature={signature}"
            
            return signed_url
            
        except Exception as e:
            logger.error(f"Erro ao gerar URL assinada: {e}")
            raise
    
    def validate_signed_url(self, token: str, expires_at: int, signature: str, file_path: str) -> bool:
        """Valida URL assinada"""
        try:
            # Verificar expiração
            if datetime.now().timestamp() > expires_at:
                logger.warning(f"URL expirada: {token}")
                return False
            
            # Reconstruir dados para verificação
            data = f"{token}:{expires_at}:{file_path}"
            
            # Calcular assinatura esperada
            expected_signature = hmac.new(
                self.secret_key.encode(),
                data.encode(),
                hashlib.sha256
            ).hexdigest()
            
            # Comparação segura
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Erro na validação da URL: {e}")
            return False
    
    def create_streaming_response(self, file_path: str, filename: str) -> Response:
        """Cria resposta de streaming para download"""
        try:
            if not os.path.exists(file_path):
                abort(404, description="Arquivo não encontrado")
            
            # Obter informações do arquivo
            file_size = os.path.getsize(file_path)
            mime_type = mimetypes.guess_type(file_path)[0] or 'application/octet-stream'
            
            # Headers para download
            headers = {
                'Content-Type': mime_type,
                'Content-Length': str(file_size),
                'Content-Disposition': f'attachment; filename="{quote(filename)}"',
                'Accept-Ranges': 'bytes',
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0'
            }
            
            # Suporte a range requests (para downloads resumíveis)
            range_header = request.headers.get('Range')
            if range_header:
                return self.handle_range_request(file_path, range_header, headers)
            
            # Download completo
            def generate():
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(8192)  # 8KB chunks
                        if not chunk:
                            break
                        yield chunk
            
            return Response(generate(), headers=headers)
            
        except Exception as e:
            logger.error(f"Erro na criação da resposta de streaming: {e}")
            abort(500, description="Erro interno do servidor")
    
    def handle_range_request(self, file_path: str, range_header: str, base_headers: Dict[str, str]) -> Response:
        """Manipula requisições de range (downloads resumíveis)"""
        try:
            file_size = os.path.getsize(file_path)
            
            # Parse do header Range
            range_match = range_header.replace('bytes=', '').split('-')
            start = int(range_match[0]) if range_match[0] else 0
            end = int(range_match[1]) if range_match[1] else file_size - 1
            
            # Validar range
            if start >= file_size or end >= file_size or start > end:
                abort(416, description="Range inválido")
            
            content_length = end - start + 1
            
            # Headers para resposta parcial
            headers = base_headers.copy()
            headers.update({
                'Content-Length': str(content_length),
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes'
            })
            
            # Gerar conteúdo parcial
            def generate():
                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = content_length
                    while remaining > 0:
                        chunk_size = min(8192, remaining)
                        chunk = f.read(chunk_size)
                        if not chunk:
                            break
                        remaining -= len(chunk)
                        yield chunk
            
            return Response(generate(), status=206, headers=headers)
            
        except Exception as e:
            logger.error(f"Erro no range request: {e}")
            abort(500, description="Erro interno do servidor")
    
    def add_watermark_info(self, download_access: Dict[str, Any]) -> Dict[str, str]:
        """Adiciona informações de marca d'água (metadados)"""
        try:
            watermark_info = {
                'buyer_id': str(download_access['user_id']),
                'purchase_date': datetime.now().isoformat(),
                'download_token': download_access['download_token'],
                'product_id': str(download_access['product_id'])
            }
            
            # Hash das informações para verificação
            info_string = '|'.join(watermark_info.values())
            watermark_info['verification_hash'] = hashlib.sha256(
                (info_string + self.secret_key).encode()
            ).hexdigest()[:16]
            
            return watermark_info
            
        except Exception as e:
            logger.error(f"Erro ao gerar marca d'água: {e}")
            return {}
    
    def log_download_attempt(self, token: str, user_ip: str, user_agent: str, success: bool, reason: str = None):
        """Registra tentativa de download para auditoria"""
        try:
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'token': token,
                'user_ip': user_ip,
                'user_agent': user_agent,
                'success': success,
                'reason': reason or 'N/A'
            }
            
            # Log estruturado
            logger.info(f"Download attempt: {log_entry}")
            
            # Aqui você pode salvar em arquivo ou banco separado para auditoria
            
        except Exception as e:
            logger.error(f"Erro no log de download: {e}")


class DeliveryScheduler:
    """Agendador para tarefas de entrega"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def cleanup_expired_downloads(self) -> int:
        """Remove downloads expirados"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Contar downloads expirados
                cursor.execute('''
                    SELECT COUNT(*) FROM downloads 
                    WHERE expires_at < datetime('now')
                ''')
                expired_count = cursor.fetchone()[0]
                
                # Remover downloads expirados
                cursor.execute('''
                    DELETE FROM downloads 
                    WHERE expires_at < datetime('now')
                ''')
                conn.commit()
                
                if expired_count > 0:
                    logger.info(f"Removidos {expired_count} downloads expirados")
                
                return expired_count
                
        except Exception as e:
            logger.error(f"Erro na limpeza de downloads: {e}")
            return 0
    
    def send_expiry_warnings(self) -> int:
        """Envia avisos de expiração próxima"""
        try:
            import sqlite3
            
            # Buscar downloads que expiram em 2 horas
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT d.*, u.telegram_id, p.name as product_name
                    FROM downloads d
                    JOIN users u ON d.user_id = u.id
                    JOIN products p ON d.product_id = p.id
                    WHERE d.expires_at BETWEEN datetime('now', '+1 hour') 
                                           AND datetime('now', '+3 hours')
                    AND d.download_count < d.max_downloads
                ''')
                
                expiring_downloads = cursor.fetchall()
                
                # Aqui você enviaria mensagens via bot
                # Por enquanto, apenas log
                for download in expiring_downloads:
                    logger.info(f"Download expirando: {download['download_token']} para usuário {download['telegram_id']}")
                
                return len(expiring_downloads)
                
        except Exception as e:
            logger.error(f"Erro no envio de avisos: {e}")
            return 0
    
    def generate_delivery_report(self, days: int = 7) -> Dict[str, Any]:
        """Gera relatório de entregas"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Estatísticas gerais
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_deliveries,
                        COUNT(DISTINCT user_id) as unique_users,
                        SUM(download_count) as total_downloads,
                        AVG(download_count) as avg_downloads_per_delivery
                    FROM downloads 
                    WHERE created_at >= datetime('now', '-{} days')
                '''.format(days))
                
                stats = cursor.fetchone()
                
                # Downloads por produto
                cursor.execute('''
                    SELECT 
                        p.name,
                        COUNT(*) as deliveries,
                        SUM(d.download_count) as total_downloads
                    FROM downloads d
                    JOIN products p ON d.product_id = p.id
                    WHERE d.created_at >= datetime('now', '-{} days')
                    GROUP BY p.id, p.name
                    ORDER BY deliveries DESC
                '''.format(days))
                
                product_stats = cursor.fetchall()
                
                # Taxa de utilização
                cursor.execute('''
                    SELECT 
                        COUNT(CASE WHEN download_count > 0 THEN 1 END) as used_deliveries,
                        COUNT(*) as total_deliveries
                    FROM downloads 
                    WHERE created_at >= datetime('now', '-{} days')
                '''.format(days))
                
                usage = cursor.fetchone()
                usage_rate = (usage['used_deliveries'] / usage['total_deliveries'] * 100) if usage['total_deliveries'] > 0 else 0
                
                return {
                    'period_days': days,
                    'summary': {
                        'total_deliveries': stats['total_deliveries'] or 0,
                        'unique_users': stats['unique_users'] or 0,
                        'total_downloads': stats['total_downloads'] or 0,
                        'avg_downloads_per_delivery': round(stats['avg_downloads_per_delivery'] or 0, 2),
                        'usage_rate': round(usage_rate, 2)
                    },
                    'products': [
                        {
                            'name': row['name'],
                            'deliveries': row['deliveries'],
                            'downloads': row['total_downloads']
                        }
                        for row in product_stats
                    ]
                }
                
        except Exception as e:
            logger.error(f"Erro na geração do relatório: {e}")
            return {}


class AntiPiracySystem:
    """Sistema básico anti-pirataria"""
    
    def __init__(self, db_manager):
        self.db = db_manager
        self.suspicious_patterns = []
    
    def detect_suspicious_activity(self, user_id: int, ip_address: str) -> Dict[str, Any]:
        """Detecta atividade suspeita"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                
                # Verificar múltiplos downloads do mesmo IP
                cursor.execute('''
                    SELECT COUNT(DISTINCT user_id) as unique_users
                    FROM downloads d
                    JOIN users u ON d.user_id = u.id
                    WHERE d.last_access >= datetime('now', '-1 day')
                    -- Aqui você adicionaria filtro por IP se armazenasse
                ''')
                
                # Por enquanto, análise básica
                warnings = []
                
                # Verificar downloads excessivos
                cursor.execute('''
                    SELECT SUM(download_count) as total_downloads
                    FROM downloads 
                    WHERE user_id = ? AND last_access >= datetime('now', '-1 day')
                ''', (user_id,))
                
                result = cursor.fetchone()
                daily_downloads = result[0] or 0
                
                if daily_downloads > 10:  # Limite arbitrário
                    warnings.append("Downloads excessivos detectados")
                
                return {
                    'user_id': user_id,
                    'risk_level': 'high' if warnings else 'low',
                    'warnings': warnings,
                    'daily_downloads': daily_downloads
                }
                
        except Exception as e:
            logger.error(f"Erro na detecção de atividade suspeita: {e}")
            return {'risk_level': 'unknown', 'warnings': []}
    
    def block_suspicious_token(self, token: str, reason: str):
        """Bloqueia token suspeito"""
        try:
            import sqlite3
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE downloads 
                    SET max_downloads = 0
                    WHERE download_token = ?
                ''', (token,))
                conn.commit()
                
                logger.warning(f"Token bloqueado: {token}, Razão: {reason}")
                
        except Exception as e:
            logger.error(f"Erro ao bloquear token: {e}")

