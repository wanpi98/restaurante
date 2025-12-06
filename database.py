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
    
    # ===== MÉTODOS GENERALES =====
    def test_connection(self):
        """Probar conexión a la base de datos"""
        try:
            response = self._client.table("users").select("count", count="exact").limit(1).execute()
            print("✅ Conexión a base de datos verificada")
            return True
        except Exception as e:
            print(f"❌ Error en conexión: {e}")
            return False
    
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
            # Intentar obtener usuario existente
            response = self.supabase.table("users")\
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
            
            response = self.supabase.table("users")\
                .insert(user_data)\
                .execute()
            
            return response.data[0] if response.data else None
            
        except Exception as e:
            print(f"❌ Error al crear usuario: {e}")
            return None
        
    def update_user_role(self, telegram_id: int, role: str) -> Optional[Dict]:
        """Actualizar rol de usuario (solo admin)"""
        try:
            response = self._client.table("users")\
                .update({"role": role})\
                .eq("telegram_id", telegram_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al actualizar rol: {e}")
            return None
    
    def update_user_status(self, telegram_id: int, is_active: bool) -> Optional[Dict]:
        """Actualizar estado de actividad de usuario"""
        update_data = {"is_active": is_active}
        
        if is_active:
            update_data["last_active"] = datetime.datetime.now().isoformat()
        
        try:
            response = self._client.table("users")\
                .update(update_data)\
                .eq("telegram_id", telegram_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al actualizar estado: {e}")
            return None
    
    def get_active_attendants(self) -> List[Dict]:
        """Obtener dependientes activos"""
        try:
            response = self._client.table("users")\
                .select("*")\
                .eq("role", "dependiente")\
                .eq("is_active", True)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener dependientes activos: {e}")
            return []
    
    def get_all_attendants(self) -> List[Dict]:
        """Obtener todos los dependientes"""
        try:
            response = self._client.table("users")\
                .select("*")\
                .eq("role", "dependiente")\
                .order("full_name")\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener dependientes: {e}")
            return []
    
    def get_all_users(self) -> List[Dict]:
        """Obtener todos los usuarios (solo admin)"""
        try:
            response = self._client.table("users")\
                .select("*")\
                .order("created_at", desc=True)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener usuarios: {e}")
            return []
    
    # ===== PRODUCTOS =====
    def get_product(self, product_id: int) -> Optional[Dict]:
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
    
    def get_products_by_category(self, category: str) -> List[Dict]:
        """Obtener productos por categoría"""
        try:
            response = self._client.table("products")\
                .select("*")\
                .eq("category", category)\
                .eq("is_available", True)\
                .order("name")\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener productos por categoría: {e}")
            return []
    
    def create_product(self, name: str, price: float, category: str, 
                      description: str = None) -> Optional[Dict]:
        """Crear nuevo producto"""
        try:
            product_data = {
                "name": name,
                "price": price,
                "category": category,
                "is_available": True
            }
            
            if description:
                product_data["description"] = description
            
            response = self._client.table("products")\
                .insert(product_data)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al crear producto: {e}")
            return None
    
    def update_product(self, product_id: int, **kwargs) -> Optional[Dict]:
        """Actualizar producto"""
        try:
            response = self._client.table("products")\
                .update(kwargs)\
                .eq("id", product_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al actualizar producto: {e}")
            return None
    
    def toggle_product_availability(self, product_id: int) -> Optional[Dict]:
        """Activar/desactivar producto"""
        product = self.get_product(product_id)
        if not product:
            return None
        
        new_status = not product.get("is_available", True)
        
        try:
            response = self._client.table("products")\
                .update({"is_available": new_status})\
                .eq("id", product_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al cambiar estado del producto: {e}")
            return None
    
    def delete_product(self, product_id: int) -> bool:
        """Eliminar producto permanentemente (cuidado)"""
        try:
            response = self._client.table("products")\
                .delete()\
                .eq("id", product_id)\
                .execute()
            
            return len(response.data) > 0
        except Exception as e:
            print(f"❌ Error al eliminar producto: {e}")
            return False
    
    def get_categories(self) -> List[str]:
        """Obtener lista de categorías únicas"""
        try:
            response = self._client.table("products")\
                .select("category")\
                .execute()
            
            # Extraer categorías únicas
            categories = set()
            for product in response.data:
                if product.get("category"):
                    categories.add(product["category"])
            
            return sorted(list(categories))
        except Exception as e:
            print(f"❌ Error al obtener categorías: {e}")
            return []
    
    # ===== PEDIDOS =====
    def generate_order_code(self) -> str:
        """Generar código único para pedido"""
        date_str = datetime.datetime.now().strftime("%y%m%d")
        random_str = ''.join(random.choices('ABCDEFGHJKLMNPQRSTUVWXYZ23456789', k=4))
        return f"{date_str}-{random_str}"
    
    def create_order(self, telegram_id: int, table_number: str, 
                    items: List[Dict], notes: str = "") -> Optional[Dict]:
        """Crear nuevo pedido"""
        try:
            # Obtener usuario
            user = self.get_user(telegram_id)
            if not user:
                print("❌ Usuario no encontrado")
                return None
            
            # Calcular total
            total = 0
            for item in items:
                product = self.get_product(item.get("product_id"))
                if product:
                    item["unit_price"] = product["price"]
                    item["product_name"] = product["name"]
                    total += product["price"] * item.get("quantity", 1)
            
            order_data = {
                "order_code": self.generate_order_code(),
                "telegram_id": telegram_id,
                "table_number": table_number,
                "items": json.dumps(items, ensure_ascii=False),
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
    
    def get_order(self, order_id: int) -> Optional[Dict]:
        """Obtener pedido por ID"""
        try:
            response = self._client.table("orders")\
                .select("*")\
                .eq("id", order_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al obtener pedido: {e}")
            return None
    
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
    
    def get_pending_orders(self) -> List[Dict]:
        """Obtener pedidos pendientes"""
        return self.get_orders_by_status("pendiente")
    
    def get_preparing_orders(self) -> List[Dict]:
        """Obtener pedidos en preparación"""
        return self.get_orders_by_status("preparando")
    
    def get_ready_orders(self) -> List[Dict]:
        """Obtener pedidos listos"""
        return self.get_orders_by_status("listo")
    
    def update_order_status(self, order_id: int, status: str) -> Optional[Dict]:
        """Actualizar estado de un pedido"""
        valid_statuses = ["pendiente", "confirmado", "preparando", "listo", "entregado", "cancelado"]
        
        if status not in valid_statuses:
            print(f"❌ Estado no válido: {status}")
            return None
        
        try:
            response = self._client.table("orders")\
                .update({"status": status})\
                .eq("id", order_id)\
                .execute()
            
            return response.data[0] if response.data else None
        except Exception as e:
            print(f"❌ Error al actualizar pedido: {e}")
            return None
    
    def get_user_orders(self, telegram_id: int, limit: int = 10) -> List[Dict]:
        """Obtener pedidos de un usuario"""
        try:
            response = self._client.table("orders")\
                .select("*")\
                .eq("telegram_id", telegram_id)\
                .order("created_at", desc=True)\
                .limit(limit)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener pedidos del usuario: {e}")
            return []
    
    def get_todays_orders(self) -> List[Dict]:
        """Obtener pedidos de hoy"""
        try:
            today = datetime.datetime.now().strftime("%Y-%m-%d")
            response = self._client.table("orders")\
                .select("*")\
                .gte("created_at", f"{today} 00:00:00")\
                .lte("created_at", f"{today} 23:59:59")\
                .order("created_at", desc=True)\
                .execute()
            
            return response.data
        except Exception as e:
            print(f"❌ Error al obtener pedidos de hoy: {e}")
            return []
    
    # ===== ESTADÍSTICAS =====
    def get_daily_stats(self, date: str = None) -> Dict[str, Any]:
        """Obtener estadísticas del día"""
        if not date:
            date = datetime.datetime.now().strftime("%Y-%m-%d")
        
        try:
            # Total pedidos
            orders_response = self._client.table("orders")\
                .select("id", count="exact")\
                .gte("created_at", f"{date} 00:00:00")\
                .lte("created_at", f"{date} 23:59:59")\
                .execute()
            
            # Total ventas
            revenue_response = self._client.table("orders")\
                .select("total")\
                .gte("created_at", f"{date} 00:00:00")\
                .lte("created_at", f"{date} 23:59:59")\
                .execute()
            
            total_orders = orders_response.count or 0
            total_revenue = sum(order["total"] for order in revenue_response.data)
            
            # Pedidos por estado
            status_response = self._client.table("orders")\
                .select("status", count="exact")\
                .gte("created_at", f"{date} 00:00:00")\
                .lte("created_at", f"{date} 23:59:59")\
                .execute()
            
            status_counts = {}
            if hasattr(status_response, 'data'):
                for order in status_response.data:
                    status = order.get("status", "desconocido")
                    status_counts[status] = status_counts.get(status, 0) + 1
            
            return {
                "date": date,
                "total_orders": total_orders,
                "total_revenue": total_revenue,
                "status_counts": status_counts,
                "avg_order_value": total_revenue / total_orders if total_orders > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ Error al obtener estadísticas: {e}")
            return {}
    
    def get_top_products(self, limit: int = 5, days: int = 30) -> List[Dict]:
        """Obtener productos más vendidos"""
        try:
            # Obtener pedidos de los últimos N días
            start_date = (datetime.datetime.now() - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
            
            response = self._client.table("orders")\
                .select("items")\
                .gte("created_at", f"{start_date} 00:00:00")\
                .execute()
            
            # Contar productos
            product_counts = {}
            for order in response.data:
                try:
                    items = json.loads(order.get("items", "[]"))
                    for item in items:
                        product_id = item.get("product_id")
                        quantity = item.get("quantity", 1)
                        
                        if product_id:
                            if product_id not in product_counts:
                                product_counts[product_id] = {
                                    "product_id": product_id,
                                    "total_quantity": 0,
                                    "product_name": item.get("product_name", f"Producto {product_id}")
                                }
                            product_counts[product_id]["total_quantity"] += quantity
                except:
                    continue
            
            # Ordenar y limitar
            top_products = sorted(product_counts.values(), 
                                key=lambda x: x["total_quantity"], 
                                reverse=True)[:limit]
            
            return top_products
            
        except Exception as e:
            print(f"❌ Error al obtener productos más vendidos: {e}")
            return []