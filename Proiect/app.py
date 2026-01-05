from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, abort, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import random
from sqlalchemy import or_

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
    
    # Activitati
    has_laborator = db.Column(db.Boolean, default=False)
    has_seminar = db.Column(db.Boolean, default=False)
    has_proiect = db.Column(db.Boolean, default=False)

    # Profesori
    id_titular = db.Column(db.Integer, db.ForeignKey('profesor.id_profesor'), nullable=True)
    id_laborant = db.Column(db.Integer, db.ForeignKey('profesor.id_profesor'), nullable=True)
    id_seminarist = db.Column(db.Integer, db.ForeignKey('profesor.id_profesor'), nullable=True)
    id_proiectant = db.Column(db.Integer, db.ForeignKey('profesor.id_profesor'), nullable=True)
    
    # Ponderi Note
    pondere_examen = db.Column(db.Integer, default=60)
    pondere_laborator = db.Column(db.Integer, default=40)
    pondere_proiect = db.Column(db.Integer, default=0)

    # Cerinte Prezenta Minima (%)
    min_prez_curs = db.Column(db.Integer, default=50)
    min_prez_laborator = db.Column(db.Integer, default=100)
    min_prez_seminar = db.Column(db.Integer, default=100)
    min_prez_proiect = db.Column(db.Integer, default=100)

    note = db.relationship('Notare', backref='disciplina', lazy=True)
    inscrieri = db.relationship('Inscriere', backref='disciplina', lazy=True, cascade="all, delete-orphan")
    prezente = db.relationship('Prezenta', backref='disciplina', lazy=True, cascade="all, delete-orphan")
    
    def get_full_name(self): return self.nume_disciplina

class Student(db.Model):
    id_student = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(50), nullable=False)
    prenume = db.Column(db.String(50), nullable=False)
    nr_matricol = db.Column(db.String(20), unique=True, nullable=False)
    grupa = db.Column(db.String(10), nullable=False)
    an_studiu = db.Column(db.Integer, nullable=False, default=1)
    specializare = db.Column(db.String(50), nullable=False, default='Calculatoare')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    
    inscrieri = db.relationship('Inscriere', backref='student', lazy=True, cascade="all, delete-orphan")
    def get_full_name(self): return f"{self.nume} {self.prenume}"

class Inscriere(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_student = db.Column(db.Integer, db.ForeignKey('student.id_student'), nullable=False)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    data_inscriere = db.Column(db.Date, default=date.today)
    __table_args__ = (db.UniqueConstraint('id_student', 'id_disciplina', name='unique_inscriere'),)

class Notare(db.Model):
    id_notare = db.Column(db.Integer, primary_key=True)
    id_student = db.Column(db.Integer, db.ForeignKey('student.id_student'), nullable=False)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    tip_activitate = db.Column(db.String(20), nullable=False) 
    nota = db.Column(db.Float, nullable=False) 
    data_notare = db.Column(db.Date, nullable=False, default=date.today)

class Prezenta(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_student = db.Column(db.Integer, db.ForeignKey('student.id_student'), nullable=False)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    tip_activitate = db.Column(db.String(20), nullable=False) # 'curs', 'laborator', 'seminar', 'proiect'
    saptamana = db.Column(db.Integer, nullable=False) # 1-14
    is_prezent = db.Column(db.Boolean, default=True)
    __table_args__ = (db.UniqueConstraint('id_student', 'id_disciplina', 'tip_activitate', 'saptamana', name='unique_prezenta_full'),)

class EvaluareProgramata(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    tip = db.Column(db.String(50), nullable=False)
    data_evaluare = db.Column(db.Date, nullable=False)

# --- POPULARE CURICULA (COMPLET) ---
def seed_discipline():
    if Disciplina.query.first(): return
    
    # Format: (Nume, Credite, An, Sem, Specializare, has_lab, has_sem, has_proiect)
    materii = [
        # === CALCULATOARE (CTI) ===
        # Anul 1
        ("Analiza Matematica", 5, 1, 1, "Calculatoare", False, True, False),
        ("Algebra si Geometrie", 5, 1, 1, "Calculatoare", False, True, False),
        ("Fizica", 4, 1, 1, "Calculatoare", True, False, False),
        ("Programarea Calculatoarelor", 6, 1, 1, "Calculatoare", True, False, False),
        ("Bazele Electrotehnicii", 5, 1, 2, "Calculatoare", True, True, False),
        ("Structuri de Date", 6, 1, 2, "Calculatoare", True, False, True),
        ("Matematici Speciale", 4, 1, 2, "Calculatoare", False, True, False),
        
        # Anul 2
        ("Programare Orientata pe Obiecte", 6, 2, 1, "Calculatoare", True, False, True),
        ("Teoria Sistemelor", 5, 2, 1, "Calculatoare", True, False, False),
        ("Electronica Digitala", 5, 2, 1, "Calculatoare", True, False, False),
        ("Limbaje de Asamblare", 5, 2, 1, "Calculatoare", True, False, False),
        ("Sisteme de Operare", 5, 2, 2, "Calculatoare", True, False, False),
        ("Arhitectura Calculatoarelor", 6, 2, 2, "Calculatoare", True, False, False),
        ("Proiectare Algoritmi", 5, 2, 2, "Calculatoare", True, False, False),
        ("Masurari Electronice", 4, 2, 2, "Calculatoare", True, False, False),

        # Anul 3
        ("Baze de Date", 6, 3, 1, "Calculatoare", True, False, True),
        ("Retele de Calculatoare", 6, 3, 1, "Calculatoare", True, False, False),
        ("Inginerie Software", 5, 3, 1, "Calculatoare", True, False, True),
        ("Calculatoare Numerice", 5, 3, 1, "Calculatoare", True, False, False),
        ("Inteligenta Artificiala", 5, 3, 2, "Calculatoare", True, False, False),
        ("Sisteme Incorporate", 5, 3, 2, "Calculatoare", True, False, True),
        ("Grafica pe Calculator", 5, 3, 2, "Calculatoare", True, False, False),
        
        # Anul 4
        ("Securitatea Sistemelor", 5, 4, 1, "Calculatoare", True, False, False),
        ("Interfete Om-Calculator", 4, 4, 1, "Calculatoare", True, False, False),
        ("Sisteme Distribuite", 5, 4, 1, "Calculatoare", True, False, False),
        ("Testarea Sistemelor", 4, 4, 1, "Calculatoare", True, False, False),
        ("Elaborare Proiect Diploma", 10, 4, 2, "Calculatoare", False, False, True),
        ("Practica de Specialitate", 5, 4, 2, "Calculatoare", False, False, True),

        # === AUTOMATICA (AIA) ===
        # Anul 1
        ("Analiza Matematica", 5, 1, 1, "Automatica", False, True, False),
        ("Fizica", 4, 1, 1, "Automatica", True, False, False),
        ("Chimie", 3, 1, 1, "Automatica", True, False, False),
        ("Programarea Calculatoarelor", 6, 1, 1, "Automatica", True, False, False),
        ("Mecanica", 5, 1, 2, "Automatica", False, True, False),
        ("Electrotehnica", 5, 1, 2, "Automatica", True, False, False),
        ("Grafica Asistata", 4, 1, 2, "Automatica", True, False, False),

        # Anul 2
        ("Electronica Analogica", 5, 2, 1, "Automatica", True, False, False),
        ("Teoria Sistemelor Automate 1", 6, 2, 1, "Automatica", True, True, False),
        ("Electronica Digitala", 5, 2, 2, "Automatica", True, False, False),
        ("Teoria Sistemelor Automate 2", 6, 2, 2, "Automatica", True, False, True),
        ("Masurari si Traductoare", 5, 2, 2, "Automatica", True, False, False),

        # Anul 3
        ("Ingineria Reglarii Automate", 6, 3, 1, "Automatica", True, False, True),
        ("Identificarea Sistemelor", 5, 3, 1, "Automatica", True, False, False),
        ("Echipamente de Automatizare", 5, 3, 1, "Automatica", True, False, False),
        ("Modelare si Simulare", 5, 3, 2, "Automatica", True, False, True),
        ("Automate Programabile", 5, 3, 2, "Automatica", True, False, False),
        ("Sisteme cu Microprocesoare", 5, 3, 2, "Automatica", True, False, False),

        # Anul 4
        ("Robotica", 5, 4, 1, "Automatica", True, False, False),
        ("Sisteme de Conducere a Fabricației", 5, 4, 1, "Automatica", True, False, True),
        ("Inginerie Software pt. Control", 4, 4, 1, "Automatica", True, False, False),
        ("Sisteme Scada", 4, 4, 1, "Automatica", True, False, False),
        ("Proiect Diploma", 10, 4, 2, "Automatica", False, False, True),

        # === ELECTRONICA APLICATA (EA) ===
        # Anul 1
        ("Matematici Speciale", 5, 1, 1, "Electronica Aplicata", False, True, False),
        ("Fizica Tehnica", 4, 1, 1, "Electronica Aplicata", True, False, False),
        ("Componente si Dispozitive Electronice", 6, 1, 2, "Electronica Aplicata", True, False, False),
        ("Materiale pentru Electronica", 4, 1, 2, "Electronica Aplicata", True, False, False),
        
        # Anul 2
        ("Semnale si Sisteme", 5, 2, 1, "Electronica Aplicata", False, True, False),
        ("Circuite Integrate Digitale", 5, 2, 1, "Electronica Aplicata", True, False, False),
        ("Prelucrarea Semnalelor", 5, 2, 2, "Electronica Aplicata", True, False, False),
        ("Circuite Electronice Fundamentale", 6, 2, 2, "Electronica Aplicata", True, False, True),

        # Anul 3
        ("Microcontrolere", 6, 3, 1, "Electronica Aplicata", True, False, True),
        ("Sisteme de Achizitie Date", 5, 3, 1, "Electronica Aplicata", True, False, False),
        ("Electronică de Putere", 5, 3, 2, "Electronica Aplicata", True, False, False),
        ("Comunicatii Mobile", 4, 3, 2, "Electronica Aplicata", False, True, False),

        # Anul 4
        ("Televiziune", 5, 4, 1, "Electronica Aplicata", True, False, False),
        ("Optoelectronica", 4, 4, 1, "Electronica Aplicata", True, False, False),
        ("Sisteme Audio-Video", 5, 4, 1, "Electronica Aplicata", True, False, False),
        ("Proiect Licenta", 10, 4, 2, "Electronica Aplicata", False, False, True),

        # === TEHNOLOGIA INFORMATIEI (TI) ===
        # Anul 1
        ("Programare C", 5, 1, 1, "Tehnologia Informatiei", True, False, False),
        ("Arhitectura Sistemelor de Calcul", 5, 1, 1, "Tehnologia Informatiei", True, False, False),
        ("Algoritmi si Structuri de Date", 6, 1, 2, "Tehnologia Informatiei", True, False, False),
        ("Bazele Electrotehnicii", 5, 1, 2, "Tehnologia Informatiei", True, True, False),

        # Anul 2
        ("Bazele Comunicatiilor", 5, 2, 1, "Tehnologia Informatiei", True, False, False),
        ("Programare Java", 5, 2, 1, "Tehnologia Informatiei", True, False, True),
        ("Protocoale de Comunicatii", 5, 2, 2, "Tehnologia Informatiei", True, False, False),
        ("Prelucrarea Digitala a Semnalelor", 5, 2, 2, "Tehnologia Informatiei", True, False, False),

        # Anul 3
        ("Tehnologii WEB", 5, 3, 1, "Tehnologia Informatiei", True, False, True),
        ("Baze de Date Relationale", 6, 3, 1, "Tehnologia Informatiei", True, False, False),
        ("Multimedia", 5, 3, 2, "Tehnologia Informatiei", True, False, True),
        ("Administrare Retele", 5, 3, 2, "Tehnologia Informatiei", True, False, False),

        # Anul 4
        ("Securitate Cibernetica", 5, 4, 1, "Tehnologia Informatiei", True, False, False),
        ("Cloud Computing", 5, 4, 1, "Tehnologia Informatiei", True, False, False),
        ("Comert Electronic", 4, 4, 1, "Tehnologia Informatiei", False, True, False),
        ("Internet of Things", 5, 4, 1, "Tehnologia Informatiei", True, False, True),
        ("Elaborare Lucrare Licenta", 10, 4, 2, "Tehnologia Informatiei", False, False, True),
    ]

    for nume, credite, an, sem, spec, has_lab, has_sem, has_pro in materii:
        p_exam = 60
        p_lab = 40 if has_lab else 0
        p_pro = 0
        if has_pro:
            p_exam = 40
            p_lab = 30 if has_lab else 0
            p_pro = 30
        if not has_lab and not has_pro and has_sem:
            p_exam = 100 

        db.session.add(Disciplina(
            nume_disciplina=nume, credite=credite, an_studiu=an, 
            specializare=spec, semestru=sem,
            has_laborator=has_lab, has_seminar=has_sem, has_proiect=has_pro,
            pondere_examen=p_exam, pondere_laborator=p_lab, pondere_proiect=p_pro,
            min_prez_curs=50, min_prez_laborator=100, min_prez_seminar=80, min_prez_proiect=100
        ))
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
            if not u.is_approved: 
                flash('Contul tău nu a fost încă aprobat.', 'warning')
                return render_template('login.html')
            login_user(u)
            return redirect(url_for('index'))
        flash('Date incorecte.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nume, pren, email, pw = request.form['nume'], request.form['prenume'], request.form['email'], request.form['password']
        if pw != request.form['confirm_password']:
            flash('Parolele nu coincid!', 'danger')
            return redirect(url_for('register'))
        if User.query.filter((User.email == email)).first():
            flash('Există deja un cont cu acest email!', 'danger')
            return redirect(url_for('register'))
        
        base_user = f"{pren}.{nume}".lower().replace(" ", "")
        if User.query.filter_by(username=base_user).first():
            base_user += str(random.randint(1,99))
        
        new_u = User(username=base_user, email=email, password=generate_password_hash(pw), role=request.form['role'], is_approved=False)
        db.session.add(new_u); db.session.commit()
        
        if request.form['role'] == 'student':
            db.session.add(Student(nume=nume, prenume=pren, nr_matricol=request.form['nr_matricol'], grupa=f"C{request.form['an_studiu']}", an_studiu=int(request.form['an_studiu']), specializare=request.form['specializare'], user_id=new_u.id))
        else:
            db.session.add(Profesor(nume=nume, prenume=pren, user_id=new_u.id))
        
        db.session.commit()
        flash('Cont creat cu succes. Așteaptă aprobarea.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('login'))

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
        msg, file = request.form.get('mesaj'), request.files.get('fisier')
        fname = None
        if file and file.filename:
            fname = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
            file.save(os.path.join(app.config['CHAT_UPLOAD_FOLDER'], fname))
        if msg or fname:
            db.session.add(Mesaj(sender_id=current_user.id, receiver_id=user_id, text=msg, fisier=fname))
            db.session.commit()
        return redirect(url_for('chat_with', user_id=user_id))
    
    mesaje = Mesaj.query.filter(((Mesaj.sender_id == current_user.id) & (Mesaj.receiver_id == user_id)) | ((Mesaj.sender_id == user_id) & (Mesaj.receiver_id == current_user.id))).order_by(Mesaj.data_trimitere.asc()).all()
    sent = db.session.query(Mesaj.receiver_id).filter(Mesaj.sender_id == current_user.id)
    received = db.session.query(Mesaj.sender_id).filter(Mesaj.receiver_id == current_user.id)
    contact_ids = sent.union(received).distinct().all()
    contacts = [User.query.get(cid) for (cid,) in contact_ids]
    if partner not in contacts: contacts.insert(0, partner)
    return render_template('chat.html', contacts=contacts, active_chat=partner, mesaje=mesaje)

@app.route('/api/search_users')
@login_required
def api_search_users():
    q = request.args.get('q', '')
    if len(q)<2: return jsonify([])
    users = User.query.filter(User.username.ilike(f'%{q}%'), User.is_approved==True, User.id!=current_user.id).limit(10).all()
    return jsonify([{'id': u.id, 'username': u.username, 'full_name': u.student_profile.get_full_name() if u.student_profile else (u.profesor_profile.get_full_name() if u.profesor_profile else u.username), 'role': u.role} for u in users])

@app.route('/lista_profesori')
@login_required
def lista_profesori(): return render_template('lista_profesori.html', profesori=Profesor.query.all())

@app.route('/lista_discipline') 
@login_required
def lista_discipline(): 
    discipline = Disciplina.query.order_by(Disciplina.specializare, Disciplina.an_studiu, Disciplina.semestru).all()
    profesori = Profesor.query.all()
    return render_template('lista_discipline.html', discipline=discipline, profesori=profesori)

@app.route('/admin/discipline')
@login_required
def admin_discipline(): return lista_discipline()

@app.route('/admin/asignare_complexa', methods=['POST'])
@login_required
def admin_asignare():
    d = Disciplina.query.get(request.form['id_disciplina'])
    d.id_titular = int(request.form['titular']) if request.form.get('titular') else None
    if d.has_laborator: d.id_laborant = int(request.form['laborant']) if request.form.get('laborant') else None
    if d.has_seminar: d.id_seminarist = int(request.form['seminarist']) if request.form.get('seminarist') else None
    if d.has_proiect: d.id_proiectant = int(request.form['proiectant']) if request.form.get('proiectant') else None
    db.session.commit()
    return redirect(url_for('lista_discipline'))

@app.route('/materie/<int:id_disc>', methods=['GET', 'POST'])
@login_required
def panou_materie(id_disc):
    d = Disciplina.query.get_or_404(id_disc)
    prof = Profesor.query.filter_by(user_id=current_user.id).first()
    is_titular = prof and (d.id_titular == prof.id_profesor)
    is_laborant = prof and (d.id_laborant == prof.id_profesor)
    is_seminarist = prof and (d.id_seminarist == prof.id_profesor)
    is_proiectant = prof and (d.id_proiectant == prof.id_profesor)
    is_admin = current_user.role == 'admin'
    
    if not (is_titular or is_laborant or is_seminarist or is_proiectant or is_admin): abort(403)
    
    if request.method == 'POST' and 'config_materie' in request.form:
        d.pondere_examen = int(request.form.get('pond_exam', 0))
        d.pondere_laborator = int(request.form.get('pond_lab', 0))
        d.pondere_proiect = int(request.form.get('pond_pro', 0))
        d.min_prez_curs = int(request.form.get('min_curs', 0))
        d.min_prez_laborator = int(request.form.get('min_lab', 0))
        d.min_prez_seminar = int(request.form.get('min_sem', 0))
        d.min_prez_proiect = int(request.form.get('min_pro', 0))
        db.session.commit()
        flash('Configurare salvată.', 'success')

    studenti_inscrisi = [i.student for i in d.inscrieri]
    # CAUTARE GLOBALA STUDENTI (Nu doar cei din aceeasi specializare)
    toti_studentii = Student.query.all()
    studenti_neinscrisi = [s for s in toti_studentii if s not in studenti_inscrisi]

    # Pre-fetch Note pentru afisare
    note_q = Notare.query.filter_by(id_disciplina=d.id_disciplina).all()
    note_map = {}
    for n in note_q:
        if n.id_student not in note_map: note_map[n.id_student] = {}
        note_map[n.id_student][n.tip_activitate] = n.nota

    return render_template('vizualizare_materie.html', disciplina=d, studenti=studenti_inscrisi, studenti_neinscrisi=studenti_neinscrisi, is_titular=is_titular, is_admin=is_admin, note_map=note_map)

@app.route('/adauga_nota_completa', methods=['POST'])
@login_required
def adauga_nota_completa():
    Notare.query.filter_by(id_student=request.form['id_student'], id_disciplina=request.form['id_disciplina'], tip_activitate=request.form['tip_activitate']).delete()
    db.session.add(Notare(id_student=request.form['id_student'], id_disciplina=request.form['id_disciplina'], tip_activitate=request.form['tip_activitate'], nota=float(request.form['nota'])))
    db.session.commit()
    return redirect(url_for('panou_materie', id_disc=request.form['id_disciplina']))

@app.route('/reset_nota', methods=['POST'])
@login_required
def reset_nota():
    Notare.query.filter_by(id_student=request.form['id_student'], id_disciplina=request.form['id_disciplina'], tip_activitate=request.form['tip_activitate']).delete()
    db.session.commit()
    return redirect(url_for('panou_materie', id_disc=request.form['id_disciplina']))

@app.route('/enroll_student', methods=['POST'])
@login_required
def enroll_student():
    db.session.add(Inscriere(id_student=request.form['id_student'], id_disciplina=request.form['id_disciplina'])); db.session.commit()
    return redirect(url_for('panou_materie', id_disc=request.form['id_disciplina']))

@app.route('/enroll_all_eligible', methods=['POST'])
@login_required
def enroll_all_eligible():
    d = Disciplina.query.get(request.form['id_disciplina'])
    eligibili = Student.query.filter_by(specializare=d.specializare, an_studiu=d.an_studiu).all()
    for s in eligibili:
        if not Inscriere.query.filter_by(id_student=s.id_student, id_disciplina=d.id_disciplina).first(): db.session.add(Inscriere(id_student=s.id_student, id_disciplina=d.id_disciplina))
    db.session.commit(); return redirect(url_for('panou_materie', id_disc=d.id_disciplina))

@app.route('/remove_student', methods=['POST'])
@login_required
def remove_student():
    ins = Inscriere.query.filter_by(id_student=request.form['id_student'], id_disciplina=request.form['id_disciplina']).first()
    if ins: db.session.delete(ins); db.session.commit()
    return redirect(url_for('panou_materie', id_disc=request.form['id_disciplina']))

@app.route('/update_prezenta', methods=['POST'])
@login_required
def update_prezenta():
    data = request.json
    Prezenta.query.filter_by(id_student=data['id_student'], id_disciplina=data['id_disciplina'], tip_activitate=data['tip_activitate']).delete()
    for sapt in data['weeks']: db.session.add(Prezenta(id_student=data['id_student'], id_disciplina=data['id_disciplina'], tip_activitate=data['tip_activitate'], saptamana=int(sapt), is_prezent=True))
    db.session.commit(); return jsonify({'status': 'success'})

@app.route('/get_prezente_student')
@login_required
def get_prezente_student():
    prezente = Prezenta.query.filter_by(id_student=request.args.get('id_student'), id_disciplina=request.args.get('id_disciplina'), tip_activitate=request.args.get('tip_activitate')).all()
    return jsonify([p.saptamana for p in prezente])

@app.route('/admin/utilizatori')
@login_required
def gestiune_utilizatori(): return render_template('admin_users.html', pending_users=User.query.filter_by(is_approved=False).all(), active_users=User.query.filter_by(is_approved=True).all())

@app.route('/admin/aproba_user/<int:user_id>')
@login_required
def aproba_user(user_id):
    u = User.query.get(user_id); u.is_approved = True; db.session.commit()
    if u.role == 'student' and u.student_profile:
        s = u.student_profile
        materii = Disciplina.query.filter_by(specializare=s.specializare, an_studiu=s.an_studiu).all()
        for m in materii:
            if not Inscriere.query.filter_by(id_student=s.id_student, id_disciplina=m.id_disciplina).first(): db.session.add(Inscriere(id_student=s.id_student, id_disciplina=m.id_disciplina))
        db.session.commit()
    return redirect(url_for('gestiune_utilizatori'))

@app.route('/admin/sterge_user/<int:user_id>')
@login_required
def sterge_utilizator(user_id): db.session.delete(User.query.get(user_id)); db.session.commit(); return redirect(url_for('gestiune_utilizatori'))
@app.route('/sterge_student/<int:id_student>')
def sterge_student(id_student): db.session.delete(Student.query.get(id_student)); db.session.commit(); return redirect(url_for('index'))
@app.route('/sterge_profesor/<int:id_profesor>')
def sterge_profesor(id_profesor): db.session.delete(Profesor.query.get(id_profesor)); db.session.commit(); return redirect(url_for('index'))

@app.route('/editeaza_student/<int:id_student>', methods=['GET', 'POST'])
@login_required
def editeaza_student(id_student):
    if current_user.role != 'admin': abort(403)
    s = Student.query.get_or_404(id_student)
    if request.method == 'POST':
        s.nume = request.form['nume']; s.prenume = request.form['prenume']; s.nr_matricol = request.form['nr_matricol']
        s.an_studiu = int(request.form['an_studiu']); s.specializare = request.form['specializare']
        db.session.commit(); flash('Actualizat.', 'success'); return redirect(url_for('index'))
    return render_template('editeaza_student.html', student=s)

@app.route('/')
@login_required
def index():
    if current_user.role == 'student': s = Student.query.filter_by(user_id=current_user.id).first(); return redirect(url_for('raport_student_general', student_id=s.id_student)) if s else "Cont incomplet"
    if current_user.role == 'profesor':
        prof = Profesor.query.filter_by(user_id=current_user.id).first()
        materii = Disciplina.query.filter(or_(Disciplina.id_titular == prof.id_profesor, Disciplina.id_laborant == prof.id_profesor, Disciplina.id_seminarist == prof.id_profesor, Disciplina.id_proiectant == prof.id_profesor)).all() if prof else []
        return render_template('index_profesor.html', materii=materii, profesor=prof)
    return render_template('index.html', studenti=Student.query.outerjoin(User).filter(User.is_approved==True).all(), profesori=Profesor.query.outerjoin(User).filter(User.is_approved==True).all())

@app.route('/raport/student/<int:student_id>')
@login_required
def raport_student_general(student_id):
    s = Student.query.get_or_404(student_id); inscrieri = Inscriere.query.filter_by(id_student=s.id_student).all()
    situatie_sem1 = []; situatie_sem2 = []; note_sem1 = []; note_sem2 = []
    
    for ins in inscrieri:
        m = ins.disciplina
        n_exam = Notare.query.filter_by(id_student=s.id_student, id_disciplina=m.id_disciplina, tip_activitate='Examen').first()
        n_lab = Notare.query.filter_by(id_student=s.id_student, id_disciplina=m.id_disciplina, tip_activitate='Laborator').first()
        n_pro = Notare.query.filter_by(id_student=s.id_student, id_disciplina=m.id_disciplina, tip_activitate='Proiect').first()
        
        nota_ex = n_exam.nota if n_exam else 0
        nota_lab = n_lab.nota if n_lab else 0
        nota_pro = n_pro.nota if n_pro else 0
        
        media = (nota_ex * m.pondere_examen + nota_lab * m.pondere_laborator + nota_pro * m.pondere_proiect) / 100
        
        p_cur = Prezenta.query.filter_by(id_student=s.id_student, id_disciplina=m.id_disciplina, tip_activitate='curs').count()
        p_lab = Prezenta.query.filter_by(id_student=s.id_student, id_disciplina=m.id_disciplina, tip_activitate='laborator').count()
        
        status = "Promovat"
        if (p_cur/14)*100 < m.min_prez_curs or (m.has_laborator and (p_lab/14)*100 < m.min_prez_laborator): status="Refacere"; media=0
        elif media < 5: status="Nepromovat"
        
        if media > 0: (note_sem1 if m.semestru==1 else note_sem2).append(media)
        
        item = {'nume': m.nume_disciplina, 'credite': m.credite, 'nota_exam': nota_ex or '-', 'nota_lab': nota_lab or '-', 'nota_pro': nota_pro or '-', 'medie_finala': f"{media:.2f}" if media else '0.00', 'status': status, 'clasa_status': 'text-danger' if status!='Promovat' else 'text-success', 'prezente_detalii': f"C:{p_cur}" + (f" L:{p_lab}" if m.has_laborator else "")}
        (situatie_sem1 if m.semestru==1 else situatie_sem2).append(item)
        
    avg1 = sum(note_sem1)/len(note_sem1) if note_sem1 else 0
    avg2 = sum(note_sem2)/len(note_sem2) if note_sem2 else 0
    avg_an = (avg1+avg2)/2 if avg1 and avg2 else (avg1 or avg2)
    return render_template('raport_student.html', student=s, sem1=situatie_sem1, sem2=situatie_sem2, avg1=f"{avg1:.2f}", avg2=f"{avg2:.2f}", avg_an=f"{avg_an:.2f}")

if __name__ == '__main__':
    with app.app_context(): db.create_all(); seed_discipline()
    app.run(debug=True)