# handlers/client.py
import logging
import asyncio
from telegram import Update
from telegram.ext import CommandHandler, CallbackContext, MessageHandler, filters

logger = logging.getLogger(__name__)

def setup_client_handlers(application, db):
    """Configurar handlers del cliente"""
    
    # Comandos del cliente
    application.add_handler(CommandHandler("start", lambda update, context: start_handler(update, context, db)))
    application.add_handler(CommandHandler("menu", menu_handler))
    application.add_handler(CommandHandler("categoria", categoria_handler))
    application.add_handler(CommandHandler("agregar", agregar_handler))
    application.add_handler(CommandHandler("carrito", carrito_handler))
    application.add_handler(CommandHandler("pedir", lambda update, context: pedir_handler(update, context, db)))
    application.add_handler(CommandHandler("limpiar", limpiar_handler))
    
    # Manejador de mensajes de texto (para capturar nombre)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

async def start_handler(update: Update, context: CallbackContext, db) -> None:
    """Manejar comando /start"""
    user = update.effective_user
    
    # Registrar usuario en base de datos
    db.get_or_create_user(
        telegram_id=user.id,
        full_name=user.full_name
    )
    
    # Verificar si hay argumento (mesa desde QR)
    args = context.args
    if args and len(args) > 0:
        mesa = args[0]
        context.user_data['mesa_actual'] = mesa
        welcome_text = f"""¡Hola {user.first_name}! 👋

Bienvenido al sistema de pedidos del restaurante.

✅ Mesa registrada: *{mesa}*

Usa /menu para ver el menú disponible"""
    else:
        welcome_text = f"""¡Hola {user.first_name}! 👋

Para comenzar, escanea el código QR de tu mesa o escribe:
/start mesa_5
/start barra_2
/start terraza_1"""
    
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def menu_handler(update: Update, context: CallbackContext) -> None:
    """Mostrar menú categoría por categoría"""
    try:
        # Verificar que el usuario esté en una mesa
        if 'mesa_actual' not in context.user_data:
            await update.message.reply_text(
                "❌ Primero necesitas registrar una mesa.\n"
                "Usa: /start mesa_1"
            )
            return
        
        # Aquí deberías obtener los productos de la base de datos
        # Por ahora usamos datos de ejemplo
        productos_ejemplo = [
            {'id': 1, 'name': 'Hamburguesa', 'price': 10.0, 'category': 'Comida'},
            {'id': 2, 'name': 'Pizza', 'price': 15.0, 'category': 'Comida'},
            {'id': 3, 'name': 'Refresco', 'price': 3.0, 'category': 'Bebidas'},
        ]
        
        from collections import defaultdict
        products = productos_ejemplo
        
        if not products:
            await update.message.reply_text("📭 El menú está vacío en este momento.")
            return
        
        # Agrupar por categoría
        by_category = defaultdict(list)
        for product in products:
            category = product.get('category', 'General')
            by_category[category].append(product)
        
        categories_list = list(by_category.keys())
        context.user_data['categorias_menu'] = categories_list
        
        response = "📁 *SELECCIONA UNA CATEGORÍA*\n\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, category in enumerate(categories_list, 1):
            count = len(by_category[category])
            response += f"`{i}.` *{category}* - ({count} productos)\n"
        
        response += "\nPara ver productos: `/categoria [número]`\n"
        response += "Ejemplo: `/categoria 1`"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al obtener menú: {e}")
        await update.message.reply_text("❌ Error al cargar el menú.")

async def categoria_handler(update: Update, context: CallbackContext) -> None:
    """Ver productos de una categoría específica"""
    try:
        if not context.args:
            await update.message.reply_text(
                "📁 Para ver productos de una categoría:\n\n"
                "Escribe: `/categoria [número]`\n"
                "Ejemplo: `/categoria 1`"
            )
            return
        
        try:
            categoria_num = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Debes ingresar un número. Ejemplo: /categoria 1")
            return
        
        # Datos de ejemplo - reemplazar con tu base de datos
        productos_ejemplo = [
            {'id': 1, 'name': 'Hamburguesa', 'price': 10.0, 'category': 'Comida', 'description': 'Deliciosa hamburguesa'},
            {'id': 2, 'name': 'Pizza', 'price': 15.0, 'category': 'Comida', 'description': 'Pizza familiar'},
            {'id': 3, 'name': 'Refresco', 'price': 3.0, 'category': 'Bebidas', 'description': 'Refresco 500ml'},
        ]
        
        from collections import defaultdict
        products = productos_ejemplo
        by_category = defaultdict(list)
        for product in products:
            category = product.get('category', 'General')
            by_category[category].append(product)
        
        categories_list = list(by_category.keys())
        
        if categoria_num < 1 or categoria_num > len(categories_list):
            await update.message.reply_text(f"❌ Número inválido. Usa un número entre 1 and {len(categories_list)}")
            return
        
        categoria_nombre = categories_list[categoria_num - 1]
        productos_categoria = by_category[categoria_nombre]
        
        # Guardar en context para referencias futuras
        context.user_data['ultima_categoria'] = categoria_nombre
        context.user_data['productos_actuales'] = productos_categoria
        
        # Crear respuesta
        response = f"🍽 *{categoria_nombre.upper()}*\n\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, producto in enumerate(productos_categoria, 1):
            nombre = producto.get('name', 'Sin nombre')
            precio = producto.get('price', 0)
            descripcion = producto.get('description', '')
            
            response += f"`{i}.` *{nombre}* - `${precio:.2f}`\n"
            if descripcion:
                response += f"    _{descripcion}_\n"
            response += f"    `/agregar {i}`\n\n"
        
        response += "Para agregar: `/agregar [número_producto]`\n"
        response += "Ejemplo: `/agregar 1`"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al obtener categoría: {e}")
        await update.message.reply_text("❌ Error al cargar la categoría.")

async def agregar_handler(update: Update, context: CallbackContext) -> None:
    """Agregar producto al carrito"""
    try:
        if 'mesa_actual' not in context.user_data:
            await update.message.reply_text(
                "❌ Primero necesitas registrar una mesa.\n"
                "Usa: /start mesa_1"
            )
            return
        
        if not context.args:
            await update.message.reply_text(
                "❌ Debes especificar un número de producto.\n"
                "Ejemplo: /agregar 1"
            )
            return
        
        try:
            producto_num = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Debes ingresar un número. Ejemplo: /agregar 1")
            return
        
        if 'productos_actuales' not in context.user_data:
            await update.message.reply_text(
                "❌ Primero debes seleccionar una categoría.\n"
                "Usa /menu para ver categorías disponibles."
            )
            return
        
        productos = context.user_data['productos_actuales']
        
        if producto_num < 1 or producto_num > len(productos):
            await update.message.reply_text(f"❌ Número inválido. Usa un número entre 1 and {len(productos)}")
            return
        
        producto = productos[producto_num - 1]
        nombre = producto.get('name', 'Sin nombre')
        precio = producto.get('price', 0)
        
        cantidad = 1
        if len(context.args) > 1:
            try:
                cantidad = int(context.args[1])
                if cantidad < 1:
                    cantidad = 1
            except ValueError:
                cantidad = 1
        
        if 'carrito' not in context.user_data:
            context.user_data['carrito'] = []
        
        # Agregar al carrito
        item_carrito = {
            'id': producto.get('id'),
            'nombre': nombre,
            'precio': precio,
            'cantidad': cantidad
        }
        
        # Buscar si ya existe en el carrito
        encontrado = False
        for item in context.user_data['carrito']:
            if item['id'] == producto.get('id'):
                item['cantidad'] += cantidad
                encontrado = True
                break
        
        if not encontrado:
            context.user_data['carrito'].append(item_carrito)
        
        await update.message.reply_text(
            f"✅ *{nombre}*\n"
            f"Cantidad: {cantidad}\n"
            f"Total: ${precio * cantidad:.2f}\n\n"
            f"Añadido al carrito correctamente.\n\n"
            f"Usa /carrito para ver tu pedido\n"
            f"Usa /pedir para confirmar el pedido",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error al agregar al carrito: {e}")
        await update.message.reply_text("❌ Error al agregar al carrito.")

async def carrito_handler(update: Update, context: CallbackContext) -> None:
    """Ver contenido del carrito"""
    try:
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
        
        total = 0
        response = "🛒 *TU CARRITO*\n\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, item in enumerate(carrito, 1):
            subtotal = item['precio'] * item['cantidad']
            total += subtotal
            response += f"`{i}.` *{item['nombre']}*\n"
            response += f"    {item['cantidad']} x ${item['precio']:.2f} = ${subtotal:.2f}\n\n"
        
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += f"💰 *TOTAL: ${total:.2f}*\n\n"
        response += "📍 *Mesa:* " + context.user_data.get('mesa_actual', 'No registrada') + "\n\n"
        response += "*Comandos:*\n"
        response += "✅ /pedir - Confirmar y enviar pedido\n"
        response += "🗑 /limpiar - Vaciar carrito\n"
        response += "📁 /menu - Seguir comprando"
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error al ver carrito: {e}")
        await update.message.reply_text("❌ Error al cargar el carrito.")

async def pedir_handler(update: Update, context: CallbackContext, db) -> None:
    """Confirmar y enviar el pedido - PEDIR NOMBRE DEL CLIENTE"""
    try:
        if 'carrito' not in context.user_data or not context.user_data['carrito']:
            await update.message.reply_text("❌ Tu carrito está vacío.")
            return
        
        if 'mesa_actual' not in context.user_data:
            await update.message.reply_text("❌ Primero necesitas registrar una mesa.")
            return
        
        # Pedir nombre del cliente si no está en user_data
        if 'nombre_cliente' not in context.user_data:
            context.user_data['pendiente_confirmacion'] = True
            await update.message.reply_text(
                "📝 Por favor, ingresa tu nombre para el pedido:"
            )
            return
        
        carrito = context.user_data['carrito']
        mesa = context.user_data['mesa_actual']
        nombre_cliente = context.user_data['nombre_cliente']
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
        pedido = db.create_order(
            telegram_id=usuario.id,
            table_number=mesa,
            items=items,
            notes=f"Cliente: {nombre_cliente}"
        )
        
        # NOTIFICACIÓN DE PEDIDO RECIBIDO
        response = f"✅ *PEDIDO CONFIRMADO* ✅\n\n"
        response += f"📦 *Código de pedido:* {pedido.get('order_code', 'N/A')}\n"
        response += f"📍 *Mesa:* {mesa}\n"
        response += f"👤 *Cliente:* {nombre_cliente}\n\n"
        response += "*Productos:*\n"
        
        for i, item in enumerate(carrito, 1):
            subtotal = item['precio'] * item['cantidad']
            response += f"`{i}.` {item['nombre']} - {item['cantidad']} x ${item['precio']:.2f}\n"
        
        response += f"\n💰 *TOTAL: ${total:.2f}*\n\n"
        response += "⏳ *Estado:* Recibido - En preparación\n"
        response += "📱 Recibirás una notificación cuando esté listo"
        
        # Limpiar carrito y nombre
        context.user_data['carrito'] = []
        if 'nombre_cliente' in context.user_data:
            del context.user_data['nombre_cliente']
        if 'pendiente_confirmacion' in context.user_data:
            del context.user_data['pendiente_confirmacion']
        
        await update.message.reply_text(response, parse_mode='Markdown')
        
        # SIMULAR NOTIFICACIÓN CUANDO EL PEDIDO TERMINA
        async def notificar_pedido_listo():
            await asyncio.sleep(10)  # Simular tiempo de preparación
            await update.message.reply_text(
                f"🎉 *PEDIDO LISTO* 🎉\n\n"
                f"📦 Pedido: {pedido.get('order_code', 'N/A')}\n"
                f"👤 Cliente: {nombre_cliente}\n"
                f"📍 Mesa: {mesa}\n\n"
                f"¡Tu pedido está listo para ser servido!",
                parse_mode='Markdown'
            )
        
        asyncio.create_task(notificar_pedido_listo())
        
    except Exception as e:
        logger.error(f"Error al confirmar pedido: {e}")
        await update.message.reply_text("❌ Error al confirmar el pedido.")

async def limpiar_handler(update: Update, context: CallbackContext) -> None:
    """Vaciar el carrito"""
    if 'carrito' in context.user_data:
        context.user_data['carrito'] = []
        await update.message.reply_text("🗑 Carrito vaciado correctamente.")
    else:
        await update.message.reply_text("✅ El carrito ya está vacío.")

async def handle_message(update: Update, context: CallbackContext) -> None:
    """Manejar mensajes de texto para capturar nombre del cliente"""
    if context.user_data.get('pendiente_confirmacion'):
        nombre_cliente = update.message.text
        context.user_data['nombre_cliente'] = nombre_cliente
        context.user_data['pendiente_confirmacion'] = False
        
        await update.message.reply_text(
            f"✅ Nombre registrado: *{nombre_cliente}*\n\n"
            f"Ahora confirma tu pedido con /pedir",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "Usa /menu para ver el menú o /help para ayuda"
        )