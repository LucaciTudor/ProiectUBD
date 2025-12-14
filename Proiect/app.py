from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import date
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import base64

# 1. INITIALIZARE APLICATIE
app = Flask(__name__)
app.config['SECRET_KEY'] = 'cheie_secreta_proiect_student'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///catalog_scoala.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- SETUP FLASK-LOGIN (NOU) ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Daca nu esti logat, te trimite aici

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 2. DEFINITIA MODELELOR (BAZA DE DATE)

# --- MODEL UTILIZATOR (NOU) ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False) # Parola va fi criptată

class Profesor(db.Model):
    id_profesor = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(50), nullable=False)
    prenume = db.Column(db.String(50), nullable=False)
    
    def get_full_name(self):
        return f"{self.nume} {self.prenume}"

class Disciplina(db.Model):
    id_disciplina = db.Column(db.Integer, primary_key=True)
    nume_disciplina = db.Column(db.String(100), unique=True, nullable=False)
    credite = db.Column(db.Integer, nullable=False)
    id_profesor_predare = db.Column(db.Integer, db.ForeignKey('profesor.id_profesor'), nullable=True) 
    
    profesor = db.relationship('Profesor', backref='discipline', lazy=True)
    note_primite = db.relationship('Notare', backref='disciplina_notata', lazy=True)
    prezente_inregistrate = db.relationship('Prezenta', backref='disciplina_prezenta', lazy=True)

class Student(db.Model):
    id_student = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(50), nullable=False)
    prenume = db.Column(db.String(50), nullable=False)
    nr_matricol = db.Column(db.String(20), unique=True, nullable=False)
    grupa = db.Column(db.String(10), nullable=False)
    
    note = db.relationship('Notare', backref='student', lazy=True)
    prezente = db.relationship('Prezenta', backref='student', lazy=True)
    
    def get_full_name(self):
        return f"{self.nume} {self.prenume}"

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

# 3. RUTE AUTENTIFICARE (NOU)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Te-ai autentificat cu succes!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email sau parolă incorectă.', 'danger')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        if password != password_confirm:
            flash('Parolele nu coincid!', 'danger')
            return redirect(url_for('register'))
            
        user_exists = User.query.filter_by(username=username).first()
        if user_exists:
            flash('Acest utilizator există deja.', 'danger')
            return redirect(url_for('register'))
            
        # Creare user nou cu parola criptata
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(username=username, password=hashed_password)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('Cont creat! Acum te poți autentifica.', 'success')
            return redirect(url_for('login'))
        except:
            db.session.rollback()
            flash('Eroare la crearea contului.', 'danger')
            
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Te-ai delogat.', 'success')
    return redirect(url_for('login'))


# 4. RUTE PRINCIPALE APLICATIE (SECURIZATE)

@app.route('/')
@login_required # <--- Nu poti intra aici daca nu esti logat
def index():
    studenti = Student.query.all()
    return render_template('index.html', studenti=studenti)

@app.route('/adauga_student', methods=['GET', 'POST'])
@login_required
def adauga_student():
    if request.method == 'POST':
        try:
            new_student = Student(
                nume=request.form['nume'],
                prenume=request.form['prenume'],
                nr_matricol=request.form['nr_matricol'],
                grupa=request.form['grupa']
            )
            db.session.add(new_student)
            db.session.commit()
            flash('Studentul a fost adăugat cu succes!', 'success')
            return redirect(url_for('index'))
        except IntegrityError:
            db.session.rollback()
            flash('Eroare: Numărul matricol există deja.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Eroare: {str(e)}', 'danger')
            
    return render_template('adauga_student.html')

@app.route('/profesori')
@login_required
def lista_profesori():
    profesori = Profesor.query.all()
    return render_template('lista_profesori.html', profesori=profesori)

@app.route('/adauga_profesor', methods=['GET', 'POST'])
@login_required
def adauga_profesor():
    if request.method == 'POST':
        try:
            new_prof = Profesor(
                nume=request.form['nume'],
                prenume=request.form['prenume']
            )
            db.session.add(new_prof)
            db.session.commit()
            flash('Profesorul a fost adăugat!', 'success')
            return redirect(url_for('lista_profesori'))
        except Exception as e:
            db.session.rollback()
            flash(f'Eroare: {str(e)}', 'danger')
    return render_template('adauga_profesor.html')

@app.route('/discipline')
@login_required
def lista_discipline():
    discipline = Disciplina.query.all()
    return render_template('lista_discipline.html', discipline=discipline)

@app.route('/adauga_disciplina', methods=['GET', 'POST'])
@login_required
def adauga_disciplina():
    profesori = Profesor.query.all()
    if request.method == 'POST':
        try:
            prof_id = request.form.get('id_profesor_predare')
            if prof_id == "": prof_id = None
            new_disciplina = Disciplina(
                nume_disciplina=request.form['nume_disciplina'],
                credite=int(request.form['credite']),
                id_profesor_predare=prof_id
            )
            db.session.add(new_disciplina)
            db.session.commit()
            flash('Disciplina a fost adăugată!', 'success')
            return redirect(url_for('lista_discipline'))
        except IntegrityError:
            db.session.rollback()
            flash('O disciplină cu acest nume există deja.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Eroare: {str(e)}', 'danger')
    return render_template('adauga_disciplina.html', profesori=profesori)

@app.route('/adauga_nota', methods=['GET', 'POST'])
@login_required
def adauga_nota():
    studenti = Student.query.all()
    discipline = Disciplina.query.all()
    if request.method == 'POST':
        try:
            nota_val = float(request.form['nota'])
            if not (1 <= nota_val <= 10):
                 flash('Nota trebuie să fie între 1 și 10.', 'danger')
                 return redirect(url_for('adauga_nota'))
            new_notare = Notare(
                id_student=request.form['id_student'],
                id_disciplina=request.form['id_disciplina'],
                nota=nota_val
            )
            db.session.add(new_notare)
            db.session.commit()
            flash(f'Nota {nota_val} a fost salvată!', 'success')
            return redirect(url_for('raport_student_general', student_id=request.form['id_student']))
        except ValueError:
            flash('Nota trebuie să fie un număr valid.', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Eroare: {str(e)}', 'danger')
    return render_template('adauga_nota.html', studenti=studenti, discipline=discipline)

@app.route('/adauga_prezenta', methods=['GET', 'POST'])
@login_required
def adauga_prezenta():
    studenti = Student.query.all()
    discipline = Disciplina.query.all()
    if request.method == 'POST':
        try:
            new_prezenta = Prezenta(
                id_student=request.form['id_student'],
                id_disciplina=request.form['id_disciplina'],
                status=request.form['status']
            )
            db.session.add(new_prezenta)
            db.session.commit()
            flash('Prezența a fost înregistrată!', 'success')
            return redirect(url_for('raport_student_general', student_id=request.form['id_student']))
        except Exception as e:
            db.session.rollback()
            flash(f'Eroare: {str(e)}', 'danger')
    return render_template('adauga_prezenta.html', studenti=studenti, discipline=discipline)

@app.route('/raport/student/<int:student_id>')
@login_required
def raport_student_general(student_id):
    student = Student.query.get_or_404(student_id)
    rezultate_note = db.session.query(
        Disciplina.nume_disciplina,
        db.func.avg(Notare.nota).label('media_nota')
    ).join(Notare).filter(Notare.id_student == student_id).group_by(Disciplina.nume_disciplina).all()
    
    lista_note = []
    for r in rezultate_note:
        lista_note.append({'materia': r.nume_disciplina, 'media': r.media_nota})
    
    disc_note = Disciplina.query.join(Notare).filter(Notare.id_student == student_id).distinct().all()
    disc_prez = Disciplina.query.join(Prezenta).filter(Prezenta.id_student == student_id).distinct().all()
    toate_id_urile = set([d.id_disciplina for d in disc_note] + [d.id_disciplina for d in disc_prez])
    
    lista_prezente = []
    for id_disc in toate_id_urile:
        disciplina = Disciplina.query.get(id_disc)
        total = Prezenta.query.filter_by(id_student=student_id, id_disciplina=id_disc).count()
        prezent = Prezenta.query.filter_by(id_student=student_id, id_disciplina=id_disc, status='prezent').count()
        rata_valoare = (prezent / total * 100) if total > 0 else 0.0
        lista_prezente.append({
            'materia': disciplina.nume_disciplina, 'prezent': prezent, 'total': total,
            'rata_text': f"{rata_valoare:.1f}%", 'rata_valoare': rata_valoare
        })

    note_brute = db.session.query(Notare.nota, Notare.data_notare).filter(Notare.id_student == student_id).order_by(Notare.data_notare).all()
    graph_url = None
    if len(note_brute) > 1:
        try:
            df = pd.DataFrame(note_brute, columns=['Nota', 'Data'])
            df['Media_Cumulativa'] = df['Nota'].expanding().mean()
            plt.figure(figsize=(10, 5))
            plt.plot(df['Data'], df['Media_Cumulativa'], marker='o', linestyle='-', color='#007bff', linewidth=2)
            plt.title(f'Evoluția Mediei - {student.get_full_name()}')
            plt.grid(True, linestyle='--', alpha=0.5)
            plt.tight_layout()
            img = io.BytesIO()
            plt.savefig(img, format='png')
            img.seek(0)
            graph_url = base64.b64encode(img.getvalue()).decode()
            plt.close()
        except Exception:
            graph_url = None

    return render_template('raport_student.html', student=student, lista_note=lista_note, lista_prezente=lista_prezente, graph_data=graph_url)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)