import os
import schedule
import time
import logging
from datetime import datetime
from database import DatabaseManager
from delivery_system import DeliveryScheduler

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class AutomatedScheduler:
    """Agendador automático para tarefas de manutenção"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.delivery_scheduler = DeliveryScheduler(self.db_manager)
        self.setup_schedules()
    
    def setup_schedules(self):
        """Configura agendamentos automáticos"""
        
        # Limpeza de downloads expirados - a cada hora
        schedule.every().hour.do(self.cleanup_expired_downloads)
        
        # Envio de avisos de expiração - a cada 2 horas
        schedule.every(2).hours.do(self.send_expiry_warnings)
        
        # Relatório diário - às 9:00
        schedule.every().day.at("09:00").do(self.generate_daily_report)
        
        # Backup do banco de dados - às 3:00
        schedule.every().day.at("03:00").do(self.backup_database)
        
        logger.info("Agendamentos configurados com sucesso")
    
    def cleanup_expired_downloads(self):
        """Tarefa: Limpeza de downloads expirados"""
        try:
            removed_count = self.delivery_scheduler.cleanup_expired_downloads()
            logger.info(f"Limpeza concluída: {removed_count} downloads expirados removidos")
        except Exception as e:
            logger.error(f"Erro na limpeza automática: {e}")
    
    def send_expiry_warnings(self):
        """Tarefa: Envio de avisos de expiração"""
        try:
            warning_count = self.delivery_scheduler.send_expiry_warnings()
            logger.info(f"Avisos enviados: {warning_count} usuários notificados")
        except Exception as e:
            logger.error(f"Erro no envio de avisos: {e}")
    
    def generate_daily_report(self):
        """Tarefa: Geração de relatório diário"""
        try:
            report = self.delivery_scheduler.generate_delivery_report(1)  # Últimas 24h
            
            # Salvar relatório em arquivo
            report_file = f"reports/daily_report_{datetime.now().strftime('%Y%m%d')}.json"
            os.makedirs('reports', exist_ok=True)
            
            import json
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Relatório diário gerado: {report_file}")
            
            # Log das estatísticas principais
            summary = report.get('summary', {})
            logger.info(f"Estatísticas do dia: {summary.get('total_deliveries', 0)} entregas, "
                       f"{summary.get('total_downloads', 0)} downloads, "
                       f"{summary.get('usage_rate', 0)}% taxa de utilização")
            
        except Exception as e:
            logger.error(f"Erro na geração do relatório diário: {e}")
    
    def backup_database(self):
        """Tarefa: Backup do banco de dados"""
        try:
            import shutil
            
            # Criar diretório de backup
            backup_dir = 'backups'
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nome do arquivo de backup
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f"{backup_dir}/database_backup_{timestamp}.db"
            
            # Copiar banco de dados
            shutil.copy2(self.db_manager.db_path, backup_file)
            
            logger.info(f"Backup do banco criado: {backup_file}")
            
            # Manter apenas os últimos 7 backups
            self.cleanup_old_backups(backup_dir, keep_count=7)
            
        except Exception as e:
            logger.error(f"Erro no backup do banco: {e}")
    
    def cleanup_old_backups(self, backup_dir: str, keep_count: int = 7):
        """Remove backups antigos, mantendo apenas os mais recentes"""
        try:
            import glob
            
            # Listar arquivos de backup
            backup_files = glob.glob(f"{backup_dir}/database_backup_*.db")
            backup_files.sort(reverse=True)  # Mais recentes primeiro
            
            # Remover backups antigos
            for old_backup in backup_files[keep_count:]:
                os.remove(old_backup)
                logger.info(f"Backup antigo removido: {old_backup}")
                
        except Exception as e:
            logger.error(f"Erro na limpeza de backups: {e}")
    
    def run(self):
        """Executa o agendador"""
        logger.info("Iniciando agendador automático...")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
                
        except KeyboardInterrupt:
            logger.info("Agendador interrompido pelo usuário")
        except Exception as e:
            logger.error(f"Erro no agendador: {e}")

def main():
    """Função principal"""
    scheduler = AutomatedScheduler()
    scheduler.run()

if __name__ == '__main__':
    main()

