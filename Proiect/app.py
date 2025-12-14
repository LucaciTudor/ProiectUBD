from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import random
import io
import base64
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from sqlalchemy import or_

# --- CONFIGURARE ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cheie_secreta_proiect_licenta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog_scoala.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MODELE BAZA DE DATE ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    is_approved = db.Column(db.Boolean, default=False)
    
    student_profile = db.relationship('Student', backref='user_account', uselist=False, cascade="all, delete-orphan")
    profesor_profile = db.relationship('Profesor', backref='user_account', uselist=False, cascade="all, delete-orphan")

class Mesaj(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    fisier = db.Column(db.String(255), nullable=True)
    data_trimitere = db.Column(db.DateTime, default=datetime.now)
    
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')

class Profesor(db.Model):
    id_profesor = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(50), nullable=False)
    prenume = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    def get_full_name(self): return f"{self.nume} {self.prenume}"

class Disciplina(db.Model):
    id_disciplina = db.Column(db.Integer, primary_key=True)
    nume_disciplina = db.Column(db.String(100), nullable=False)
    credite = db.Column(db.Integer, nullable=False)
    an_studiu = db.Column(db.Integer, nullable=False) 
    specializare = db.Column(db.String(50), nullable=False)
    semestru = db.Column(db.Integer, nullable=False) 
    
    id_titular = db.Column(db.Integer, db.ForeignKey('profesor.id_profesor'), nullable=True)
    id_laborant = db.Column(db.Integer, db.ForeignKey('profesor.id_profesor'), nullable=True)
    
    pondere_examen = db.Column(db.Integer, default=60)
    pondere_laborator = db.Column(db.Integer, default=40)

    note = db.relationship('Notare', backref='disciplina', lazy=True)
    evaluari = db.relationship('EvaluareProgramata', backref='disciplina', lazy=True)
    
    def get_full_name(self): return self.nume_disciplina

class EvaluareProgramata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    tip = db.Column(db.String(50), nullable=False)
    data_evaluare = db.Column(db.Date, nullable=False)

class Student(db.Model):
    id_student = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(50), nullable=False)
    prenume = db.Column(db.String(50), nullable=False)
    nr_matricol = db.Column(db.String(20), unique=True, nullable=False)
    grupa = db.Column(db.String(10), nullable=False)
    an_studiu = db.Column(db.Integer, nullable=False, default=1)
    specializare = db.Column(db.String(50), nullable=False, default='Calculatoare')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    
    def get_full_name(self): return f"{self.nume} {self.prenume}"

class Notare(db.Model):
    id_notare = db.Column(db.Integer, primary_key=True)
    id_student = db.Column(db.Integer, db.ForeignKey('student.id_student'), nullable=False)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    tip_activitate = db.Column(db.String(20), nullable=False) 
    nota = db.Column(db.Float, nullable=False) 
    data_notare = db.Column(db.Date, nullable=False, default=date.today)

class Prezenta(db.Model):
    id_prezenta = db.Column(db.Integer, primary_key=True)
    id_student = db.Column(db.Integer, db.ForeignKey('student.id_student'), nullable=False)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    data_curs = db.Column(db.Date, nullable=False, default=date.today)

# --- POPULARE CURICULA ---
def seed_discipline():
    if Disciplina.query.first(): return
    materii = [
        ("Analiza Matematica", 5, 1, 1, "Calculatoare"), ("Algebra si Geometrie", 5, 1, 1, "Calculatoare"), ("Fizica", 4, 1, 1, "Calculatoare"), ("Programarea Calculatoarelor", 6, 1, 1, "Calculatoare"),
        ("Matematici Speciale", 5, 1, 2, "Calculatoare"), ("Structuri de Date", 6, 1, 2, "Calculatoare"), ("Electrotehnica", 5, 1, 2, "Calculatoare"), ("Metode Numerice", 4, 1, 2, "Calculatoare"),
        ("Programare Orientata pe Obiecte", 6, 2, 1, "Calculatoare"), ("Electronica Digitala", 5, 2, 1, "Calculatoare"), ("Teoria Sistemelor", 5, 2, 1, "Calculatoare"), ("Limbaje de Asamblare", 5, 2, 1, "Calculatoare"),
        ("Sisteme de Operare", 5, 2, 2, "Calculatoare"), ("Proiectare Algoritmi", 5, 2, 2, "Calculatoare"), ("Arhitectura Calculatoarelor", 6, 2, 2, "Calculatoare"),
        ("Baze de Date", 6, 3, 1, "Calculatoare"), ("Retele de Calculatoare", 6, 3, 1, "Calculatoare"), ("Calculatoare Numerice", 5, 3, 1, "Calculatoare"), ("Inginerie Software", 5, 3, 1, "Calculatoare"),
        ("Inteligenta Artificiala", 5, 4, 1, "Calculatoare"), ("Sisteme Incorporate", 5, 4, 1, "Calculatoare"), ("Securitatea Sistemelor", 5, 4, 1, "Calculatoare"), ("Proiect Diploma", 10, 4, 2, "Calculatoare"),
    ]
    for nume, credite, an, sem, spec in materii:
        db.session.add(Disciplina(nume_disciplina=nume, credite=credite, an_studiu=an, specializare=spec, semestru=sem))
    db.session.commit()

# --- RUTE ---
@app.route('/setup_admin')
def setup_admin():
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', email='admin@uoradea.ro', password=generate_password_hash('admin123'), role='admin', is_approved=True))
        db.session.commit(); return "Admin creat!"
    return "Exista deja."

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = User.query.filter((User.username==request.form.get('username')) | (User.email==request.form.get('username'))).first()
        if u and check_password_hash(u.password, request.form.get('password')):
            if not u.is_approved: flash('Cont neaprobat.', 'warning'); return render_template('login.html')
            login_user(u); return redirect(url_for('index'))
        flash('Date incorecte.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nume, pren, email, pw = request.form['nume'], request.form['prenume'], request.form['email'], request.form['password']
        base_user = f"{pren}.{nume}".lower().replace(" ", "")
        new_u = User(username=base_user, email=email, password=generate_password_hash(pw), role=request.form['role'], is_approved=False)
        db.session.add(new_u); db.session.commit()
        if request.form['role'] == 'student':
            db.session.add(Student(nume=nume, prenume=pren, nr_matricol=f"M{random.randint(1000,9999)}", grupa=f"C{request.form['an_studiu']}", an_studiu=int(request.form['an_studiu']), specializare=request.form['specializare'], user_id=new_u.id))
        else:
            db.session.add(Profesor(nume=nume, prenume=pren, user_id=new_u.id))
        db.session.commit(); return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('login'))

# === CHAT ===
@app.route('/chat')
@login_required
def chat_home():
    sent = db.session.query(Mesaj.receiver_id).filter(Mesaj.sender_id == current_user.id)
    received = db.session.query(Mesaj.sender_id).filter(Mesaj.receiver_id == current_user.id)
    contact_ids = sent.union(received).distinct().all()
    contacts = [User.query.get(cid) for (cid,) in contact_ids]
    return render_template('chat.html', contacts=contacts, active_chat=None)

@app.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat_with(user_id):
    partner = User.query.get_or_404(user_id)
    if request.method == 'POST':
        if request.form.get('mesaj'):
            db.session.add(Mesaj(sender_id=current_user.id, receiver_id=user_id, text=request.form.get('mesaj')))
            db.session.commit()
        return redirect(url_for('chat_with', user_id=user_id))
    mesaje = Mesaj.query.filter(((Mesaj.sender_id == current_user.id) & (Mesaj.receiver_id == user_id)) | ((Mesaj.sender_id == user_id) & (Mesaj.receiver_id == current_user.id))).order_by(Mesaj.data_trimitere.asc()).all()
    
    sent = db.session.query(Mesaj.receiver_id).filter(Mesaj.sender_id == current_user.id)
    received = db.session.query(Mesaj.sender_id).filter(Mesaj.receiver_id == current_user.id)
    contact_ids = sent.union(received).distinct().all()
    contacts = [User.query.get(cid) for (cid,) in contact_ids]
    return render_template('chat.html', contacts=contacts, active_chat=partner, mesaje=mesaje)

@app.route('/api/search_users')
@login_required
def api_search_users():
    query = request.args.get('q', '')
    if len(query) < 2: return jsonify([])
    users = User.query.filter(User.username.ilike(f'{query}%'), User.is_approved==True, User.id!=current_user.id).limit(10).all()
    return jsonify([{'id': u.id, 'username': u.username, 'role': u.role} for u in users])

# === RUTE ADAUGARE (COMPATIBILITATE) ===
@app.route('/adauga_student', methods=['GET', 'POST'])
@login_required
def adauga_student():
    if current_user.role not in ['admin', 'profesor']: return redirect(url_for('index'))
    if request.method == 'POST':
        db.session.add(Student(nume=request.form['nume'], prenume=request.form['prenume'], nr_matricol=request.form['nr_matricol'], grupa=request.form['grupa'], an_studiu=int(request.form['an_studiu']), specializare=request.form['specializare']))
        db.session.commit(); return redirect(url_for('index'))
    return render_template('adauga_student.html')

@app.route('/adauga_profesor', methods=['GET', 'POST'])
@login_required
def adauga_profesor():
    if current_user.role != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        db.session.add(Profesor(nume=request.form['nume'], prenume=request.form['prenume']))
        db.session.commit(); return redirect(url_for('index'))
    return render_template('adauga_profesor.html')

# === RUTE REINTRODUSE PENTRU A EVITA BUILD ERROR ===
# Acestea sunt rutele care lipseau si cauzau erorile din screenshot-uri
@app.route('/lista_discipline') 
@login_required
def lista_discipline(): 
    # Aceasta ruta era cautata de butonul "Discipline"
    return render_template('lista_discipline.html', discipline=Disciplina.query.all(), profesori=Profesor.query.all())

@app.route('/admin/discipline')
@login_required
def admin_discipline():
    # Alias pentru aceeasi pagina
    return lista_discipline()


# === PROFESOR & ADMIN ===
@app.route('/materie/<int:id_disc>', methods=['GET', 'POST'])
@login_required
def panou_materie(id_disc):
    d = Disciplina.query.get_or_404(id_disc)
    prof = Profesor.query.filter_by(user_id=current_user.id).first()
    is_titular = prof and (d.id_titular == prof.id_profesor)
    is_laborant = prof and (d.id_laborant == prof.id_profesor)
    if not (is_titular or is_laborant or current_user.role == 'admin'): abort(403)
    
    if request.method == 'POST' and 'set_ponderi' in request.form and is_titular:
        d.pondere_examen = int(request.form.get('exam')); d.pondere_laborator = int(request.form.get('lab')); db.session.commit()
    if request.method == 'POST' and 'programare' in request.form:
        db.session.add(EvaluareProgramata(id_disciplina=d.id_disciplina, tip=request.form.get('tip'), data_evaluare=datetime.strptime(request.form.get('data'), '%Y-%m-%d').date())); db.session.commit()

    return render_template('vizualizare_materie.html', disciplina=d, studenti=Student.query.filter_by(specializare=d.specializare, an_studiu=d.an_studiu).all(), is_titular=is_titular, is_laborant=is_laborant, evaluari=d.evaluari)

@app.route('/adauga_nota_completa', methods=['POST'])
@login_required
def adauga_nota_completa():
    db.session.add(Notare(id_student=request.form['id_student'], id_disciplina=request.form['id_disciplina'], tip_activitate=request.form['tip_activitate'], nota=float(request.form['nota']))); db.session.commit()
    return redirect(url_for('panou_materie', id_disc=request.form['id_disciplina']))

@app.route('/')
@login_required
def index():
    if current_user.role == 'student': 
        s = Student.query.filter_by(user_id=current_user.id).first()
        return redirect(url_for('raport_student_general', student_id=s.id_student)) if s else "Cont student incomplet"
    if current_user.role == 'profesor':
        prof = Profesor.query.filter_by(user_id=current_user.id).first()
        materii = Disciplina.query.filter(or_(Disciplina.id_titular == prof.id_profesor, Disciplina.id_laborant == prof.id_profesor)).all() if prof else []
        return render_template('index_profesor.html', materii=materii)
    studenti = Student.query.outerjoin(User).filter((User.is_approved == True) | (Student.user_id == None)).all()
    profesori = Profesor.query.outerjoin(User).filter((User.is_approved == True) | (Profesor.user_id == None)).all()
    return render_template('index.html', studenti=studenti, profesori=profesori)

# Rute Admin
@app.route('/admin/utilizatori')
@login_required
def gestiune_utilizatori(): return render_template('admin_users.html', pending_users=User.query.filter_by(is_approved=False).all(), active_users=User.query.filter_by(is_approved=True).all())

@app.route('/admin/aproba_user/<int:user_id>')
@login_required
def aproba_user(user_id):
    User.query.get(user_id).is_approved = True; db.session.commit(); return redirect(url_for('gestiune_utilizatori'))

@app.route('/admin/sterge_user/<int:user_id>')
@login_required
def sterge_utilizator(user_id):
    db.session.delete(User.query.get(user_id)); db.session.commit(); return redirect(url_for('gestiune_utilizatori'))

@app.route('/admin/asignare_complexa', methods=['POST'])
@login_required
def admin_asignare():
    d = Disciplina.query.get(request.form['id_disciplina']); d.id_titular = int(request.form['titular']) if request.form['titular'] else None; d.id_laborant = int(request.form['laborant']) if request.form['laborant'] else None; db.session.commit(); return redirect(url_for('lista_discipline'))

@app.route('/sterge_student/<int:id_student>')
def sterge_student(id_student): db.session.delete(Student.query.get(id_student)); db.session.commit(); return redirect(url_for('index'))
@app.route('/sterge_profesor/<int:id_profesor>')
def sterge_profesor(id_profesor): db.session.delete(Profesor.query.get(id_profesor)); db.session.commit(); return redirect(url_for('index'))

@app.route('/raport/student/<int:student_id>')
@login_required
def raport_student_general(student_id):
    s = Student.query.get_or_404(student_id)
    materii = Disciplina.query.filter_by(specializare=s.specializare, an_studiu=s.an_studiu).all()
    situatie = []
    for m in materii:
        n_exam = Notare.query.filter_by(id_student=s.id_student, id_disciplina=m.id_disciplina, tip_activitate='Examen').first()
        n_lab = Notare.query.filter_by(id_student=s.id_student, id_disciplina=m.id_disciplina, tip_activitate='Laborator').all()
        media_lab = sum([x.nota for x in n_lab])/len(n_lab) if n_lab else 0
        nota_ex = n_exam.nota if n_exam else 0
        medie_finala = (nota_ex * m.pondere_examen + media_lab * m.pondere_laborator) / 100 if (nota_ex > 0 and media_lab > 0) else 0
        situatie.append({'nume': m.nume_disciplina, 'nota_exam': nota_ex or '-', 'media_lab': f"{media_lab:.2f}" if media_lab else '-', 'medie_finala': f"{medie_finala:.2f}" if medie_finala else 'Incomplet', 'pondere': f"Ex:{m.pondere_examen}% / Lab:{m.pondere_laborator}%"})
    return render_template('raport_student.html', student=s, situatie=situatie)

@app.route('/editeaza_student/<int:id_student>', methods=['GET', 'POST'])
def editeaza_student(id_student): return "Editare Student Placeholder" # Placeholder

if __name__ == '__main__':
    with app.app_context(): db.create_all(); seed_discipline()
    app.run(debug=True)