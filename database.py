import os
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

class DatabaseManager:
    """Gerenciador do banco de dados SQLite"""
    
    def __init__(self, db_path: str = "bot_database.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Inicializa o banco de dados com as tabelas necessárias"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela de usuários
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabela de produtos (vídeos)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS products (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    price_stars INTEGER NOT NULL,
                    file_path TEXT NOT NULL,
                    thumbnail_path TEXT,
                    file_size INTEGER,
                    duration_seconds INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabela de transações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    amount_stars INTEGER NOT NULL,
                    telegram_payment_id TEXT UNIQUE,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Tabela de downloads/acessos
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS downloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    transaction_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    product_id INTEGER NOT NULL,
                    download_token TEXT UNIQUE NOT NULL,
                    download_count INTEGER DEFAULT 0,
                    max_downloads INTEGER DEFAULT 3,
                    last_access TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (transaction_id) REFERENCES transactions (id),
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (product_id) REFERENCES products (id)
                )
            ''')
            
            # Tabela de configurações
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            logging.info("Banco de dados inicializado com sucesso")
    
    def get_user_by_telegram_id(self, telegram_id: int) -> Optional[Dict[str, Any]]:
        """Busca usuário pelo ID do Telegram"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_user(self, telegram_id: int, username: str = None, 
                   first_name: str = None, last_name: str = None) -> int:
        """Cria um novo usuário"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO users (telegram_id, username, first_name, last_name)
                VALUES (?, ?, ?, ?)
            ''', (telegram_id, username, first_name, last_name))
            conn.commit()
            return cursor.lastrowid
    
    def get_active_products(self) -> List[Dict[str, Any]]:
        """Retorna todos os produtos ativos"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM products 
                WHERE is_active = 1 
                ORDER BY created_at DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]
    
    def get_product_by_id(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Busca produto pelo ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE id = ? AND is_active = 1", (product_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def create_transaction(self, user_id: int, product_id: int, amount_stars: int) -> int:
        """Cria uma nova transação"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO transactions (user_id, product_id, amount_stars)
                VALUES (?, ?, ?)
            ''', (user_id, product_id, amount_stars))
            conn.commit()
            return cursor.lastrowid
    
    def update_transaction_payment(self, transaction_id: int, telegram_payment_id: str, status: str = 'completed'):
        """Atualiza transação com dados do pagamento"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE transactions 
                SET telegram_payment_id = ?, status = ?, completed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (telegram_payment_id, status, transaction_id))
            conn.commit()
    
    def create_download_access(self, transaction_id: int, user_id: int, product_id: int, 
                              download_token: str, expiry_hours: int = 24, max_downloads: int = 3) -> int:
        """Cria acesso de download para uma transação"""
        expires_at = datetime.now() + timedelta(hours=expiry_hours)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO downloads (transaction_id, user_id, product_id, download_token, 
                                     max_downloads, expires_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (transaction_id, user_id, product_id, download_token, max_downloads, expires_at))
            conn.commit()
            return cursor.lastrowid
    
    def get_download_access(self, download_token: str) -> Optional[Dict[str, Any]]:
        """Busca acesso de download pelo token"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT d.*, p.file_path, p.name as product_name
                FROM downloads d
                JOIN products p ON d.product_id = p.id
                WHERE d.download_token = ? AND d.expires_at > CURRENT_TIMESTAMP
            ''', (download_token,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def increment_download_count(self, download_token: str) -> bool:
        """Incrementa contador de downloads e retorna se ainda é válido"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE downloads 
                SET download_count = download_count + 1, last_access = CURRENT_TIMESTAMP
                WHERE download_token = ? AND download_count < max_downloads
            ''', (download_token,))
            conn.commit()
            return cursor.rowcount > 0

