from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime, date

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    is_approved = db.Column(db.Boolean, default=False)
    reset_token = db.Column(db.String(100), nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)
    
    student_profile = db.relationship('Student', backref='user_account', uselist=False, cascade="all, delete-orphan")
    profesor_profile = db.relationship('Profesor', backref='user_account', uselist=False, cascade="all, delete-orphan")

class Mesaj(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    text = db.Column(db.Text, nullable=True)
    fisier = db.Column(db.String(255), nullable=True)
    data_trimitere = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)
    data_citire = db.Column(db.DateTime, nullable=True)

class Profesor(db.Model):
    id_profesor = db.Column(db.Integer, primary_key=True)
    nume = db.Column(db.String(50), nullable=False)
    prenume = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    def get_full_name(self): 
        return f"{self.nume} {self.prenume}"

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
    
    # Ponderi Note (seminarul nu contribuie la nota finala)
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
    
    def get_full_name(self): 
        return self.nume_disciplina
    
    def calculeaza_nota_finala(self, nota_examen, nota_laborator, nota_proiect):
        """Calculează nota finală conform sistemului IETI"""
        # Seminarul nu contribuie la nota finală
        total_pondere = self.pondere_examen + self.pondere_laborator + self.pondere_proiect
        
        if total_pondere == 0:
            return 0
            
        nota_finala = (
            (nota_examen or 0) * self.pondere_examen + 
            (nota_laborator or 0) * self.pondere_laborator + 
            (nota_proiect or 0) * self.pondere_proiect
        ) / total_pondere
        
        return nota_finala

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
    
    def get_full_name(self): 
        return f"{self.nume} {self.prenume}"

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