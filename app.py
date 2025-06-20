import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify, send_file, abort, Response, render_template
from flask_cors import CORS
from dotenv import load_dotenv
import telebot
from bot import create_bot
from database import DatabaseManager
from download_manager import DownloadManager
from delivery_system import SecureDeliverySystem, DeliveryScheduler

# Carregar variáveis de ambiente
load_dotenv()

# Configuração de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Criar aplicação Flask
app = Flask(__name__)
CORS(app)  # Permitir CORS para todas as rotas

# Configurações
BOT_TOKEN = os.getenv('BOT_TOKEN', 'SEU_TOKEN_AQUI')
WEBHOOK_URL = os.getenv('WEBHOOK_URL', '')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key')

app.config['SECRET_KEY'] = SECRET_KEY

# Inicializar bot e banco de dados
db_manager = DatabaseManager()
download_manager = DownloadManager(db_manager)
delivery_system = SecureDeliverySystem(db_manager, SECRET_KEY)
delivery_scheduler = DeliveryScheduler(db_manager)
telegram_bot = create_bot(BOT_TOKEN)

@app.route('/')
def index():
    """Página inicial da API"""
    return jsonify({
        'status': 'online',
        'service': 'Telegram Video Bot API',
        'version': '1.0.0'
    })

@app.route('/webhook', methods=['POST'])
def webhook():
    """Endpoint para receber updates do Telegram via webhook"""
    try:
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            telegram_bot.bot.process_new_updates([update])
            return jsonify({'status': 'ok'})
        else:
            abort(403)
    except Exception as e:
        logger.error(f"Erro no webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/download/<token>')
def download_video(token):
    """Endpoint para download de vídeos com token"""
    try:
        # Obter informações do usuário
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        user_agent = request.headers.get('User-Agent', 'Unknown')
        
        # Processar download
        result = download_manager.process_download(token, user_ip)
        
        if not result['success']:
            delivery_system.log_download_attempt(token, user_ip, user_agent, False, result['error'])
            abort(404, description=result['error'])
        
        # Log de sucesso
        delivery_system.log_download_attempt(token, user_ip, user_agent, True)
        
        # Criar resposta de streaming segura
        return delivery_system.create_streaming_response(
            result['file_path'],
            result['filename']
        )
        
    except Exception as e:
        logger.error(f"Erro no download: {e}")
        abort(500, description="Erro interno do servidor")

@app.route('/secure-download/<token>')
def secure_download_video(token):
    """Endpoint para download seguro com URL assinada"""
    try:
        # Obter parâmetros da URL assinada
        expires_at = int(request.args.get('expires', 0))
        signature = request.args.get('signature', '')
        
        # Obter informações do download
        download_access = db_manager.get_download_access(token)
        if not download_access:
            abort(404, description="Token inválido")
        
        # Validar URL assinada
        if not delivery_system.validate_signed_url(token, expires_at, signature, download_access['file_path']):
            abort(403, description="URL inválida ou expirada")
        
        # Processar download normalmente
        user_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
        result = download_manager.process_download(token, user_ip)
        
        if not result['success']:
            abort(404, description=result['error'])
        
        # Retornar arquivo com streaming seguro
        return delivery_system.create_streaming_response(
            result['file_path'],
            result['filename']
        )
        
    except Exception as e:
        logger.error(f"Erro no download seguro: {e}")
        abort(500, description="Erro interno do servidor")

@app.route('/api/products', methods=['GET'])
def get_products():
    """API para listar produtos"""
    try:
        products = db_manager.get_active_products()
        return jsonify({
            'status': 'success',
            'products': products
        })
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/products', methods=['POST'])
def create_product():
    """API para criar novo produto"""
    try:
        data = request.get_json()
        
        # Validação básica
        required_fields = ['name', 'price_stars', 'file_path']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Campo obrigatório: {field}'}), 400
        
        # Aqui você implementaria a criação do produto
        # Por enquanto, retorna sucesso
        return jsonify({
            'status': 'success',
            'message': 'Produto criado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar produto: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API para estatísticas básicas"""
    try:
        # Implementar estatísticas básicas
        return jsonify({
            'status': 'success',
            'stats': {
                'total_products': 0,
                'total_sales': 0,
                'total_users': 0
            }
        })
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health')
def health_check():
    """Endpoint de health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })

def setup_webhook():
    """Configura webhook se URL estiver definida"""
    if WEBHOOK_URL:
        try:
            telegram_bot.set_webhook(f"{WEBHOOK_URL}/webhook")
            logger.info(f"Webhook configurado: {WEBHOOK_URL}/webhook")
        except Exception as e:
            logger.error(f"Erro ao configurar webhook: {e}")

if __name__ == '__main__':
    # Verificar se token está configurado
    if BOT_TOKEN == 'SEU_TOKEN_AQUI':
        logger.warning("Token do bot não configurado! Configure BOT_TOKEN no arquivo .env")
    
    # Configurar webhook se especificado
    if WEBHOOK_URL:
        setup_webhook()
    else:
        logger.info("Webhook não configurado. Bot rodará em modo polling em desenvolvimento.")
    
    # Iniciar aplicação
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    logger.info(f"Iniciando servidor Flask na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)


@app.route('/api/delivery/stats', methods=['GET'])
def get_delivery_stats():
    """API para estatísticas de entrega"""
    try:
        days = int(request.args.get('days', 7))
        stats = delivery_scheduler.generate_delivery_report(days)
        return jsonify({
            'status': 'success',
            'data': stats
        })
    except Exception as e:
        logger.error(f"Erro ao buscar estatísticas de entrega: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/delivery/cleanup', methods=['POST'])
def cleanup_expired_downloads():
    """API para limpeza de downloads expirados"""
    try:
        removed_count = delivery_scheduler.cleanup_expired_downloads()
        return jsonify({
            'status': 'success',
            'message': f'{removed_count} downloads expirados removidos'
        })
    except Exception as e:
        logger.error(f"Erro na limpeza: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/delivery/warnings', methods=['POST'])
def send_expiry_warnings():
    """API para enviar avisos de expiração"""
    try:
        warning_count = delivery_scheduler.send_expiry_warnings()
        return jsonify({
            'status': 'success',
            'message': f'{warning_count} avisos enviados'
        })
    except Exception as e:
        logger.error(f"Erro no envio de avisos: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/admin')
def admin_panel():
    """Página de administração"""
    return render_template('admin.html')

@app.route('/api/products', methods=['POST'])
def create_product():
    """API para criar novo produto"""
    try:
        from product_manager import ProductManager
        product_manager = ProductManager(db_manager)
        
        # Obter dados do formulário
        name = request.form.get('name')
        description = request.form.get('description', '')
        price_stars = int(request.form.get('price_stars', 0))
        
        if not name or price_stars <= 0:
            return jsonify({'error': 'Nome e preço são obrigatórios'}), 400
        
        # Upload do arquivo
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'Arquivo de vídeo é obrigatório'}), 400
        
        # Salvar arquivo
        file_path = product_manager.upload_video(file.read(), file.filename)
        
        # Upload da thumbnail (opcional)
        thumbnail_path = None
        thumbnail = request.files.get('thumbnail')
        if thumbnail:
            thumbnail_path = product_manager.upload_video(thumbnail.read(), thumbnail.filename, 'thumbnails')
        
        # Criar produto no banco
        product_id = product_manager.create_product(
            name=name,
            description=description,
            price_stars=price_stars,
            file_path=file_path,
            thumbnail_path=thumbnail_path
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Produto criado com sucesso',
            'product_id': product_id
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar produto: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """API para atualizar produto"""
    try:
        from product_manager import ProductManager
        product_manager = ProductManager(db_manager)
        
        data = request.get_json()
        success = product_manager.update_product(product_id, **data)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Produto atualizado com sucesso'
            })
        else:
            return jsonify({'error': 'Produto não encontrado'}), 404
            
    except Exception as e:
        logger.error(f"Erro ao atualizar produto: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """API para excluir produto"""
    try:
        from product_manager import ProductManager
        product_manager = ProductManager(db_manager)
        
        success = product_manager.delete_product(product_id)
        
        if success:
            return jsonify({
                'status': 'success',
                'message': 'Produto excluído com sucesso'
            })
        else:
            return jsonify({'error': 'Produto não encontrado'}), 404
            
    except Exception as e:
        logger.error(f"Erro ao excluir produto: {e}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """API para upload de arquivos"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Nenhum arquivo enviado'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Nenhum arquivo selecionado'}), 400
        
        from product_manager import ProductManager
        product_manager = ProductManager(db_manager)
        
        file_path = product_manager.upload_video(file.read(), file.filename)
        
        return jsonify({
            'status': 'success',
            'file_path': file_path,
            'message': 'Arquivo enviado com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro no upload: {e}")
        return jsonify({'error': 'Erro no upload do arquivo'}), 500

