# test_connection.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from database import Database

def test_database_connection():
    print("🧪 Probando conexión a Supabase...")
    
    # 1. Validar configuración
    try:
        Config.validate()
        print("✅ Configuración válida")
    except ValueError as e:
        print(f"❌ Error en configuración: {e}")
        return
    
    # 2. Probar conexión
    try:
        db = Database()
        print("✅ Instancia de base de datos creada")
        
        # 3. Probar consulta simple
        print("🧪 Probando consulta a la base de datos...")
        test_result = db.test_connection()
        
        if test_result:
            print("✅ Conexión a base de datos exitosa")
        else:
            print("❌ No se pudo conectar a la base de datos")
            return
        
        # 4. Probar obtener productos
        print("🧪 Probando obtener productos...")
        products = db.get_all_products()
        print(f"✅ Se encontraron {len(products)} productos")
        
        # 5. Probar obtener usuarios
        print("🧪 Probando obtener usuarios...")
        users = db.get_all_users()
        print(f"✅ Se encontraron {len(users)} usuarios")
        
        # 6. Probar categorías
        print("🧪 Probando obtener categorías...")
        categories = db.get_categories()
        print(f"✅ Categorías encontradas: {', '.join(categories) if categories else 'Ninguna'}")
        
        print("\n🎉 ¡Todas las pruebas pasaron!")
        
    except Exception as e:
        print(f"❌ Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_database_connection()