# main.py
from bot import RestaurantBot
from config import Config

def main():
    # Validar configuración
    try:
        Config.validate()
    except ValueError as e:
        print(f"❌ Error de configuración: {e}")
        return
    
    # Crear y ejecutar el bot
    bot = RestaurantBot()
    print("🤖 Bot iniciado. Presiona Ctrl+C para detener.")
    bot.run()

if __name__ == '__main__':
    main()