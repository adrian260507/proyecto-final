from app import create_app
import os
from models_bd import crear_tablas

app = create_app()

# --- ✅ Se ejecuta tanto en local como en Railway ---
try:
    print("🔄 Verificando estructura de la base de datos (modo Gunicorn)...")
    crear_tablas()
    print("✅ Base de datos verificada correctamente")
except Exception as e:
    print(f"⚠️ No se pudieron crear las tablas: {e}")

def verificar_y_crear_tablas():
    """Verifica y crea las tablas si no existen"""
    try:
        print("🔄 Verificando estructura de la base de datos...")
        crear_tablas()
        print("✅ Base de datos verificada y actualizada correctamente")
    except Exception as e:
        print(f"❌ Error al verificar la base de datos: {e}")
        raise

if __name__ == "__main__":
    verificar_y_crear_tablas()
    
    debug_mode = os.getenv("FLASK_DEBUG", "0") == "1"
    try:
        port = int(os.getenv("PORT", 5000))
        host = os.getenv("FLASK_HOST", "0.0.0.0")
        
        print(f"🚀 Iniciando aplicación en {host}:{port}")
        app.run(debug=debug_mode, host=host, port=port)
    except Exception as e:
        app.logger.error(f"Error al iniciar la aplicación: {e}")
        raise


