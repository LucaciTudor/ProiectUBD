from models import db, Disciplina

def seed_discipline():
    """Populează baza de date cu disciplinele IETI Oradea"""
    if Disciplina.query.first(): 
        return
    
    # Format: (Nume, Credite, An, Sem, Specializare, has_lab, has_sem, has_proiect, pond_exam, pond_lab, pond_proj)
    materii = [
        # === CALCULATOARE (CTI) ===
        # Anul 1
        ("Analiza Matematica", 5, 1, 1, "Calculatoare", False, True, False, 100, 0, 0),
        ("Algebra si Geometrie", 5, 1, 1, "Calculatoare", False, True, False, 100, 0, 0),
        ("Fizica", 4, 1, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Programarea Calculatoarelor", 6, 1, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Bazele Electrotehnicii", 5, 1, 2, "Calculatoare", True, True, False, 60, 40, 0),
        ("Structuri de Date", 6, 1, 2, "Calculatoare", True, False, True, 40, 30, 30),
        ("Matematici Speciale", 4, 1, 2, "Calculatoare", False, True, False, 100, 0, 0),
        
        # Anul 2
        ("Programare Orientata pe Obiecte", 6, 2, 1, "Calculatoare", True, False, True, 40, 30, 30),
        ("Teoria Sistemelor", 5, 2, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Electronica Digitala", 5, 2, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Limbaje de Asamblare", 5, 2, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Sisteme de Operare", 5, 2, 2, "Calculatoare", True, False, False, 60, 40, 0),
        ("Arhitectura Calculatoarelor", 6, 2, 2, "Calculatoare", True, False, False, 60, 40, 0),
        ("Proiectare Algoritmi", 5, 2, 2, "Calculatoare", True, False, False, 60, 40, 0),
        ("Masurari Electronice", 4, 2, 2, "Calculatoare", True, False, False, 60, 40, 0),

        # Anul 3
        ("Baze de Date", 6, 3, 1, "Calculatoare", True, False, True, 40, 30, 30),
        ("Retele de Calculatoare", 6, 3, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Inginerie Software", 5, 3, 1, "Calculatoare", True, False, True, 40, 30, 30),
        ("Calculatoare Numerice", 5, 3, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Inteligenta Artificiala", 5, 3, 2, "Calculatoare", True, False, False, 60, 40, 0),
        ("Sisteme Incorporate", 5, 3, 2, "Calculatoare", True, False, True, 40, 30, 30),
        ("Grafica pe Calculator", 5, 3, 2, "Calculatoare", True, False, False, 60, 40, 0),
        
        # Anul 4
        ("Securitatea Sistemelor", 5, 4, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Interfete Om-Calculator", 4, 4, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Sisteme Distribuite", 5, 4, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Testarea Sistemelor", 4, 4, 1, "Calculatoare", True, False, False, 60, 40, 0),
        ("Elaborare Proiect Diploma", 10, 4, 2, "Calculatoare", False, False, True, 0, 0, 100),
        ("Practica de Specialitate", 5, 4, 2, "Calculatoare", False, False, True, 0, 0, 100),

        # === AUTOMATICA (AIA) ===
        # Anul 1
        ("Analiza Matematica", 5, 1, 1, "Automatica", False, True, False, 100, 0, 0),
        ("Fizica", 4, 1, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Chimie", 3, 1, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Programarea Calculatoarelor", 6, 1, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Mecanica", 5, 1, 2, "Automatica", False, True, False, 100, 0, 0),
        ("Electrotehnica", 5, 1, 2, "Automatica", True, False, False, 60, 40, 0),
        ("Grafica Asistata", 4, 1, 2, "Automatica", True, False, False, 60, 40, 0),

        # Anul 2
        ("Electronica Analogica", 5, 2, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Teoria Sistemelor Automate 1", 6, 2, 1, "Automatica", True, True, False, 60, 40, 0),
        ("Electronica Digitala", 5, 2, 2, "Automatica", True, False, False, 60, 40, 0),
        ("Teoria Sistemelor Automate 2", 6, 2, 2, "Automatica", True, False, True, 40, 30, 30),
        ("Masurari si Traductoare", 5, 2, 2, "Automatica", True, False, False, 60, 40, 0),

        # Anul 3
        ("Ingineria Reglarii Automate", 6, 3, 1, "Automatica", True, False, True, 40, 30, 30),
        ("Identificarea Sistemelor", 5, 3, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Echipamente de Automatizare", 5, 3, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Modelare si Simulare", 5, 3, 2, "Automatica", True, False, True, 40, 30, 30),
        ("Automate Programabile", 5, 3, 2, "Automatica", True, False, False, 60, 40, 0),
        ("Sisteme cu Microprocesoare", 5, 3, 2, "Automatica", True, False, False, 60, 40, 0),

        # Anul 4
        ("Robotica", 5, 4, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Sisteme de Conducere a Fabricației", 5, 4, 1, "Automatica", True, False, True, 40, 30, 30),
        ("Inginerie Software pt. Control", 4, 4, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Sisteme Scada", 4, 4, 1, "Automatica", True, False, False, 60, 40, 0),
        ("Proiect Diploma", 10, 4, 2, "Automatica", False, False, True, 0, 0, 100),

        # === ELECTRONICA APLICATA (EA) ===
        # Anul 1
        ("Matematici Speciale", 5, 1, 1, "Electronica Aplicata", False, True, False, 100, 0, 0),
        ("Fizica Tehnica", 4, 1, 1, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Componente si Dispozitive Electronice", 6, 1, 2, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Materiale pentru Electronica", 4, 1, 2, "Electronica Aplicata", True, False, False, 60, 40, 0),
        
        # Anul 2
        ("Semnale si Sisteme", 5, 2, 1, "Electronica Aplicata", False, True, False, 100, 0, 0),
        ("Circuite Integrate Digitale", 5, 2, 1, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Prelucrarea Semnalelor", 5, 2, 2, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Circuite Electronice Fundamentale", 6, 2, 2, "Electronica Aplicata", True, False, True, 40, 30, 30),

        # Anul 3
        ("Microcontrolere", 6, 3, 1, "Electronica Aplicata", True, False, True, 40, 30, 30),
        ("Sisteme de Achizitie Date", 5, 3, 1, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Electronică de Putere", 5, 3, 2, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Comunicatii Mobile", 4, 3, 2, "Electronica Aplicata", False, True, False, 100, 0, 0),

        # Anul 4
        ("Televiziune", 5, 4, 1, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Optoelectronica", 4, 4, 1, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Sisteme Audio-Video", 5, 4, 1, "Electronica Aplicata", True, False, False, 60, 40, 0),
        ("Proiect Licenta", 10, 4, 2, "Electronica Aplicata", False, False, True, 0, 0, 100),

        # === TEHNOLOGIA INFORMATIEI (TI) ===
        # Anul 1
        ("Programare C", 5, 1, 1, "Tehnologia Informatiei", True, False, False, 60, 40, 0),
        ("Arhitectura Sistemelor de Calcul", 5, 1, 1, "Tehnologia Informatiei", True, False, False, 60, 40, 0),
        ("Algoritmi si Structuri de Date", 6, 1, 2, "Tehnologia Informatiei", True, False, False, 60, 40, 0),
        ("Bazele Electrotehnicii", 5, 1, 2, "Tehnologia Informatiei", True, True, False, 60, 40, 0),

        # Anul 2
        ("Bazele Comunicatiilor", 5, 2, 1, "Tehnologia Informatiei", True, False, False, 60, 40, 0),
        ("Programare Java", 5, 2, 1, "Tehnologia Informatiei", True, False, True, 40, 30, 30),
        ("Protocoale de Comunicatii", 5, 2, 2, "Tehnologia Informatiei", True, False, False, 60, 40, 0),
        ("Prelucrarea Digitala a Semnalelor", 5, 2, 2, "Tehnologia Informatiei", True, False, False, 60, 40, 0),

        # Anul 3
        ("Tehnologii WEB", 5, 3, 1, "Tehnologia Informatiei", True, False, True, 40, 30, 30),
        ("Baze de Date Relationale", 6, 3, 1, "Tehnologia Informatiei", True, False, False, 60, 40, 0),
        ("Multimedia", 5, 3, 2, "Tehnologia Informatiei", True, False, True, 40, 30, 30),
        ("Administrare Retele", 5, 3, 2, "Tehnologia Informatiei", True, False, False, 60, 40, 0),

        # Anul 4
        ("Securitate Cibernetica", 5, 4, 1, "Tehnologia Informatiei", True, False, False, 60, 40, 0),
        ("Cloud Computing", 5, 4, 1, "Tehnologia Informatiei", True, False, False, 60, 40, 0),
        ("Comert Electronic", 4, 4, 1, "Tehnologia Informatiei", False, True, False, 100, 0, 0),
        ("Internet of Things", 5, 4, 1, "Tehnologia Informatiei", True, False, True, 40, 30, 30),
        ("Elaborare Lucrare Licenta", 10, 4, 2, "Tehnologia Informatiei", False, False, True, 0, 0, 100),
    ]

    for nume, credite, an, sem, spec, has_lab, has_sem, has_pro, p_exam, p_lab, p_pro in materii:
        db.session.add(Disciplina(
            nume_disciplina=nume, 
            credite=credite, 
            an_studiu=an, 
            specializare=spec, 
            semestru=sem,
            has_laborator=has_lab, 
            has_seminar=has_sem, 
            has_proiect=has_pro,
            pondere_examen=p_exam, 
            pondere_laborator=p_lab, 
            pondere_proiect=p_pro,
            min_prez_curs=50, 
            min_prez_laborator=100, 
            min_prez_seminar=80, 
            min_prez_proiect=100
        ))
    
    db.session.commit()
    print("Disciplinele IETI Oradea au fost încărcate cu succes!")