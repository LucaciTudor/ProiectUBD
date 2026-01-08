from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Student, Profesor, Inscriere, Disciplina

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin/utilizatori')
@login_required
def gestiune_utilizatori(): 
    if current_user.role != 'admin':
        flash('Acces interzis!', 'danger')
        return redirect(url_for('index'))
    
    pending_users = User.query.filter_by(is_approved=False).all()
    active_users = User.query.filter_by(is_approved=True).all()
    
    return render_template('admin_users.html', 
                         pending_users=pending_users, 
                         active_users=active_users)

@admin_bp.route('/admin/aproba_user/<int:user_id>')
@login_required
def aproba_user(user_id):
    if current_user.role != 'admin':
        flash('Acces interzis!', 'danger')
        return redirect(url_for('index'))
    
    u = User.query.get(user_id)
    u.is_approved = True
    db.session.commit()
    
    # Dacă este student, înscrie-l automat la materiile corespunzătoare
    if u.role == 'student' and u.student_profile:
        s = u.student_profile
        materii = Disciplina.query.filter_by(
            specializare=s.specializare, 
            an_studiu=s.an_studiu
        ).all()
        
        for m in materii:
            existing = Inscriere.query.filter_by(
                id_student=s.id_student, 
                id_disciplina=m.id_disciplina
            ).first()
            
            if not existing:
                inscriere = Inscriere(
                    id_student=s.id_student, 
                    id_disciplina=m.id_disciplina
                )
                db.session.add(inscriere)
        
        db.session.commit()
    
    flash(f'Utilizatorul {u.username} a fost aprobat!', 'success')
    return redirect(url_for('admin.gestiune_utilizatori'))

@admin_bp.route('/admin/sterge_user/<int:user_id>')
@login_required
def sterge_utilizator(user_id):
    if current_user.role != 'admin':
        flash('Acces interzis!', 'danger')
        return redirect(url_for('index'))
    
    user = User.query.get(user_id)
    username = user.username
    db.session.delete(user)
    db.session.commit()
    
    flash(f'Utilizatorul {username} a fost șters!', 'success')
    return redirect(url_for('admin.gestiune_utilizatori'))

@admin_bp.route('/sterge_student/<int:id_student>')
@login_required
def sterge_student(id_student):
    if current_user.role != 'admin':
        flash('Acces interzis!', 'danger')
        return redirect(url_for('index'))
    
    student = Student.query.get(id_student)
    db.session.delete(student)
    db.session.commit()
    
    flash('Studentul a fost șters!', 'success')
    return redirect(url_for('index'))

@admin_bp.route('/sterge_profesor/<int:id_profesor>')
@login_required
def sterge_profesor(id_profesor):
    if current_user.role != 'admin':
        flash('Acces interzis!', 'danger')
        return redirect(url_for('index'))
    
    profesor = Profesor.query.get(id_profesor)
    db.session.delete(profesor)
    db.session.commit()
    
    flash('Profesorul a fost șters!', 'success')
    return redirect(url_for('index'))

@admin_bp.route('/editeaza_student/<int:id_student>', methods=['GET', 'POST'])
@login_required
def editeaza_student(id_student):
    if current_user.role != 'admin':
        flash('Acces interzis!', 'danger')
        return redirect(url_for('index'))
    
    s = Student.query.get_or_404(id_student)
    
    if request.method == 'POST':
        s.nume = request.form['nume']
        s.prenume = request.form['prenume']
        s.nr_matricol = request.form['nr_matricol']
        s.an_studiu = int(request.form['an_studiu'])
        s.specializare = request.form['specializare']
        
        db.session.commit()
        flash('Datele studentului au fost actualizate!', 'success')
        return redirect(url_for('index'))
    
    return render_template('editeaza_student.html', student=s)