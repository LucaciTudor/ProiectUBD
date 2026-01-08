from flask import Flask, render_template, request, redirect, url_for, Blueprint
from flask_login import LoginManager, login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Student, Profesor, Disciplina
from curriculum_data import seed_discipline
from auth_routes import auth_bp
from chat_routes import chat_bp
from academic_routes import academic_bp
from admin_routes import admin_bp
from sqlalchemy import or_
import os

# --- CONFIGURARE ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cheie_secreta_proiect_licenta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog_scoala.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configurare Uploads
UPLOAD_FOLDER = os.path.join('static', 'uploads')
CHAT_UPLOAD_FOLDER = os.path.join('static', 'chat_uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHAT_UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['CHAT_UPLOAD_FOLDER'] = CHAT_UPLOAD_FOLDER

# Inițializare baza de date
db.init_app(app)

# Configurare Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Înregistrare Blueprint-uri
app.register_blueprint(auth_bp)
app.register_blueprint(chat_bp)
app.register_blueprint(academic_bp)
app.register_blueprint(admin_bp)

@app.before_request
def before_request():
    # Previne cache-ul pentru paginile protejate
    if current_user.is_authenticated and request.endpoint not in ['auth.login', 'auth.register', 'static']:
        pass  # Utilizatorul este autentificat, permite accesul
    elif request.endpoint not in ['auth.login', 'auth.register', 'auth.forgot_password', 'auth.reset_password', 'setup_admin', 'static'] and not current_user.is_authenticated:
        return redirect(url_for('auth.login'))

@app.after_request
def after_request(response):
    # Adaugă header-e pentru a preveni cache-ul pe paginile protejate
    if current_user.is_authenticated and request.endpoint not in ['static']:
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'
    return response

# --- RUTE PRINCIPALE ---
@app.route('/setup_admin')
def setup_admin():
    if not User.query.filter_by(username='admin').first():
        admin_user = User(
            username='admin', 
            email='admin@uoradea.ro', 
            password=generate_password_hash('admin123'), 
            role='admin', 
            is_approved=True
        )
        db.session.add(admin_user)
        db.session.commit()
        return "Admin creat cu succes!"
    return "Admin există deja."

@app.route('/')
@login_required
def index():
    if current_user.role == 'student': 
        s = Student.query.filter_by(user_id=current_user.id).first()
        if s:
            return redirect(url_for('academic.raport_student_general', student_id=s.id_student))
        else:
            return "Cont incomplet - contactați administratorul"
    
    if current_user.role == 'profesor':
        prof = Profesor.query.filter_by(user_id=current_user.id).first()
        materii = []
        
        if prof:
            materii = Disciplina.query.filter(
                or_(
                    Disciplina.id_titular == prof.id_profesor, 
                    Disciplina.id_laborant == prof.id_profesor, 
                    Disciplina.id_seminarist == prof.id_profesor, 
                    Disciplina.id_proiectant == prof.id_profesor
                )
            ).all()
        
        return render_template('index_profesor.html', materii=materii, profesor=prof)
    
    # Admin dashboard
    studenti = Student.query.outerjoin(User).filter(User.is_approved == True).all()
    profesori = Profesor.query.outerjoin(User).filter(User.is_approved == True).all()
    
    return render_template('index.html', studenti=studenti, profesori=profesori)

if __name__ == '__main__':
    with app.app_context(): 
        db.create_all()
        seed_discipline()
    app.run(debug=True)