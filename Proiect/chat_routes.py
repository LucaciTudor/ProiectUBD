from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Mesaj
from datetime import datetime
import os

chat_bp = Blueprint('chat', __name__)

@chat_bp.route('/chat')
@login_required
def chat_home():
    sent = db.session.query(Mesaj.receiver_id).filter(Mesaj.sender_id == current_user.id)
    received = db.session.query(Mesaj.sender_id).filter(Mesaj.receiver_id == current_user.id)
    contact_ids = sent.union(received).distinct().all()
    contacts = [User.query.get(cid) for (cid,) in contact_ids]
    
    # Obține numărul de mesaje necitite pentru fiecare contact
    mesaje_necitite = {}
    for contact in contacts:
        count = Mesaj.query.filter_by(sender_id=contact.id, receiver_id=current_user.id, is_read=False).count()
        if count > 0:
            mesaje_necitite[contact.id] = count
    
    return render_template('chat.html', contacts=contacts, active_chat=None, mesaje_necitite=mesaje_necitite)

@chat_bp.route('/chat/<int:user_id>', methods=['GET', 'POST'])
@login_required
def chat_with(user_id):
    partner = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        msg = request.form.get('mesaj')
        file = request.files.get('fisier')
        fname = None
        
        if file and file.filename:
            from flask import current_app
            fname = secure_filename(f"{int(datetime.now().timestamp())}_{file.filename}")
            file.save(os.path.join(current_app.config['CHAT_UPLOAD_FOLDER'], fname))
        
        if msg or fname:
            new_message = Mesaj(
                sender_id=current_user.id, 
                receiver_id=user_id, 
                text=msg, 
                fisier=fname
            )
            db.session.add(new_message)
            db.session.commit()
        
        return redirect(url_for('chat.chat_with', user_id=user_id))
    
    # Marchează mesajele primite ca citite
    mesaje_necitite = Mesaj.query.filter_by(
        sender_id=user_id, 
        receiver_id=current_user.id, 
        is_read=False
    ).all()
    
    for mesaj in mesaje_necitite:
        mesaj.is_read = True
        mesaj.data_citire = datetime.now()
    db.session.commit()
    
    # Obține toate mesajele din conversație
    mesaje = Mesaj.query.filter(
        ((Mesaj.sender_id == current_user.id) & (Mesaj.receiver_id == user_id)) | 
        ((Mesaj.sender_id == user_id) & (Mesaj.receiver_id == current_user.id))
    ).order_by(Mesaj.data_trimitere.asc()).all()
    
    # Obține lista de contacte
    sent = db.session.query(Mesaj.receiver_id).filter(Mesaj.sender_id == current_user.id)
    received = db.session.query(Mesaj.sender_id).filter(Mesaj.receiver_id == current_user.id)
    contact_ids = sent.union(received).distinct().all()
    contacts = [User.query.get(cid) for (cid,) in contact_ids]
    
    if partner not in contacts: 
        contacts.insert(0, partner)
    
    # Obține numărul de mesaje necitite pentru fiecare contact (excluzând contactul curent)
    mesaje_necitite_dict = {}
    for contact in contacts:
        if contact.id != user_id:
            count = Mesaj.query.filter_by(
                sender_id=contact.id, 
                receiver_id=current_user.id, 
                is_read=False
            ).count()
            if count > 0:
                mesaje_necitite_dict[contact.id] = count
    
    return render_template('chat.html', 
                         contacts=contacts, 
                         active_chat=partner, 
                         mesaje=mesaje, 
                         mesaje_necitite=mesaje_necitite_dict)

@chat_bp.route('/api/search_users')
@login_required
def api_search_users():
    q = request.args.get('q', '')
    if len(q) < 2: 
        return jsonify([])
    
    users = User.query.filter(
        User.username.ilike(f'%{q}%'), 
        User.is_approved == True, 
        User.id != current_user.id
    ).limit(10).all()
    
    result = []
    for u in users:
        full_name = u.username
        if u.student_profile:
            full_name = u.student_profile.get_full_name()
        elif u.profesor_profile:
            full_name = u.profesor_profile.get_full_name()
        
        result.append({
            'id': u.id, 
            'username': u.username, 
            'full_name': full_name, 
            'role': u.role
        })
    
    return jsonify(result)

@chat_bp.route('/api/unread_messages')
@login_required
def api_unread_messages():
    """Returnează numărul de mesaje necitite pentru utilizatorul curent"""
    unread_count = Mesaj.query.filter_by(receiver_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': unread_count})

@chat_bp.route('/api/unread_messages_by_user')
@login_required
def api_unread_messages_by_user():
    """Returnează numărul de mesaje necitite pentru fiecare utilizator"""
    unread_messages = db.session.query(
        Mesaj.sender_id, 
        db.func.count(Mesaj.id).label('count')
    ).filter_by(
        receiver_id=current_user.id, 
        is_read=False
    ).group_by(Mesaj.sender_id).all()
    
    result = {}
    for sender_id, count in unread_messages:
        result[sender_id] = count
    
    return jsonify(result)