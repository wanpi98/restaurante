# bot.py
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext
from config import Config
from database import Database

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
        """Configurar manejadores de comandos básicos"""
        # Comandos de inicio
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("help", self.help))
        self.application.add_handler(CommandHandler("menu", self.menu))
    
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Manejar comando /start"""
        user = update.effective_user
        
        # Registrar usuario en base de datos
        self.db.get_or_create_user(
            telegram_id=user.id,
            full_name=user.full_name,
            username=user.username
        )
        
        # Responder
        welcome_text = f"""
¡Hola {user.first_name}! 👋

Bienvenido al sistema de pedidos del restaurante.

📋 *Comandos disponibles:*
/menu - Ver el menú disponible
/help - Ver ayuda

Escanea el código QR de tu mesa para hacer un pedido.
        """
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help(self, update: Update, context: CallbackContext) -> None:
        """Manejar comando /help"""
        help_text = """
*Ayuda del sistema:*

👤 *Cliente:*
/menu - Ver menú
/pedido - Hacer pedido
/estado - Ver estado de pedido

👨‍🍳 *Dependiente:*
/pedidos - Ver pedidos pendientes
/estadisticas - Ver estadísticas
/activar - Activar modo dependiente

👑 *Administrador:*
/admin - Panel de administración
        """
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def menu(self, update: Update, context: CallbackContext) -> None:
        """Manejar comando /menu"""
        try:
            # Obtener productos de la base de datos
            products = self.db.get_all_products()
            
            if not products:
                await update.message.reply_text("📭 El menú está vacío en este momento.")
                return
            
            # Agrupar por categoría
            from collections import defaultdict
            by_category = defaultdict(list)
            
            for product in products:
                category = product.get('category', 'General')
                by_category[category].append(product)
            
            # Formatear respuesta
            menu_text = "🍽️ *Menú del Restaurante*\n\n"
            
            for category, items in by_category.items():
                menu_text += f"*{category}:*\n"
                for item in items:
                    price = item.get('price', 0)
                    name = item.get('name', 'Sin nombre')
                    menu_text += f"  • {name} - ${price:.2f}\n"
                menu_text += "\n"
            
            await update.message.reply_text(menu_text, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error al obtener menú: {e}")
            await update.message.reply_text("❌ Error al cargar el menú.")
    
    def run(self):
        """Iniciar el bot"""
        self.application.run_polling()