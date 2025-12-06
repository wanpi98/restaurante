# bot.py
import logging
from telegram.ext import Application
from config import Config
from database import Database
from handlers.client import setup_client_handlers

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class RestaurantBot:
    def __init__(self):
        self.db = Database()
        self.application = Application.builder().token(Config.BOT_TOKEN).build()
        self.setup_handlers()
    
    def setup_handlers(self):
        """Configurar todos los handlers"""
        setup_client_handlers(self.application, self.db)
    
    def run(self):
        """Iniciar el bot"""
        self.application.run_polling()