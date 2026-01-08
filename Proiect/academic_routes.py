from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort
from flask_login import login_required, current_user
from models import db, Disciplina, Profesor, Student, Inscriere, Notare, Prezenta, User
from sqlalchemy import or_

academic_bp = Blueprint('academic', __name__)

@academic_bp.route('/lista_profesori')
@login_required
def lista_profesori(): 
    return render_template('lista_profesori.html', profesori=Profesor.query.all())

@academic_bp.route('/lista_discipline') 
@login_required
def lista_discipline(): 
    discipline = Disciplina.query.order_by(
        Disciplina.specializare, 
        Disciplina.an_studiu, 
        Disciplina.semestru
    ).all()
    profesori = Profesor.query.all()
    return render_template('lista_discipline.html', discipline=discipline, profesori=profesori)

@academic_bp.route('/admin/discipline')
@login_required
def admin_discipline(): 
    return lista_discipline()

@academic_bp.route('/admin/asignare_complexa', methods=['POST'])
@login_required
def admin_asignare():
    # Verifică dacă utilizatorul este admin
    if current_user.role != 'admin':
        flash('Nu ai permisiunea să asignezi profesori!', 'danger')
        return redirect(url_for('academic.lista_discipline'))
    
    try:
        id_disciplina = request.form.get('id_disciplina')
        if not id_disciplina:
            flash('ID disciplină lipsește!', 'danger')
            return redirect(url_for('academic.lista_discipline'))
            
        d = Disciplina.query.get(int(id_disciplina))
        if not d:
            flash('Disciplina nu a fost găsită!', 'danger')
            return redirect(url_for('academic.lista_discipline'))
        
        # Debug: afișează datele primite
        print(f"Asignare pentru disciplina: {d.nume_disciplina}")
        print(f"Form data: {dict(request.form)}")
        
        # Asignează profesorii
        titular_id = request.form.get('titular')
        d.id_titular = int(titular_id) if titular_id and titular_id != '' else None
        
        if d.has_laborator: 
            laborant_id = request.form.get('laborant')
            d.id_laborant = int(laborant_id) if laborant_id and laborant_id != '' else None
            
        if d.has_seminar: 
            seminarist_id = request.form.get('seminarist')
            d.id_seminarist = int(seminarist_id) if seminarist_id and seminarist_id != '' else None
            
        if d.has_proiect: 
            proiectant_id = request.form.get('proiectant')
            d.id_proiectant = int(proiectant_id) if proiectant_id and proiectant_id != '' else None
        
        db.session.commit()
        
        # Mesaj de succes cu detalii
        assigned_profs = []
        if d.id_titular:
            prof = Profesor.query.get(d.id_titular)
            if prof:
                assigned_profs.append(f"Titular: {prof.get_full_name()}")
        if d.has_laborator and d.id_laborant:
            prof = Profesor.query.get(d.id_laborant)
            if prof:
                assigned_profs.append(f"Laborator: {prof.get_full_name()}")
        if d.has_seminar and d.id_seminarist:
            prof = Profesor.query.get(d.id_seminarist)
            if prof:
                assigned_profs.append(f"Seminar: {prof.get_full_name()}")
        if d.has_proiect and d.id_proiectant:
            prof = Profesor.query.get(d.id_proiectant)
            if prof:
                assigned_profs.append(f"Proiect: {prof.get_full_name()}")
        
        success_msg = f'Profesorii au fost asignați cu succes pentru "{d.nume_disciplina}"!'
        if assigned_profs:
            success_msg += f' ({", ".join(assigned_profs)})'
        
        flash(success_msg, 'success')
        
    except ValueError as ve:
        db.session.rollback()
        flash(f'Eroare la procesarea datelor: {str(ve)}', 'danger')
        print(f"ValueError in admin_asignare: {ve}")
    except Exception as e:
        db.session.rollback()
        flash('A apărut o eroare la asignarea profesorilor!', 'danger')
        print(f"Error in admin_asignare: {e}")
        print(f"Form data: {dict(request.form)}")
    
    return redirect(url_for('academic.lista_discipline'))

@academic_bp.route('/materie/<int:id_disc>', methods=['GET', 'POST'])
@login_required
def panou_materie(id_disc):
    d = Disciplina.query.get_or_404(id_disc)
    prof = Profesor.query.filter_by(user_id=current_user.id).first()
    
    is_titular = prof and (d.id_titular == prof.id_profesor)
    is_laborant = prof and (d.id_laborant == prof.id_profesor)
    is_seminarist = prof and (d.id_seminarist == prof.id_profesor)
    is_proiectant = prof and (d.id_proiectant == prof.id_profesor)
    is_admin = current_user.role == 'admin'
    
    if not (is_titular or is_laborant or is_seminarist or is_proiectant or is_admin): 
        abort(403)
    
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
    toti_studentii = Student.query.all()
    studenti_neinscrisi = [s for s in toti_studentii if s not in studenti_inscrisi]

    # Pre-fetch Note pentru afisare
    note_q = Notare.query.filter_by(id_disciplina=d.id_disciplina).all()
    note_map = {}
    for n in note_q:
        if n.id_student not in note_map: 
            note_map[n.id_student] = {}
        note_map[n.id_student][n.tip_activitate] = n.nota

    return render_template('vizualizare_materie.html', 
                         disciplina=d, 
                         studenti=studenti_inscrisi, 
                         studenti_neinscrisi=studenti_neinscrisi, 
                         is_titular=is_titular, 
                         is_admin=is_admin, 
                         note_map=note_map)

@academic_bp.route('/adauga_nota_completa', methods=['POST'])
@login_required
def adauga_nota_completa():
    # Șterge nota existentă dacă există
    Notare.query.filter_by(
        id_student=request.form['id_student'], 
        id_disciplina=request.form['id_disciplina'], 
        tip_activitate=request.form['tip_activitate']
    ).delete()
    
    # Adaugă nota nouă
    nota_noua = Notare(
        id_student=request.form['id_student'], 
        id_disciplina=request.form['id_disciplina'], 
        tip_activitate=request.form['tip_activitate'], 
        nota=float(request.form['nota'])
    )
    db.session.add(nota_noua)
    db.session.commit()
    
    return redirect(url_for('academic.panou_materie', id_disc=request.form['id_disciplina']))

@academic_bp.route('/reset_nota', methods=['POST'])
@login_required
def reset_nota():
    Notare.query.filter_by(
        id_student=request.form['id_student'], 
        id_disciplina=request.form['id_disciplina'], 
        tip_activitate=request.form['tip_activitate']
    ).delete()
    db.session.commit()
    return redirect(url_for('academic.panou_materie', id_disc=request.form['id_disciplina']))

@academic_bp.route('/enroll_student', methods=['POST'])
@login_required
def enroll_student():
    inscriere = Inscriere(
        id_student=request.form['id_student'], 
        id_disciplina=request.form['id_disciplina']
    )
    db.session.add(inscriere)
    db.session.commit()
    return redirect(url_for('academic.panou_materie', id_disc=request.form['id_disciplina']))

@academic_bp.route('/enroll_all_eligible', methods=['POST'])
@login_required
def enroll_all_eligible():
    d = Disciplina.query.get(request.form['id_disciplina'])
    eligibili = Student.query.filter_by(
        specializare=d.specializare, 
        an_studiu=d.an_studiu
    ).all()
    
    for s in eligibili:
        existing = Inscriere.query.filter_by(
            id_student=s.id_student, 
            id_disciplina=d.id_disciplina
        ).first()
        
        if not existing:
            inscriere = Inscriere(
                id_student=s.id_student, 
                id_disciplina=d.id_disciplina
            )
            db.session.add(inscriere)
    
    db.session.commit()
    return redirect(url_for('academic.panou_materie', id_disc=d.id_disciplina))

@academic_bp.route('/remove_student', methods=['POST'])
@login_required
def remove_student():
    ins = Inscriere.query.filter_by(
        id_student=request.form['id_student'], 
        id_disciplina=request.form['id_disciplina']
    ).first()
    
    if ins: 
        db.session.delete(ins)
        db.session.commit()
    
    return redirect(url_for('academic.panou_materie', id_disc=request.form['id_disciplina']))

@academic_bp.route('/update_prezenta', methods=['POST'])
@login_required
def update_prezenta():
    data = request.json
    
    # Șterge prezențele existente
    Prezenta.query.filter_by(
        id_student=data['id_student'], 
        id_disciplina=data['id_disciplina'], 
        tip_activitate=data['tip_activitate']
    ).delete()
    
    # Adaugă prezențele noi
    for sapt in data['weeks']: 
        prezenta = Prezenta(
            id_student=data['id_student'], 
            id_disciplina=data['id_disciplina'], 
            tip_activitate=data['tip_activitate'], 
            saptamana=int(sapt), 
            is_prezent=True
        )
        db.session.add(prezenta)
    
    db.session.commit()
    return jsonify({'status': 'success'})

@academic_bp.route('/get_prezente_student')
@login_required
def get_prezente_student():
    prezente = Prezenta.query.filter_by(
        id_student=request.args.get('id_student'), 
        id_disciplina=request.args.get('id_disciplina'), 
        tip_activitate=request.args.get('tip_activitate')
    ).all()
    
    return jsonify([p.saptamana for p in prezente])

@academic_bp.route('/raport/student/<int:student_id>')
@login_required
def raport_student_general(student_id):
    s = Student.query.get_or_404(student_id)
    inscrieri = Inscriere.query.filter_by(id_student=s.id_student).all()
    
    situatie_sem1 = []
    situatie_sem2 = []
    note_sem1 = []
    note_sem2 = []
    
    for ins in inscrieri:
        m = ins.disciplina
        
        # Obține notele pentru fiecare tip de activitate
        n_exam = Notare.query.filter_by(
            id_student=s.id_student, 
            id_disciplina=m.id_disciplina, 
            tip_activitate='Examen'
        ).first()
        
        n_lab = Notare.query.filter_by(
            id_student=s.id_student, 
            id_disciplina=m.id_disciplina, 
            tip_activitate='Laborator'
        ).first()
        
        n_pro = Notare.query.filter_by(
            id_student=s.id_student, 
            id_disciplina=m.id_disciplina, 
            tip_activitate='Proiect'
        ).first()
        
        nota_ex = n_exam.nota if n_exam else 0
        nota_lab = n_lab.nota if n_lab else 0
        nota_pro = n_pro.nota if n_pro else 0
        
        # Calculează media finală folosind noua metodă
        media = m.calculeaza_nota_finala(nota_ex, nota_lab, nota_pro)
        
        # Verifică prezențele
        p_cur = Prezenta.query.filter_by(
            id_student=s.id_student, 
            id_disciplina=m.id_disciplina, 
            tip_activitate='curs'
        ).count()
        
        p_lab = Prezenta.query.filter_by(
            id_student=s.id_student, 
            id_disciplina=m.id_disciplina, 
            tip_activitate='laborator'
        ).count()
        
        # Determină statusul
        status = "Promovat"
        if (p_cur/14)*100 < m.min_prez_curs:
            status = "Refacere"
            media = 0
        elif m.has_laborator and (p_lab/14)*100 < m.min_prez_laborator:
            status = "Refacere"
            media = 0
        elif media < 5:
            status = "Nepromovat"
        
        if media > 0: 
            if m.semestru == 1:
                note_sem1.append(media)
            else:
                note_sem2.append(media)
        
        item = {
            'nume': m.nume_disciplina, 
            'credite': m.credite, 
            'nota_exam': nota_ex or '-', 
            'nota_lab': nota_lab or '-', 
            'nota_pro': nota_pro or '-', 
            'medie_finala': f"{media:.2f}" if media else '0.00', 
            'status': status, 
            'clasa_status': 'text-danger' if status != 'Promovat' else 'text-success', 
            'prezente_detalii': f"C:{p_cur}" + (f" L:{p_lab}" if m.has_laborator else "")
        }
        
        if m.semestru == 1:
            situatie_sem1.append(item)
        else:
            situatie_sem2.append(item)
        
    avg1 = sum(note_sem1)/len(note_sem1) if note_sem1 else 0
    avg2 = sum(note_sem2)/len(note_sem2) if note_sem2 else 0
    avg_an = (avg1+avg2)/2 if avg1 and avg2 else (avg1 or avg2)
    
    return render_template('raport_student.html', 
                         student=s, 
                         sem1=situatie_sem1, 
                         sem2=situatie_sem2, 
                         avg1=f"{avg1:.2f}", 
                         avg2=f"{avg2:.2f}", 
                         avg_an=f"{avg_an:.2f}")