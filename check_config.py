from app import app
import os

print("🔍 VERIFICANDO CONFIGURACIÓN ACTUAL...")
print(f"📊 DATABASE_URL en Environment: {os.environ.get('DATABASE_URL', 'NO EXISTE')}")
print(f"📊 SQLALCHEMY_DATABASE_URI: {app.config.get('SQLALCHEMY_DATABASE_URI')}")

with app.app_context():
    from app import db
    print(f"📊 URL de conexión real: {db.engine.url}")
