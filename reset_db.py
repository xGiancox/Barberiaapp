from app import app, db, User
from datetime import datetime

def reset_database():
    with app.app_context():
        print("🔄 Reiniciando base de datos...")
        
        # Eliminar todas las tablas
        db.drop_all()
        
        # Crear tablas nuevamente
        db.create_all()
        
        # Crear usuario jefe
        jefe = User(
            email='jefe@barberia.com', 
            name='Jefe Principal', 
            role='jefe'
        )
        jefe.set_password('admin123')
        db.session.add(jefe)
        
        db.session.commit()
        print("✅ Base de datos reiniciada correctamente")
        print("📧 Usuario jefe: jefe@barberia.com")
        print("🔑 Contraseña: admin123")

if __name__ == '__main__':
    reset_database()
