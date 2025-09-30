from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from functools import wraps
import os
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuración para producción/desarrollo
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'barberapp_secret_key_2024')

# Configuración de base de datos mejorada
if os.environ.get('DATABASE_URL'):
    # PostgreSQL en producción (Render)
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL').replace('postgres://', 'postgresql://')
else:
    # SQLite en desarrollo
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_recycle': 300,
    'pool_pre_ping': True
}

db = SQLAlchemy(app)

# Modelos
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='barbero')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    cuts = db.relationship('HairCut', backref='barber', lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class HairCut(db.Model):
    __tablename__ = 'hair_cuts'
    id = db.Column(db.Integer, primary_key=True)
    date_cut = db.Column(db.Date, nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total = db.Column(db.Float, nullable=False)
    divided_total = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class MonthlyExpense(db.Model):
    __tablename__ = 'monthly_expenses'
    id = db.Column(db.Integer, primary_key=True)
    month_year = db.Column(db.String(7), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ProductSale(db.Model):
    __tablename__ = 'product_sales'
    id = db.Column(db.Integer, primary_key=True)
    date_sale = db.Column(db.Date, nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    product_name = db.Column(db.String(200), nullable=False)
    price = db.Column(db.Float, nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    total = db.Column(db.Float, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

# Decoradores
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def jefe_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        user = User.query.get(session['user_id'])
        if user.role != 'jefe':
            flash('No tienes permisos para acceder a esta página', 'error')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated_function

# Ruta principal
@app.route('/')
def index():
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user.role == 'jefe':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Ruta de login (CORREGIDA)
@app.route('/login', methods=['GET', 'POST'])
def login():
    try:
        if request.method == 'POST':
            email = request.form['email']
            password = request.form['password']
            
            logger.info(f"Intento de login para: {email}")
            
            user = User.query.filter_by(email=email).first()
            
            if user and user.check_password(password):
                session['user_id'] = user.id
                session['user_name'] = user.name
                session['user_role'] = user.role
                
                logger.info(f"Login exitoso: {user.name} ({user.role})")
                
                if user.role == 'jefe':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Email o contraseña incorrectos', 'error')
                logger.warning(f"Login fallido para: {email}")
        
        return render_template('login.html')
        
    except Exception as e:
        logger.error(f"Error en login: {str(e)}")
        flash('Error interno del servidor. Por favor intenta nuevamente.', 'error')
        return render_template('login.html')

# Ruta de dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    try:
        user = User.query.get(session['user_id'])
        today = date.today()
        today_cuts = HairCut.query.filter_by(user_id=user.id, date_cut=today).all()
        
        daily_total = sum(cut.total for cut in today_cuts)
        daily_divided = sum(cut.divided_total for cut in today_cuts)
        
        week_ago = today - timedelta(days=7)
        weekly_cuts = HairCut.query.filter(
            HairCut.user_id == user.id,
            HairCut.date_cut >= week_ago
        ).all()
        
        weekly_total = sum(cut.total for cut in weekly_cuts)
        weekly_divided = sum(cut.divided_total for cut in weekly_cuts)
        
        two_weeks_ago = today - timedelta(days=14)
        biweekly_cuts = HairCut.query.filter(
            HairCut.user_id == user.id,
            HairCut.date_cut >= two_weeks_ago
        ).all()
        
        biweekly_total = sum(cut.total for cut in biweekly_cuts)
        biweekly_divided = sum(cut.divided_total for cut in biweekly_cuts)
        
        return render_template('dashboard.html',
                             user=user,
                             today_cuts=today_cuts,
                             daily_total=daily_total,
                             daily_divided=daily_divided,
                             weekly_total=weekly_total,
                             weekly_divided=weekly_divided,
                             biweekly_total=biweekly_total,
                             biweekly_divided=biweekly_divided)
                             
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        flash('Error al cargar el dashboard', 'error')
        return redirect(url_for('login'))

# [MANTENER TODAS LAS DEMÁS RUTAS EXACTAMENTE COMO LAS TENÍAS]
# ... pega aquí el resto de tus rutas ...

@app.route('/register', methods=['GET', 'POST'])
@jefe_required
def register():
    if request.method == 'POST':
        try:
            email = request.form['email']
            name = request.form['name']
            password = request.form['password']
            role = request.form['role']
            
            if User.query.filter_by(email=email).first():
                flash('El email ya está registrado', 'error')
                return render_template('register.html')
            
            user = User(email=email, name=name, role=role)
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('admin_users'))
            
        except Exception as e:
            flash('Error al crear usuario: ' + str(e), 'error')
    
    return render_template('register.html')

@app.route('/add_cut', methods=['GET', 'POST'])
@login_required
def add_cut():
    if request.method == 'POST':
        try:
            date_cut_str = request.form['date_cut']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            
            date_cut = datetime.strptime(date_cut_str, '%Y-%m-%d').date()
            total = price * quantity
            
            user = User.query.get(session['user_id'])
            if user.role == 'jefe':
                divided_total = total
            else:
                divided_total = total / 2
            
            cut = HairCut(
                date_cut=date_cut,
                price=price,
                quantity=quantity,
                total=total,
                divided_total=divided_total,
                user_id=session['user_id']
            )
            
            db.session.add(cut)
            db.session.commit()
            
            flash('Corte registrado exitosamente', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash('Error al registrar el corte: ' + str(e), 'error')
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    return render_template('add_cut.html', current_date=current_date)

# ... continúa con todas tus otras rutas ...

@app.route('/admin/product_sales', methods=['GET', 'POST'])
@jefe_required
def admin_product_sales():
    if request.method == 'POST':
        try:
            date_sale_str = request.form['date_sale']
            product_name = request.form['product_name']
            price = float(request.form['price'])
            quantity = int(request.form['quantity'])
            
            date_sale = datetime.strptime(date_sale_str, '%Y-%m-%d').date()
            total = price * quantity
            
            sale = ProductSale(
                date_sale=date_sale,
                product_name=product_name,
                price=price,
                quantity=quantity,
                total=total,
                created_by=session['user_id']
            )
            
            db.session.add(sale)
            db.session.commit()
            
            flash('Venta de producto registrada exitosamente', 'success')
            return redirect(url_for('admin_product_sales'))
            
        except Exception as e:
            flash('Error al registrar la venta: ' + str(e), 'error')
    
    product_sales = ProductSale.query.order_by(ProductSale.date_sale.desc()).all()
    
    today = date.today()
    today_sales = ProductSale.query.filter_by(date_sale=today).all()
    today_total = sum(sale.total for sale in today_sales)
    
    month_sales = ProductSale.query.filter(
        ProductSale.date_sale >= date(today.year, today.month, 1)
    ).all()
    month_total = sum(sale.total for sale in month_sales)
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    return render_template('admin_product_sales.html',
                         product_sales=product_sales,
                         today_total=today_total,
                         month_total=month_total,
                         current_date=current_date)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/manifest.json')
def manifest():
    return app.send_static_file('manifest.json')

# Función para inicializar la base de datos
def init_db():
    with app.app_context():
        try:
            db.create_all()
            logger.info("✅ Tablas creadas exitosamente")
            
            # Crear usuario jefe por defecto si no existe
            if not User.query.filter_by(role='jefe').first():
                jefe = User(
                    email='jefe@barberia.com', 
                    name='Jefe Principal', 
                    role='jefe'
                )
                jefe.set_password('admin123')
                db.session.add(jefe)
                db.session.commit()
                logger.info("✅ Usuario jefe creado: jefe@barberia.com / admin123")
            
            logger.info("✅ Base de datos inicializada correctamente")
            
        except Exception as e:
            logger.error(f"❌ Error inicializando base de datos: {str(e)}")

# Inicializar la base de datos al iniciar
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
