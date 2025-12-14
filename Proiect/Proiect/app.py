from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
import random
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

# --- CONFIGURARE ---
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cheie_secreta_proiect_student'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog_scoala.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# UPLOAD CONFIG
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'docx', 'txt', 'zip'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
    mesaje = db.relationship('Mesaj', backref='sender', lazy=True)
    # Relatii cascade
    student_rel = db.relationship('Student', backref='user_ref', uselist=False, cascade="all, delete-orphan")
    profesor_rel = db.relationship('Profesor', backref='user_ref', uselist=False, cascade="all, delete-orphan")

class Mesaj(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    fisier = db.Column(db.String(255), nullable=True)
    tip_fisier = db.Column(db.String(20), nullable=True)
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
    
    # Optional profesor titular
    id_profesor_titular = db.Column(db.Integer, db.ForeignKey('profesor.id_profesor'), nullable=True)
    profesor = db.relationship('Profesor', backref='discipline_predate', lazy=True)

    note_primite = db.relationship('Notare', backref='disciplina_notata', lazy=True)
    prezente_inregistrate = db.relationship('Prezenta', backref='disciplina_prezenta', lazy=True)

class Student(db.Model):
    id_student = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(50), nullable=False)
    prenume = db.Column(db.String(50), nullable=False)
    nr_matricol = db.Column(db.String(20), unique=True, nullable=False)
    grupa = db.Column(db.String(10), nullable=False)
    
    an_studiu = db.Column(db.Integer, nullable=False, default=1)
    specializare = db.Column(db.String(50), nullable=False, default='Calculatoare')
    
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True) 
    
    note = db.relationship('Notare', backref='student', lazy=True, cascade="all, delete-orphan")
    prezente = db.relationship('Prezenta', backref='student', lazy=True, cascade="all, delete-orphan")
    
    def get_full_name(self): return f"{self.nume} {self.prenume}"

class Notare(db.Model):
    id_notare = db.Column(db.Integer, primary_key=True)
    id_student = db.Column(db.Integer, db.ForeignKey('student.id_student'), nullable=False)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    nota = db.Column(db.Float, nullable=False) 
    data_notare = db.Column(db.Date, nullable=False, default=date.today)
    
class Prezenta(db.Model):
    id_prezenta = db.Column(db.Integer, primary_key=True)
    id_student = db.Column(db.Integer, db.ForeignKey('student.id_student'), nullable=False)
    id_disciplina = db.Column(db.Integer, db.ForeignKey('disciplina.id_disciplina'), nullable=False)
    data_curs = db.Column(db.Date, nullable=False, default=date.today)
    status = db.Column(db.String(10), nullable=False)

# --- POPULARE AUTOMATA (CURICULA IETI) ---
def seed_discipline():
    if Disciplina.query.first():
        return 

    materii_ieti = [
        ("Analiza Matematica", 5, 1, "Calculatoare"),
        ("Algebra si Geometrie", 5, 1, "Calculatoare"),
        ("Programarea Calculatoarelor", 6, 1, "Calculatoare"),
        ("Fizica Generala", 4, 1, "Calculatoare"),
        ("Proiectare Logica", 5, 1, "Calculatoare"),
        ("Programare Orientata pe Obiecte", 6, 2, "Calculatoare"),
        ("Structuri de Date si Algoritmi", 6, 2, "Calculatoare"),
        ("Electronica Digitala", 5, 2, "Calculatoare"),
        ("Teoria Sistemelor", 5, 2, "Calculatoare"),
        ("Limbaje de Asamblare", 5, 2, "Calculatoare"),
        ("Baze de Date", 6, 3, "Calculatoare"),
        ("Sisteme de Operare", 5, 3, "Calculatoare"),
        ("Retele de Calculatoare", 6, 3, "Calculatoare"),
        ("Calculatoare Numerice", 5, 3, "Calculatoare"),
        ("Inginerie Software", 5, 3, "Calculatoare"),
        ("Inteligenta Artificiala", 5, 4, "Calculatoare"),
        ("Sisteme Incorporate", 5, 4, "Calculatoare"),
        ("Securitatea Sistemelor", 5, 4, "Calculatoare"),
        ("Proiect de Diploma", 10, 4, "Calculatoare"),
        ("Matematici Speciale", 5, 1, "Tehnologia Informatiei"),
        ("Fundamentele Programarii", 6, 1, "Tehnologia Informatiei"),
        ("Bazele Electrotehnicii", 5, 1, "Tehnologia Informatiei"),
        ("Programare Java", 6, 2, "Tehnologia Informatiei"),
        ("Circuite Electronice", 5, 2, "Tehnologia Informatiei"),
        ("Semnale si Sisteme", 5, 2, "Tehnologia Informatiei"),
        ("Tehnologii Web", 5, 3, "Tehnologia Informatiei"),
        ("Comunicatii Mobile", 5, 3, "Tehnologia Informatiei"),
        ("Administrare Retele", 6, 3, "Tehnologia Informatiei"),
        ("Cloud Computing", 5, 4, "Tehnologia Informatiei"),
        ("Internet of Things", 6, 4, "Tehnologia Informatiei"),
        ("Dispozitive Electronice", 6, 1, "Electronica Aplicata"),
        ("Materiale Componente", 5, 1, "Electronica Aplicata"),
        ("Circuite Integrate Analogice", 6, 2, "Electronica Aplicata"),
        ("Microcontrolere", 5, 3, "Electronica Aplicata"),
        ("Electronica de Putere", 6, 4, "Electronica Aplicata"),
        ("Analiza Matematica", 5, 1, "Automatica"),
        ("Grafica Asistata", 4, 1, "Automatica"),
        ("Teoria Sistemelor Automate", 6, 2, "Automatica"),
        ("Senzori si Traductoare", 5, 2, "Automatica"),
        ("Identificarea Sistemelor", 6, 3, "Automatica"),
        ("Robotica", 5, 4, "Automatica"),
    ]

    print("⏳ Se populează materiile IETI...")
    for nume, credite, an, spec in materii_ieti:
        db.session.add(Disciplina(nume_disciplina=nume, credite=credite, an_studiu=an, specializare=spec))
    db.session.commit()
    print("✅ Materii adăugate cu succes!")

# --- SETUP ADMIN ---
@app.route('/setup_admin')
def setup_admin():
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', email='admin@scoala.ro', password=generate_password_hash('admin123', method='scrypt'), role='admin', is_approved=True))
        db.session.commit()
        return "Admin creat!"
    return "Admin exista."

# --- AUTH ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter((User.username == request.form.get('username')) | (User.email == request.form.get('username'))).first()
        if user and check_password_hash(user.password, request.form.get('password')):
            if not user.is_approved: flash('Așteaptă aprobarea adminului.', 'warning'); return render_template('login.html')
            login_user(user); return redirect(url_for('index'))
        flash('Eroare autentificare.', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nume, prenume, email = request.form.get('nume'), request.form.get('prenume'), request.form.get('email')
        pw, pw_c = request.form.get('password'), request.form.get('confirm_password')
        role = request.form.get('role', 'student')
        
        if pw != pw_c: flash('Parolele nu coincid.', 'danger'); return redirect(url_for('register'))
        base_user = f"{prenume.lower()}.{nume.lower()}".replace(" ", "")
        if User.query.filter((User.email==email) | (User.username==base_user)).first(): base_user += str(random.randint(1,999))
        
        new_u = User(username=base_user, email=email, password=generate_password_hash(pw, method='scrypt'), role=role, is_approved=False)
        db.session.add(new_u); db.session.commit()
        
        if role == 'student':
            an, spec = request.form.get('an_studiu'), request.form.get('specializare')
            db.session.add(Student(nume=nume, prenume=prenume, nr_matricol=f"M{random.randint(1000,9999)}", grupa=f"{spec[:3].upper()}{an}", an_studiu=int(an), specializare=spec, user_id=new_u.id))
        elif role == 'profesor':
            db.session.add(Profesor(nume=nume, prenume=prenume, user_id=new_u.id))
        
        db.session.commit()
        flash(f'Cont creat! Username: {base_user}. Așteaptă aprobarea.', 'info'); return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout(): logout_user(); return redirect(url_for('login'))

# --- CHAT & UPLOADS ---
@app.route('/chat', methods=['GET', 'POST'])
@login_required
def chat():
    if request.method == 'POST':
        txt, file = request.form.get('mesaj'), request.files.get('fisier')
        fname, ftype = None, None
        if file and allowed_file(file.filename):
            fname = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            ftype = 'image' if fname.rsplit('.', 1)[1].lower() in ['png','jpg','jpeg'] else 'file'
        if txt or fname: db.session.add(Mesaj(sender_id=current_user.id, text=txt, fisier=fname, tip_fisier=ftype)); db.session.commit(); return redirect(url_for('chat'))
    return render_template('chat.html', mesaje=Mesaj.query.order_by(Mesaj.data_trimitere.asc()).all())

# --- ADMIN ROUTES ---
@app.route('/admin/utilizatori')
@login_required
def gestiune_utilizatori():
    # Aici adminul vede TOATE cererile (aprobate si neaprobate)
    return render_template('admin_users.html', pending_users=User.query.filter_by(is_approved=False).all(), active_users=User.query.filter_by(is_approved=True).all())

@app.route('/admin/aproba_user/<int:user_id>')
@login_required
def aproba_user(user_id):
    u = User.query.get(user_id); u.is_approved = True; db.session.commit(); return redirect(url_for('gestiune_utilizatori'))

@app.route('/admin/sterge_user/<int:user_id>')
@login_required
def sterge_utilizator(user_id):
    # Aici se declanseaza CASCADE delete (sterge si student/profesor asociat)
    db.session.delete(User.query.get(user_id)); db.session.commit(); return redirect(url_for('gestiune_utilizatori'))

@app.route('/sterge_profesor/<int:id_profesor>')
@login_required
def sterge_profesor(id_profesor):
    p = Profesor.query.get_or_404(id_profesor); db.session.delete(p); db.session.commit(); return redirect(url_for('index'))

@app.route('/sterge_student/<int:id_student>')
@login_required
def sterge_student(id_student):
    s = Student.query.get_or_404(id_student); db.session.delete(s); db.session.commit(); return redirect(url_for('index'))

@app.route('/editeaza_student/<int:id_student>', methods=['GET', 'POST'])
@login_required
def editeaza_student(id_student):
    s = Student.query.get_or_404(id_student)
    # Filtram materiile pentru editare doar cele relevante (sau toate, la alegere)
    discipline = Disciplina.query.filter_by(specializare=s.specializare, an_studiu=s.an_studiu).all()
    if request.method == 'POST':
        if 'update_info' in request.form:
            s.an_studiu = request.form.get('an_studiu'); s.specializare = request.form.get('specializare'); s.grupa = request.form.get('grupa'); db.session.commit(); flash('Date actualizate', 'success')
        return redirect(url_for('editeaza_student', id_student=id_student))
    return render_template('editeaza_student.html', student=s, discipline=discipline)

# --- MAIN ---
@app.route('/')
@login_required
def index():
    if current_user.role == 'student':
        s = Student.query.filter_by(user_id=current_user.id).first()
        if s: return redirect(url_for('raport_student_general', student_id=s.id_student))
    
    # FILTRARE LISTA: Afisam DOAR daca user-ul e aprobat SAU daca nu are user asociat (adaugat manual)
    studenti = Student.query.outerjoin(User).filter((User.is_approved == True) | (Student.user_id == None)).all()
    profesori = Profesor.query.outerjoin(User).filter((User.is_approved == True) | (Profesor.user_id == None)).all()
    
    return render_template('index.html', studenti=studenti, profesori=profesori)

# === RUTE REINTRODUSE (ACUM EXISTĂ) ===

@app.route('/adauga_student', methods=['GET', 'POST'])
@login_required
def adauga_student():
    if current_user.role not in ['admin', 'profesor']: return redirect(url_for('index'))
    if request.method == 'POST':
        db.session.add(Student(
            nume=request.form['nume'], 
            prenume=request.form['prenume'], 
            nr_matricol=request.form['nr_matricol'], 
            grupa=request.form['grupa'],
            an_studiu=int(request.form['an_studiu']),
            specializare=request.form['specializare']
        ))
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('adauga_student.html')

@app.route('/adauga_profesor', methods=['GET', 'POST'])
@login_required
def adauga_profesor():
    if current_user.role != 'admin': return redirect(url_for('index'))
    if request.method == 'POST':
        db.session.add(Profesor(nume=request.form['nume'], prenume=request.form['prenume']))
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('adauga_profesor.html')

# === RESTUL RUTELOR ===

@app.route('/adauga_nota', methods=['GET', 'POST'])
@login_required
def adauga_nota():
    if current_user.role == 'student': return redirect(url_for('index'))
    if request.method == 'POST':
        db.session.add(Notare(id_student=request.form['id_student'], id_disciplina=request.form['id_disciplina'], nota=float(request.form['nota'])))
        db.session.commit(); return redirect(url_for('raport_student_general', student_id=request.form['id_student']))
    return render_template('adauga_nota.html', studenti=Student.query.all(), discipline=Disciplina.query.all())

@app.route('/adauga_prezenta', methods=['GET', 'POST'])
@login_required
def adauga_prezenta():
    if current_user.role == 'student': return redirect(url_for('index'))
    if request.method == 'POST':
        db.session.add(Prezenta(id_student=request.form['id_student'], id_disciplina=request.form['id_disciplina'], status=request.form['status']))
        db.session.commit(); return redirect(url_for('raport_student_general', student_id=request.form['id_student']))
    return render_template('adauga_prezenta.html', studenti=Student.query.all(), discipline=Disciplina.query.all())

@app.route('/lista_discipline') 
@login_required
def lista_discipline(): 
    discipline = Disciplina.query.order_by(Disciplina.specializare, Disciplina.an_studiu).all()
    return render_template('lista_discipline.html', discipline=discipline)

@app.route('/raport/student/<int:student_id>')
@login_required
def raport_student_general(student_id):
    if current_user.role == 'student':
        s = Student.query.filter_by(user_id=current_user.id).first()
        if not s or s.id_student != student_id: return redirect(url_for('index'))
    
    student = Student.query.get_or_404(student_id)
    materii_obligatorii = Disciplina.query.filter_by(specializare=student.specializare, an_studiu=student.an_studiu).all()
    
    lista_note = []
    lista_prezente = []
    for mat in materii_obligatorii:
        note_db = Notare.query.filter_by(id_student=student.id_student, id_disciplina=mat.id_disciplina).all()
        media = sum([n.nota for n in note_db]) / len(note_db) if note_db else 0
        lista_note.append({'materia': mat.nume_disciplina, 'credite': mat.credite, 'media': media if media > 0 else "-"})
        
        total = Prezenta.query.filter_by(id_student=student.id_student, id_disciplina=mat.id_disciplina).count()
        prez = Prezenta.query.filter_by(id_student=student.id_student, id_disciplina=mat.id_disciplina, status='prezent').count()
        lista_prezente.append({'materia': mat.nume_disciplina, 'prezent': prez, 'total': total, 'rata_text': f"{(prez/total*100):.0f}%" if total else "0%"})

    note = db.session.query(Notare.nota, Notare.data_notare).filter(Notare.id_student==student_id).order_by(Notare.data_notare).all()
    graph_url = None
    if len(note) > 1:
        df = pd.DataFrame(note, columns=['Nota', 'Data']); df['Media'] = df['Nota'].expanding().mean()
        plt.figure(figsize=(8,4)); plt.plot(df['Data'], df['Media'], marker='o'); plt.tight_layout()
        img = io.BytesIO(); plt.savefig(img, format='png'); img.seek(0); graph_url = base64.b64encode(img.getvalue()).decode(); plt.close()
    return render_template('raport_student.html', student=student, lista_note=lista_note, lista_prezente=lista_prezente, graph_data=graph_url)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        seed_discipline()
    app.run(debug=True)