import os
import sqlite3
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class ProductManager:
    """Gerenciador de produtos (vídeos)"""
    
    def __init__(self, db_manager):
        self.db = db_manager
    
    def create_product(self, name: str, description: str, price_stars: int, 
                      file_path: str, thumbnail_path: str = None, 
                      duration_seconds: int = None) -> int:
        """Cria um novo produto"""
        try:
            # Verificar se arquivo existe
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
            
            # Obter tamanho do arquivo
            file_size = os.path.getsize(file_path)
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO products (name, description, price_stars, file_path, 
                                        thumbnail_path, file_size, duration_seconds)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (name, description, price_stars, file_path, thumbnail_path, 
                      file_size, duration_seconds))
                conn.commit()
                product_id = cursor.lastrowid
                
                logger.info(f"Produto criado: ID {product_id}, Nome: {name}")
                return product_id
                
        except Exception as e:
            logger.error(f"Erro ao criar produto: {e}")
            raise
    
    def update_product(self, product_id: int, **kwargs) -> bool:
        """Atualiza um produto existente"""
        try:
            # Campos permitidos para atualização
            allowed_fields = [
                'name', 'description', 'price_stars', 'file_path', 
                'thumbnail_path', 'duration_seconds', 'is_active'
            ]
            
            # Filtrar campos válidos
            update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}
            
            if not update_fields:
                return False
            
            # Construir query de atualização
            set_clause = ', '.join([f"{field} = ?" for field in update_fields.keys()])
            values = list(update_fields.values()) + [product_id]
            
            with sqlite3.connect(self.db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(f'''
                    UPDATE products 
                    SET {set_clause}
                    WHERE id = ?
                ''', values)
                conn.commit()
                
                success = cursor.rowcount > 0
                if success:
                    logger.info(f"Produto {product_id} atualizado: {update_fields}")
                
                return success
                
        except Exception as e:
            logger.error(f"Erro ao atualizar produto {product_id}: {e}")
            return False
    
    def delete_product(self, product_id: int) -> bool:
        """Remove um produto (marca como inativo)"""
        return self.update_product(product_id, is_active=False)
    
    def get_product_stats(self, product_id: int) -> Dict[str, Any]:
        """Retorna estatísticas de um produto"""
        try:
            with sqlite3.connect(self.db.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Informações básicas do produto
                cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
                product = cursor.fetchone()
                
                if not product:
                    return None
                
                # Estatísticas de vendas
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_sales,
                        SUM(amount_stars) as total_revenue,
                        AVG(amount_stars) as avg_price
                    FROM transactions 
                    WHERE product_id = ? AND status = 'completed'
                ''', (product_id,))
                
                sales_stats = cursor.fetchone()
                
                # Estatísticas de downloads
                cursor.execute('''
                    SELECT 
                        COUNT(*) as total_downloads,
                        AVG(download_count) as avg_downloads_per_purchase
                    FROM downloads 
                    WHERE product_id = ? AND download_count > 0
                ''', (product_id,))
                
                download_stats = cursor.fetchone()
                
                return {
                    'product': dict(product),
                    'sales': {
                        'total_sales': sales_stats['total_sales'] or 0,
                        'total_revenue': sales_stats['total_revenue'] or 0,
                        'average_price': sales_stats['avg_price'] or 0
                    },
                    'downloads': {
                        'total_downloads': download_stats['total_downloads'] or 0,
                        'avg_downloads_per_purchase': download_stats['avg_downloads_per_purchase'] or 0
                    }
                }
                
        except Exception as e:
            logger.error(f"Erro ao buscar estatísticas do produto {product_id}: {e}")
            return None
    
    def upload_video(self, file_data, filename: str, upload_dir: str = None) -> str:
        """Faz upload de um vídeo"""
        try:
            if upload_dir is None:
                upload_dir = os.getenv('STORAGE_PATH', '/home/ubuntu/telegram_video_bot/videos')
            
            # Criar diretório se não existir
            os.makedirs(upload_dir, exist_ok=True)
            
            # Gerar nome único para o arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name, ext = os.path.splitext(filename)
            unique_filename = f"{timestamp}_{name}{ext}"
            
            file_path = os.path.join(upload_dir, unique_filename)
            
            # Salvar arquivo
            with open(file_path, 'wb') as f:
                f.write(file_data)
            
            logger.info(f"Vídeo salvo: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Erro no upload do vídeo: {e}")
            raise
    
    def generate_thumbnail(self, video_path: str, thumbnail_dir: str = None) -> Optional[str]:
        """Gera thumbnail de um vídeo (requer ffmpeg)"""
        try:
            if thumbnail_dir is None:
                thumbnail_dir = os.path.join(
                    os.path.dirname(video_path), 
                    'thumbnails'
                )
            
            os.makedirs(thumbnail_dir, exist_ok=True)
            
            # Nome do thumbnail
            video_name = os.path.splitext(os.path.basename(video_path))[0]
            thumbnail_path = os.path.join(thumbnail_dir, f"{video_name}_thumb.jpg")
            
            # Comando ffmpeg para gerar thumbnail
            import subprocess
            cmd = [
                'ffmpeg', '-i', video_path, 
                '-ss', '00:00:01', '-vframes', '1', 
                '-y', thumbnail_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(thumbnail_path):
                logger.info(f"Thumbnail gerado: {thumbnail_path}")
                return thumbnail_path
            else:
                logger.warning(f"Falha ao gerar thumbnail: {result.stderr}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao gerar thumbnail: {e}")
            return None
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """Obtém informações de um vídeo (requer ffprobe)"""
        try:
            import subprocess
            import json
            
            cmd = [
                'ffprobe', '-v', 'quiet', '-print_format', 'json',
                '-show_format', '-show_streams', video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                
                # Extrair informações relevantes
                format_info = data.get('format', {})
                video_stream = next(
                    (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
                    {}
                )
                
                return {
                    'duration': float(format_info.get('duration', 0)),
                    'size': int(format_info.get('size', 0)),
                    'bitrate': int(format_info.get('bit_rate', 0)),
                    'width': video_stream.get('width'),
                    'height': video_stream.get('height'),
                    'codec': video_stream.get('codec_name'),
                    'fps': eval(video_stream.get('r_frame_rate', '0/1'))
                }
            else:
                logger.warning(f"Falha ao obter info do vídeo: {result.stderr}")
                return {}
                
        except Exception as e:
            logger.error(f"Erro ao obter informações do vídeo: {e}")
            return {}

