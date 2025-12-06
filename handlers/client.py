# handlers/client.py
import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackContext, MessageHandler, filters, CallbackQueryHandler

logger = logging.getLogger(__name__)

def setup_client_handlers(application, db):
    """Configurar handlers del cliente con botones"""
    
    # Comandos del cliente
    application.add_handler(CommandHandler("start", lambda update, context: start_handler(update, context, db)))
    application.add_handler(CommandHandler("menu", lambda update, context: menu_handler(update, context, db)))
    application.add_handler(CommandHandler("carrito", carrito_handler))
    application.add_handler(CommandHandler("pedir", lambda update, context: pedir_handler(update, context, db)))
    application.add_handler(CommandHandler("limpiar", limpiar_handler))
    
    # Manejadores de callback para botones
    application.add_handler(CallbackQueryHandler(lambda update, context: categoria_callback(update, context, db), pattern="^categoria_"))
    application.add_handler(CallbackQueryHandler(producto_callback, pattern="^producto_"))
    application.add_handler(CallbackQueryHandler(cantidad_callback, pattern="^cantidad_"))
    application.add_handler(CallbackQueryHandler(carrito_callback, pattern="^carrito$"))
    application.add_handler(CallbackQueryHandler(lambda update, context: volver_categorias_callback(update, context, db), pattern="^volver_categorias$"))
    
    # Manejador de mensajes de texto
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
        welcome_text = f"""¡Hola {user.first_name}! 👋👋

Bienvenido al sistema de pedidos del restaurante.

✅ Mesa registrada: *{mesa}*

Usa /menu para ver el menú disponible"""
    else:
        welcome_text = f"""¡Hola {user.first_name}! 👋👋

Para comenzar, escanea el código QR de tu mesa o escribe:
/start mesa_5
/start barra_2
/start terraza_1"""
    
    await update.message.reply_text(welcome_text)

async def menu_handler(update: Update, context: CallbackContext, db) -> None:
    """Mostrar menú con botones de categorías"""
    try:
        # Verificar que el usuario esté en una mesa
        if 'mesa_actual' not in context.user_data:
            await update.message.reply_text(
                "❌❌ Primero necesitas registrar una mesa.\n"
                "Usa: /start mesa_1"
            )
            return
        
        # Obtener productos de la base de datos
        products = db.get_products()
        
        if not products:
            await update.message.reply_text("📭📭 El menú está vacío en este momento.")
            return
        
        from collections import defaultdict
        # Agrupar por categoría
        by_category = defaultdict(list)
        for product in products:
            category = product.get('category', 'General')
            by_category[category].append(product)
        
        # Guardar en context para referencias futuras
        context.user_data['categorias_menu'] = list(by_category.keys())
        context.user_data['productos_por_categoria'] = by_category
        
        # Crear botones para categorías
        keyboard = []
        categories_list = list(by_category.keys())
        
        for i, category in enumerate(categories_list):
            count = len(by_category[category])
            # Crear botón para cada categoría
            keyboard.append([InlineKeyboardButton(
                f"{category} ({count} productos)", 
                callback_data=f"categoria_{category}"
            )])
        
        # Agregar botón para ver carrito
        keyboard.append([InlineKeyboardButton("🛒🛒🛒 Ver Carrito", callback_data="carrito")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "📁📁 *SELECCIONA UNA CATEGORÍA*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error al obtener menú: {e}")
        await update.message.reply_text("❌❌ Error al cargar el menú.")

async def categoria_callback(update: Update, context: CallbackContext, db) -> None:
    """Manejar clic en botón de categoría"""
    query = update.callback_query
    await query.answer()
    
    categoria_nombre = query.data.replace('categoria_', '')
    
    try:
        # Obtener productos de la categoría desde la base de datos
        productos_categoria = db.get_products_by_category(categoria_nombre)
        
        if not productos_categoria:
            await query.edit_message_text("No hay productos en esta categoría.")
            return
        
        # Guardar en context para referencias futuras
        context.user_data['ultima_categoria'] = categoria_nombre
        context.user_data['productos_actuales'] = productos_categoria
        
        # Crear botones para productos
        keyboard = []
        
        for i, producto in enumerate(productos_categoria, 1):
            nombre = producto.get('name', 'Sin nombre')
            precio = producto.get('price', 0)
            
            # Crear botón para cada producto
            keyboard.append([InlineKeyboardButton(
                f"{nombre} - ${precio:.2f}", 
                callback_data=f"producto_{producto['id']}"
            )])
        
        # Botones de navegación
        keyboard.append([
            InlineKeyboardButton("⬅⬅️ Volver a Categorías", callback_data="volver_categorias"),
            InlineKeyboardButton("🛒🛒🛒 Ver Carrito", callback_data="carrito")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"🍽🍽 *{categoria_nombre.upper()}*\nSelecciona un producto:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error al mostrar categoría: {e}")
        await query.edit_message_text("❌❌ Error al cargar la categoría.")

async def producto_callback(update: Update, context: CallbackContext) -> None:
    """Manejar clic en botón de producto"""
    query = update.callback_query
    await query.answer()
    
    producto_id = int(query.data.replace('producto_', ''))
    
    try:
        productos_categoria = context.user_data.get('productos_actuales', [])
        producto_seleccionado = None
        
        for producto in productos_categoria:
            if producto['id'] == producto_id:
                producto_seleccionado = producto
                break
        
        if not producto_seleccionado:
            await query.edit_message_text("❌❌ Producto no encontrado.")
            return
        
        # Guardar producto seleccionado temporalmente
        context.user_data['producto_seleccionado'] = producto_seleccionado
        
        # Crear botones de cantidad
        keyboard = []
        
        # Cantidades predefinidas
        cantidades = [1, 2, 3, 5]
        for cantidad in cantidades:
            keyboard.append([InlineKeyboardButton(
                f"Agregar {cantidad}", 
                callback_data=f"cantidad_{cantidad}"
            )])
        
        # Botones de navegación
        keyboard.append([
            InlineKeyboardButton("⬅⬅️ Volver a Productos", callback_data=f"categoria_{context.user_data.get('ultima_categoria', '')}"),
            InlineKeyboardButton("🛒🛒🛒 Ver Carrito", callback_data="carrito")
        ])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        nombre = producto_seleccionado.get('name', 'Sin nombre')
        precio = producto_seleccionado.get('price', 0)
        descripcion = producto_seleccionado.get('description', '')
        
        mensaje = f"🍽🍽 *{nombre}*\n"
        mensaje += f"💰 Precio: ${precio:.2f}\n"
        if descripcion:
            mensaje += f"📝📝 {descripcion}\n"
        mensaje += "\nSelecciona la cantidad:"
        
        await query.edit_message_text(
            mensaje,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error al seleccionar producto: {e}")
        await query.edit_message_text("❌❌ Error al seleccionar el producto.")

async def cantidad_callback(update: Update, context: CallbackContext) -> None:
    """Manejar selección de cantidad"""
    query = update.callback_query
    await query.answer()
    
    cantidad = int(query.data.replace('cantidad_', ''))
    
    try:
        producto_seleccionado = context.user_data.get('producto_seleccionado')
        
        if not producto_seleccionado:
            await query.edit_message_text("❌❌ No hay producto seleccionado.")
            return
        
        nombre = producto_seleccionado.get('name', 'Sin nombre')
        precio = producto_seleccionado.get('price', 0)
        
        # Inicializar carrito si no existe
        if 'carrito' not in context.user_data:
            context.user_data['carrito'] = []
        
        # Buscar si ya existe en el carrito
        encontrado = False
        for item in context.user_data['carrito']:
            if item['id'] == producto_seleccionado['id']:
                item['cantidad'] += cantidad
                encontrado = True
                break
        
        if not encontrado:
            context.user_data['carrito'].append({
                'id': producto_seleccionado['id'],
                'nombre': nombre,
                'precio': precio,
                'cantidad': cantidad
            })
        
        # Limpiar producto seleccionado
        context.user_data['producto_seleccionado'] = None
        
        # Crear botones para continuar
        keyboard = [
            [InlineKeyboardButton("📁📁 Seguir Comprando", callback_data="volver_categorias")],
            [InlineKeyboardButton("🛒🛒🛒 Ver Carrito", callback_data="carrito")],
            [InlineKeyboardButton("✅ Confirmar Pedido", callback_data="confirmar_pedido")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✅ *{nombre}*\n"
            f"📦📦 Cantidad: {cantidad}\n"
            f"💰 Total: ${precio * cantidad:.2f}\n\n"
            f"¡Añadido al carrito correctamente!",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error al agregar al carrito: {e}")
        await query.edit_message_text("❌❌ Error al agregar al carrito.")

async def carrito_handler(update: Update, context: CallbackContext) -> None:
    """Ver contenido del carrito"""
    await mostrar_carrito(update.message, context)

async def mostrar_carrito(message, context: CallbackContext):
    """Función auxiliar para mostrar carrito"""
    try:
        if 'carrito' not in context.user_data or not context.user_data['carrito']:
            keyboard = [[InlineKeyboardButton("📁📁 Ver Menú", callback_data="volver_categorias")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await message.reply_text(
                "🛒🛒🛒 Tu carrito está vacío.\n\n"
                "¡Agrega algunos productos del menú!",
                reply_markup=reply_markup
            )
            return
        
        carrito = context.user_data['carrito']
        
        total = 0
        response = "🛒🛒🛒 *TU CARRITO*\n\n"
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        
        for i, item in enumerate(carrito, 1):
            subtotal = item['precio'] * item['cantidad']
            total += subtotal
            response += f"`{i}.` *{item['nombre']}*\n"
            response += f"    {item['cantidad']} x ${item['precio']:.2f} = ${subtotal:.2f}\n\n"
        
        response += "━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        response += f"💰 *TOTAL: ${total:.2f}*\n\n"
        response += "📍 *Mesa:* " + context.user_data.get('mesa_actual', 'No registrada')
        
        # Crear botones para el carrito
        keyboard = [
            [InlineKeyboardButton("📁📁 Seguir Comprando", callback_data="volver_categorias")],
            [InlineKeyboardButton("🗑🗑 Vaciar Carrito", callback_data="vaciar_carrito")],
            [InlineKeyboardButton("✅ Confirmar Pedido", callback_data="confirmar_pedido")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await message.reply_text(
            response,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error al ver carrito: {e}")
        await message.reply_text("❌❌ Error al cargar el carrito.")

async def pedir_handler(update: Update, context: CallbackContext, db) -> None:
    """Confirmar y enviar el pedido"""
    await confirmar_pedido(update.message, context, db)

async def confirmar_pedido(message, context: CallbackContext, db):
    """Función auxiliar para confirmar pedido"""
    try:
        if 'carrito' not in context.user_data or not context.user_data['carrito']:
            await message.reply_text("❌❌ Tu carrito está vacío.")
            return
        
        if 'mesa_actual' not in context.user_data:
            await message.reply_text("❌❌ Primero necesitas registrar una mesa.")
            return
        
        # Pedir nombre del cliente si no está en user_data
        if 'nombre_cliente' not in context.user_data:
            context.user_data['pendiente_confirmacion'] = True
            await message.reply_text(
                "📝📝 Por favor, ingresa tu nombre para el pedido:"
            )
            return
        
        # Crear pedido en la base de datos
        pedido_id = db.create_order(
            user_id=message.from_user.id,
            mesa=context.user_data['mesa_actual'],
            nombre_cliente=context.user_data['nombre_cliente'],
            items=context.user_data['carrito'],
            total=sum(item['precio'] * item['cantidad'] for item in context.user_data['carrito'])
        )
        
        # Limpiar carrito después de confirmar
        context.user_data['carrito'] = []
        
        await message.reply_text(
            f"✅✅ *Pedido confirmado!*\n\n"
            f"📋 Número de pedido: *{pedido_id}*\n"
            f"👤 Cliente: *{context.user_data['nombre_cliente']}*\n"
            f"📍 Mesa: *{context.user_data['mesa_actual']}*\n\n"
            f"¡Tu pedido está en camino! 🚀",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error al confirmar pedido: {e}")
        await message.reply_text("❌❌ Error al confirmar el pedido.")

async def limpiar_handler(update: Update, context: CallbackContext) -> None:
    """Vaciar el carrito"""
    if 'carrito' in context.user_data:
        context.user_data['carrito'] = []
        await update.message.reply_text("🗑🗑 Carrito vaciado correctamente.")
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
            "Usa /menu para ver el menú"
        )

# Manejadores adicionales para botones especiales
async def carrito_callback(update: Update, context: CallbackContext) -> None:
    """Manejar clic en botón de carrito"""
    query = update.callback_query
    await query.answer()
    await mostrar_carrito(query.message, context)

async def volver_categorias_callback(update: Update, context: CallbackContext, db) -> None:
    """Manejar clic en botón de volver a categorías"""
    query = update.callback_query
    await query.answer()
    await menu_handler_from_callback(query, context, db)

async def menu_handler_from_callback(query, context: CallbackContext, db):
    """Mostrar menú desde callback"""
    try:
        # Obtener productos de la base de datos
        products = db.get_products()
        
        if not products:
            await query.edit_message_text("📭📭 El menú está vacío en este momento.")
            return
        
        from collections import defaultdict
        # Agrupar por categoría
        by_category = defaultdict(list)
        for product in products:
            category = product.get('category', 'General')
            by_category[category].append(product)
        
        # Crear botones para categorías
        keyboard = []
        categories_list = list(by_category.keys())
        
        for category in categories_list:
            count = len(by_category[category])
            keyboard.append([InlineKeyboardButton(
                f"{category} ({count} productos)", 
                callback_data=f"categoria_{category}"
            )])
        
        keyboard.append([InlineKeyboardButton("🛒🛒🛒 Ver Carrito", callback_data="carrito")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            "📁📁 *SELECCIONA UNA CATEGORÍA*",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Error al mostrar menú: {e}")
        await query.edit_message_text("❌❌ Error al cargar el menú.")