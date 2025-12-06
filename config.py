import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

class Config:
    # Token del bot de Telegram
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    
    # Credenciales de Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Configuración de la aplicación
    DEBUG = os.getenv("DEBUG", "False").lower() == "true"
    
    # Validar que existan las variables críticas
    @classmethod
    def validate(cls):
        required_vars = ["BOT_TOKEN", "SUPABASE_URL", "SUPABASE_KEY"]
        missing = []
        
        for var in required_vars:
            if not getattr(cls, var):
                missing.append(var)
        
        if missing:
            raise ValueError(f"Faltan variables de entorno: {', '.join(missing)}")
        
        print("✅ Configuración cargada correctamente")
        return True