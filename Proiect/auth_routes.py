from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Student, Profesor
import random
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        
        u = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        if u and check_password_hash(u.password, password):
            if not u.is_approved: 
                flash('Contul tău nu a fost încă aprobat de administrator.', 'warning')
                return render_template('login.html')
            login_user(u)
            return redirect(url_for('index'))
        flash('Nume de utilizator/email sau parolă incorectă.', 'danger')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nume = request.form['nume']
        prenume = request.form['prenume']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']
        
        if password != confirm_password:
            flash('Parolele nu coincid!', 'danger')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Există deja un cont cu acest email!', 'danger')
            return redirect(url_for('auth.register'))
        
        # Generează username în formatul nume.prenume
        base_username = f"{prenume.lower()}.{nume.lower()}".replace(" ", "")
        username = base_username
        counter = 1
        
        while User.query.filter_by(username=username).first():
            username = f"{base_username}{counter}"
            counter += 1
        
        new_user = User(
            username=username, 
            email=email, 
            password=generate_password_hash(password), 
            role=role, 
            is_approved=False
        )
        db.session.add(new_user)
        db.session.commit()
        
        if role == 'student':
            student = Student(
                nume=nume, 
                prenume=prenume, 
                nr_matricol=request.form['nr_matricol'], 
                grupa=f"C{request.form['an_studiu']}", 
                an_studiu=int(request.form['an_studiu']), 
                specializare=request.form['specializare'], 
                user_id=new_user.id
            )
            db.session.add(student)
        else:
            profesor = Profesor(
                nume=nume, 
                prenume=prenume, 
                user_id=new_user.id
            )
            db.session.add(profesor)
        
        db.session.commit()
        flash(f'Cont creat cu succes cu numele de utilizator: {username}. Așteaptă aprobarea administratorului.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout(): 
    logout_user()
    response = redirect(url_for('auth.login'))
    # Previne cache-ul browserului pentru a nu permite revenirea cu butonul back
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generează token de resetare
            reset_token = secrets.token_urlsafe(32)
            user.reset_token = reset_token
            user.reset_token_expiry = datetime.now() + timedelta(hours=1)  # Token valid 1 oră
            db.session.commit()
            
            # În producție, aici ai trimite email-ul
            # Pentru dezvoltare, afișăm doar un mesaj
            flash(f'Un link de resetare a fost trimis la {email}. Token: {reset_token}', 'info')
            return redirect(url_for('auth.login'))
        else:
            flash('Nu există niciun cont cu acest email.', 'danger')
    
    return render_template('forgot_password.html')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.reset_token_expiry or user.reset_token_expiry < datetime.now():
        flash('Token-ul de resetare este invalid sau a expirat.', 'danger')
        return redirect(url_for('auth.forgot_password'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Parolele nu coincid!', 'danger')
            return render_template('reset_password.html', token=token)
        
        user.password = generate_password_hash(password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        
        flash('Parola a fost resetată cu succes!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('reset_password.html', token=token)