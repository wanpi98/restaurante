import json
import random
import datetime
from typing import List, Dict, Any, Optional
from supabase import create_client, Client
from config import Config

class Database:
    _instance = None
    _client: Client = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Inicializar conexión a Supabase"""
        try:
            self._client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)
            print("✅ Conexión a Supabase establecida")
        except Exception as e:
            print(f"❌ Error conectando a Supabase: {e}")
            raise
    
    # ===== USUARIOS =====
    def get_user(self, telegram_id: int) -> Optional[Dict]:
        """Obtener usuario por Telegram ID"""
        try:
            response = self._client.table("users")\
                .select("*")\
                .eq("telegram_id", telegram_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al obtener usuario: {e}")
            return None
    
    def get_or_create_user(self, telegram_id: int, full_name: str, role: str = "cliente") -> Dict:
        """Obtener o crear usuario si no existe"""
        try:
            # ✅ CORREGIDO: Usar self._client
            response = self._client.table("users")\
                .select("*")\
                .eq("telegram_id", telegram_id)\
                .execute()
            
            if response.data:
                return response.data[0]
            
            # Crear nuevo usuario
            user_data = {
                "telegram_id": telegram_id,
                "full_name": full_name,
                "role": role
            }
            
            # ✅ CORREGIDO: Usar self._client
            response = self._client.table("users")\
                .insert(user_data)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"❌ Error al crear usuario: {e}")
            return None
    
    # ===== PRODUCTOS =====
    def get_all_products(self, available_only: bool = True) -> List[Dict]:
        """Obtener todos los productos"""
        try:
            query = self._client.table("products").select("*")
            
            if available_only:
                query = query.eq("is_available", True)
            
            response = query.order("category").order("name").execute()
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener productos: {e}")
            return []
    
    def get_products(self, product_id: int) -> Optional[Dict]:
        """Obtener un producto por ID"""
        try:
            response = self._client.table("products")\
                .select("*")\
                .eq("id", product_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al obtener producto: {e}")
            return None
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Obtener productos por categoría"""
        try:
            response = self._client.table("products")\
                .select("*")\
                .eq("category", category)\
                .eq("is_available", True)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener productos por categoría: {e}")
            return []
            
    # ===== PEDIDOS =====
    def generate_order_code(self) -> str:
        """Generar código único para pedido"""
        date_str = datetime.datetime.now().strftime("%y%m%d")
        random_str = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=4))
        return f"{date_str}-{random_str}"
    
    def create_order(self, telegram_id: int, table_number: str, 
                    items: List[Dict], notes: str = "") -> Optional[Dict]:
        """Crear nuevo pedido - CORREGIDO"""
        try:
            user = self.get_user(telegram_id)
            if not user:
                print("❌ Usuario no encontrado")
                return None
            
            # Calcular total y formatear items
            total = 0
            order_items = []
            
            for item in items:
                # ✅ CORREGIDO: Usar 'id' en lugar de 'product_id'
                product_id = item.get('id')
                if not product_id:
                    continue
                    
                product = self.get_products(product_id)
                if product:
                    # Formatear item para la base de datos
                    order_item = {
                        'product_id': product_id,
                        'product_name': product.get('name', 'Sin nombre'),
                        'unit_price': product.get('price', 0),
                        'quantity': item.get('cantidad', 1)
                    }
                    order_items.append(order_item)
                    
                    # Calcular subtotal
                    total += product['price'] * item.get('cantidad', 1)
            
            order_data = {
                "order_code": self.generate_order_code(),
                "telegram_id": telegram_id,
                "table_number": table_number,
                "items": json.dumps(order_items, ensure_ascii=False),
                "total": total,
                "status": "pendiente",
                "notes": notes
            }
            
            response = self._client.table("orders")\
                .insert(order_data)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"❌ Error al crear pedido: {e}")
            return None
    
    def get_pending_orders(self) -> List[Dict]:
        """Obtener pedidos pendientes"""
        return self.get_orders_by_status("pendiente")
    
    def get_orders_by_status(self, status: str) -> List[Dict]:
        """Obtener pedidos por estado"""
        try:
            response = self._client.table("orders")\
                .select("*")\
                .eq("status", status)\
                .order("created_at", desc=True)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener pedidos: {e}")
            return []