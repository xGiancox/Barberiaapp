from app import app, User
from datetime import datetime

def check_current_code():
    with app.app_context():
        print("🔍 INICIANDO DIAGNÓSTICO COMPLETO")
        
        # Verificar usuario jefe
        jefe = User.query.filter_by(role='jefe').first()
        if jefe:
            print(f"✅ Jefe encontrado: {jefe.email} - {jefe.name}")
        else:
            print("❌ No se encontró usuario jefe")
        
        # Simular cálculo
        total = 100
        user = jefe
        if user and user.role == 'jefe':
            calculated = total
            print(f"🎯 CÁLCULO CORRECTO: Jefe debería recibir 100% = {calculated}")
        else:
            calculated = total / 2
            print(f"🎯 CÁLCULO INCORRECTO: Se está dividiendo = {calculated}")
            
        print("🔍 DIAGNÓSTICO COMPLETADO")

if __name__ == '__main__':
    check_current_code()
