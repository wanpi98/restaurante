# bot.py
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackContext, CallbackQueryHandler, ConversationHandler, MessageHandler, filters
from config import Config
from database import Database

# Configurar logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados de conversación
MESA, CATEGORIA, PRODUCTO, CANTIDAD, CONFIRMAR = range(5)

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
        self.application.add_handler(CommandHandler("categoria", self.ver_categoria))
        self.application.add_handler(CommandHandler("carrito", self.ver_carrito))
        self.application.add_handler(CommandHandler("pedir", self.confirmar_pedido))
        self.application.add_handler(CommandHandler("limpiar", self.limpiar_carrito))
        
        # Para agregar productos: /agregar [numero]
        self.application.add_handler(CommandHandler("agregar", self.agregar_al_carrito))
    
    async def start(self, update: Update, context: CallbackContext) -> None:
        """Manejar comando /start"""
        user = update.effective_user
        
        # Registrar usuario en base de datos
        self.db.get_or_create_user(
            telegram_id=user.id,
            full_name=user.full_name
        )
        # ... resto del código
        
        # Verificar si hay argumento (mesa desde QR)
        args = context.args
        if args and len(args) > 0:
            mesa = args[0]  # Ej: "mesa_5", "barra_1", "terraza_3"
            context.user_data['mesa_actual'] = mesa
            welcome_text = f"""¡Hola {user.first_name}! 👋

Bienvenido al sistema de pedidos del restaurante.

✅ Mesa registrada: *{mesa}*

📋 *Comandos disponibles:*
/menu - Ver el menú disponible
/help - Ver ayuda

Para hacer un pedido, primero ve el menú con /menu
"""
        else:
            # Si no hay código QR, pedir que escanee
            welcome_text = f"""¡Hola {user.first_name}! 👋

Bienvenido al sistema de pedidos del restaurante.

📍 Para comenzar, necesitas:
1. Escanear el código QR de tu mesa
2. O escribe el número de tu mesa

Por favor, escanea el código QR o escribe tu mesa así:
/start mesa_5
/start barra_2
/start terraza_1
"""
        await update.message.reply_text(welcome_text, parse_mode='Markdown')
    
    async def help(self, update: Update, context: CallbackContext) -> None:
        """Manejar comando /help"""
        help_text = """
*Ayuda del sistema:*

👤 *Cliente:*
/start [mesa] - Iniciar o registrar mesa
/menu - Ver categorías de productos
/categoria [número] - Ver productos de una categoría
/agregar [número] - Agregar producto al carrito
/carrito - Ver carrito actual
/pedir - Confirmar y enviar pedido
/limpiar - Vaciar carrito
/ayuda - Ver esta ayuda

👨‍🍳 *Dependiente:*
/pedidos - Ver pedidos pendientes
/estadisticas - Ver estadísticas
/activar - Activar modo dependiente
/desactivar - Desactivar modo dependiente

👑 *Administrador:*
/admin - Panel de administración
/admin_productos - Gestionar productos
/admin_usuarios - Gestionar usuarios
/admin_estadisticas - Ver estadísticas completas
"""
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def menu(self, update: Update, context: CallbackContext) -> None:
        """Mostrar menú categoría por categoría"""
        try:
            # Obtener categorías únicas
            from collections import defaultdict
            products = self.db.get_all_products()
            
            if not products:
                await update.message.reply_text("📭 El menú está vacío en este momento.")
                return
            
            # Agrupar por categoría
            by_category = defaultdict(list)
            for product in products:
                category = product.get('category', 'General')
                by_category[category].append(product)
            
            # Crear respuesta
            categories_list = list(by_category.keys())
            context.user_data['categorias_menu'] = categories_list
            
            response = "📁 *SELECCIONA UNA CATEGORÍA*\n\n"
            response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, category in enumerate(categories_list, 1):
                # Contar productos en esta categoría
                count = len(by_category[category])
                response += f"`{i}.` *{category}* - ({count} productos)\n"
            
            response += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += "Para ver productos de una categoría, escribe:\n"
            response += "`/categoria [número]`\n"
            response += "Ejemplo: `/categoria 1`\n"
            response += "O usa /help para ver todos los comandos."
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error al obtener menú: {e}")
            await update.message.reply_text("❌ Error al cargar el menú.")
    
    async def ver_categoria(self, update: Update, context: CallbackContext) -> None:
        """Ver productos de una categoría específica"""
        try:
            if not context.args:
                # Si no se especifica categoría, mostrar instrucciones
                response = "📁 *Para ver productos de una categoría:*\n\n"
                response += "Escribe: `/categoria [número]`\n"
                response += "Ejemplo: `/categoria 1`\n\n"
                response += "Primero usa /menu para ver las categorías disponibles."
                await update.message.reply_text(response, parse_mode='Markdown')
                return
            
            # Obtener número de categoría
            try:
                categoria_num = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Debes ingresar un número. Ejemplo: /categoria 1")
                return
            
            # Obtener todas las categorías
            from collections import defaultdict
            products = self.db.get_all_products()
            by_category = defaultdict(list)
            for product in products:
                category = product.get('category', 'General')
                by_category[category].append(product)
            
            categories_list = list(by_category.keys())
            
            # Validar número
            if categoria_num < 1 or categoria_num > len(categories_list):
                await update.message.reply_text(f"❌ Número inválido. Usa un número entre 1 y {len(categories_list)}")
                return
            
            categoria_nombre = categories_list[categoria_num - 1]
            productos_categoria = by_category[categoria_nombre]
            
            # Guardar en context para referencias futuras
            context.user_data['ultima_categoria'] = categoria_nombre
            context.user_data['productos_actuales'] = productos_categoria
            
            # Crear respuesta
            response = f"🍽️ *{categoria_nombre.upper()}*\n\n"
            response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, producto in enumerate(productos_categoria, 1):
                nombre = producto.get('name', 'Sin nombre')
                precio = producto.get('price', 0)
                descripcion = producto.get('description', '')
                
                # Formatear respuesta
                response += f"`{i}.` *{nombre}* - `${precio:.2f}`\n"
                if descripcion:
                    response += f"    _{descripcion}_\n"
                response += f"    `/agregar {i}`\n\n"
            
            response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += "Para agregar al carrito, usa:\n"
            response += "`/agregar [número_producto]`\n"
            response += "Ejemplo: `/agregar 1`\n\n"
            response += "Usa /menu para volver a categorías\n"
            response += "Usa /carrito para ver tu pedido"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error al obtener categoría: {e}")
            await update.message.reply_text("❌ Error al cargar la categoría.")
    
    async def agregar_al_carrito(self, update: Update, context: CallbackContext) -> None:
        """Agregar producto al carrito"""
        try:
            # Verificar que el usuario esté en una mesa
            if 'mesa_actual' not in context.user_data:
                await update.message.reply_text(
                    "❌ Primero necesitas registrar una mesa.\n"
                    "1. Escanea el código QR de tu mesa\n"
                    "2. O inicia con: /start mesa_1"
                )
                return
            
            if not context.args:
                await update.message.reply_text(
                    "❌ Debes especificar un número de producto.\n"
                    "Ejemplo: /agregar 1\n\n"
                    "Usa primero /categoria [número] para ver los productos."
                )
                return
            
            # Obtener número de producto
            try:
                producto_num = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Debes ingresar un número. Ejemplo: /agregar 1")
                return
            
            # Verificar que tenemos productos en contexto
            if 'productos_actuales' not in context.user_data:
                await update.message.reply_text(
                    "❌ Primero debes seleccionar una categoría.\n"
                    "Usa /menu para ver categorías disponibles."
                )
                return
            
            productos = context.user_data['productos_actuales']
            
            # Validar número
            if producto_num < 1 or producto_num > len(productos):
                await update.message.reply_text(
                    f"❌ Número inválido. Usa un número entre 1 y {len(productos)}"
                )
                return
            
            # Obtener producto seleccionado
            producto = productos[producto_num - 1]
            producto_id = producto.get('id')
            nombre = producto.get('name', 'Sin nombre')
            precio = producto.get('price', 0)
            
            # Obtener cantidad (opcional)
            cantidad = 1
            if len(context.args) > 1:
                try:
                    cantidad = int(context.args[1])
                    if cantidad < 1:
                        cantidad = 1
                except ValueError:
                    cantidad = 1
            
            # Inicializar carrito si no existe
            if 'carrito' not in context.user_data:
                context.user_data['carrito'] = []
            
            # Agregar al carrito
            item_carrito = {
                'id': producto_id,
                'nombre': nombre,
                'precio': precio,
                'cantidad': cantidad
            }
            
            # Buscar si ya existe en el carrito
            encontrado = False
            for item in context.user_data['carrito']:
                if item['id'] == producto_id:
                    item['cantidad'] += cantidad
                    encontrado = True
                    break
            
            if not encontrado:
                context.user_data['carrito'].append(item_carrito)
            
            await update.message.reply_text(
                f"✅ *{nombre}*\n"
                f"📦 Cantidad: {cantidad}\n"
                f"💰 Total: ${precio * cantidad:.2f}\n\n"
                f"Añadido al carrito correctamente.\n\n"
                f"Usa /carrito para ver tu pedido\n"
                f"Usa /pedir para confirmar el pedido",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logger.error(f"Error al agregar al carrito: {e}")
            await update.message.reply_text("❌ Error al agregar al carrito.")
    
    async def ver_carrito(self, update: Update, context: CallbackContext) -> None:
        """Ver contenido del carrito"""
        try:
            # Verificar que hay carrito
            if 'carrito' not in context.user_data or not context.user_data['carrito']:
                await update.message.reply_text(
                    "🛒 Tu carrito está vacío.\n\n"
                    "Para agregar productos:\n"
                    "1. Usa /menu para ver categorías\n"
                    "2. Usa /categoria [número] para ver productos\n"
                    "3. Usa /agregar [número] para añadir al carrito"
                )
                return
            
            carrito = context.user_data['carrito']
            
            # Calcular total
            total = 0
            response = "🛒 *TU CARRITO* 🛒\n\n"
            response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            for i, item in enumerate(carrito, 1):
                subtotal = item['precio'] * item['cantidad']
                total += subtotal
                response += f"`{i}.` *{item['nombre']}*\n"
                response += f"    📦 {item['cantidad']} x ${item['precio']:.2f} = ${subtotal:.2f}\n"
                response += f"    ❌ /eliminar {i}\n\n"
            
            response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            response += f"💰 *TOTAL: ${total:.2f}*\n\n"
            response += "📍 *Mesa:* " + context.user_data.get('mesa_actual', 'No registrada') + "\n\n"
            response += "*Comandos disponibles:*\n"
            response += "✅ /pedir - Confirmar y enviar pedido\n"
            response += "🗑️ /limpiar - Vaciar carrito\n"
            response += "📁 /menu - Seguir comprando\n"
            response += "❌ /eliminar [número] - Eliminar producto"
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error al ver carrito: {e}")
            await update.message.reply_text("❌ Error al cargar el carrito.")
    
    async def confirmar_pedido(self, update: Update, context: CallbackContext) -> None:
        """Confirmar y enviar el pedido"""
        try:
            # Verificar que hay carrito
            if 'carrito' not in context.user_data or not context.user_data['carrito']:
                await update.message.reply_text(
                    "❌ Tu carrito está vacío.\n\n"
                    "Agrega productos con /menu y /agregar"
                )
                return
            
            # Verificar que el usuario esté en una mesa
            if 'mesa_actual' not in context.user_data:
                await update.message.reply_text(
                    "❌ Primero necesitas registrar una mesa.\n"
                    "1. Escanea el código QR de tu mesa\n"
                    "2. O inicia con: /start mesa_1"
                )
                return
            
            carrito = context.user_data['carrito']
            mesa = context.user_data['mesa_actual']
            usuario = update.effective_user
            
            # Calcular total
            total = 0
            items = []
            
            for item in carrito:
                subtotal = item['precio'] * item['cantidad']
                total += subtotal
                items.append({
                    'product_id': item['id'],
                    'nombre': item['nombre'],
                    'precio': item['precio'],
                    'cantidad': item['cantidad']
                })
            
            # Crear pedido en la base de datos
            pedido = self.db.create_order(
                telegram_id=usuario.id,
                table_number=mesa,
                items=items,
                notes=""
            )
            
            if not pedido:
                await update.message.reply_text("❌ Error al crear el pedido. Inténtalo de nuevo.")
                return
            
            # Confirmar al cliente
            response = f"✅ *PEDIDO CONFIRMADO* ✅\n\n"
            response += f"📦 *Código de pedido:* {pedido.get('order_code', 'N/A')}\n"
            response += f"📍 *Mesa:* {mesa}\n"
            response += f"👤 *Cliente:* {usuario.first_name}\n\n"
            response += "*Productos:*\n"
            
            for i, item in enumerate(carrito, 1):
                subtotal = item['precio'] * item['cantidad']
                response += f"`{i}.` {item['nombre']} - {item['cantidad']} x ${item['precio']:.2f} = ${subtotal:.2f}\n"
            
            response += f"\n💰 *TOTAL: ${total:.2f}*\n\n"
            response += "⏳ *Estado:* Pendiente\n"
            response += "📱 Usa /estado para ver el estado de tu pedido\n"
            response += "🔄 Usa /menu para hacer otro pedido"
            
            # Limpiar carrito
            context.user_data['carrito'] = []
            
            await update.message.reply_text(response, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Error al confirmar pedido: {e}")
            await update.message.reply_text("❌ Error al confirmar el pedido.")
    
    async def limpiar_carrito(self, update: Update, context: CallbackContext) -> None:
        """Vaciar el carrito"""
        if 'carrito' in context.user_data:
            context.user_data['carrito'] = []
            await update.message.reply_text("🗑️ Carrito vaciado correctamente.")
        else:
            await update.message.reply_text("✅ El carrito ya está vacío.")
    
    def run(self):
        """Iniciar el bot"""
        self.application.run_polling()