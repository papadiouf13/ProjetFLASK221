from flask import Flask, render_template, session, redirect, url_for, request, flash
from bson import ObjectId
from flask_pymongo import PyMongo
import bcrypt
from functools import wraps

app = Flask(__name__)
app.secret_key = "tester"

app.config["MONGO_URI"] = "mongodb://localhost:27017/ProjetFlask221"
mongo = PyMongo(app)
db = mongo.db
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "email" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.context_processor
def inject_mongo():
    return dict(mongo=mongo)
# def inject_object_id():
#     return dict(ObjectId=ObjectId)

@app.route("/", methods=["POST", "GET"])
def login():
    message = 'Please login to your account'
    if "email" in session:
        user_role = db.users.find_one({"email": session["email"]}).get('role')
        if user_role == "admin":
            return redirect(url_for('admin_dashboard'))
        elif user_role == "professeur":
            return redirect(url_for('professeur_dashboard'))
        else:
            return render_template('login.html', message="Entrez le bon utilisateur")

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        email_found = db.users.find_one({"email": email})
        if email_found:
            email_val = email_found['email']
            passwordcheck = email_found['password']
            user_role = email_found.get('role')  
            if bcrypt.checkpw(password.encode('utf-8'), passwordcheck):
                session["email"] = email_val
                if user_role == "admin":
                    return redirect(url_for('admin_dashboard'))
                elif user_role == "professeur":
                    return redirect(url_for('professeur_dashboard'))
            else:
                return render_template('login.html', message=message)
        else:
            message = 'Email not found'
            return render_template('login.html', message=message)
    return render_template('login.html', message=message)

@app.route('/admin_dashboard')
@login_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/professeur_dashboard')
@login_required
def professeur_dashboard():
    return render_template('professeur_dashboard.html')

@app.route("/logout", methods=["POST", "GET"])
def logout():
    if "email" in session:
        session.pop("email", None)
    return redirect(url_for("login"))


            ######################################################
            #                    PARTIE PROFESSEUR               #
            ######################################################
   
@app.route("/listeProfesseur")
def listeProfesseur():
    professeurs = mongo.db.users.find({"role": "professeur"})
    return render_template("listeProfesseur.html", professeurs=professeurs, matieres=matieres, classes=classes)
   

classes = list(mongo.db.classes.find()) 
type_notes = list(mongo.db.typeNote.find()) 
matieres = list(mongo.db.matieres.find()) 
etudiants = list(mongo.db.users.find({"role": "etudiant"}))

@app.route('/insertProfesseur', methods=['POST', 'GET'])
def insertProfesseur():
    if request.method == "POST":
        flash("Data Inserted Successfully")
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        matiere_id = request.form['matiere']
        classe_id = request.form['classe']
        coef = request.form['coef']
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        if password != password_confirm:
            message = 'Passwords do not match'
            return render_template('index.html', matieres=matieres, classes=classes, message=message)

        matiere = mongo.db.matieres.find_one({"_id": ObjectId(matiere_id)})
        classe = mongo.db.classes.find_one({"_id": ObjectId(classe_id)})
        if not matiere or not classe:
            message = 'Invalid matiere or classe selected'
            return render_template('index.html', matieres=matieres, classes=classes, message=message)

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        user_records = mongo.db.users
        user_records.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "password": hashed_password,
            "role": "professeur"
        })

        inserted_user = user_records.find_one({"email": email})

        classe_matiere_records = mongo.db.ClasseMatiere
        classe_matiere_records.insert_one({
            "professeur_id": inserted_user['_id'],
            "matiere": matiere['libelle'],
            "classe": classe['libelle'],
            "coef": coef
        })

        return redirect(url_for('listeProfesseur'))
    else:
        matieres = mongo.db.matieres.find()
        classes = mongo.db.classes.find()
        return render_template('listeProfesseur.html', matieres=matieres, classes=classes)

    
@app.route('/deleteProfesseur/<string:id_data>', methods=['GET'])
def deleteProfesseur(id_data):
    flash("Record Has Been Deleted Successfully")
    
    records = mongo.db.users
    records.delete_one({"_id": ObjectId(id_data)})  

    return redirect(url_for('listeProfesseur'))

@app.route('/updateProfesseur', methods=['POST'])
def updateProfesseur():
    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        classe_id = request.form['classe']  # Champ de sélection de classe
        matiere_id = request.form['matiere']  # Champ de sélection de matière
        coef = request.form['coef']  # Champ de coefficient

        # Mettre à jour les informations du professeur
        records = mongo.db.users
        records.update_one({"_id": ObjectId(id_data)}, {
            "$set": {
                "name": name,
                "email": email,
                "phone": phone
            }
        })

        # Récupérer les informations de classe et de matière
        classe = mongo.db.classes.find_one({"_id": ObjectId(classe_id)})
        matiere = mongo.db.matieres.find_one({"_id": ObjectId(matiere_id)})

        # Mettre à jour les informations de classe et de matière associées dans ClasseMatiere
        classe_matiere_records = mongo.db.ClasseMatiere
        classe_matiere_records.update_one({"professeur_id": ObjectId(id_data)}, {
            "$set": {
                "matiere": matiere['libelle'],
                "classe": classe['libelle'],
                "coef": coef
            }
        })

        flash("Modifier avec Succes")
        return redirect(url_for('listeProfesseur'))


                ######################################################
                #                   PARTIE MATIERES                  #
                ######################################################

@app.route("/listeMatiere")
def listeMatiere():
    matieres = mongo.db.matieres.find()
    return render_template("listeMatiere.html", matieres=matieres) 
    
@app.route('/insertMatiere', methods=['POST'])
def insertMatiere():
    if request.method == "POST":
        flash("Matiere ajoutée avec Succes")
        libelle = request.form['libelle']
        records = mongo.db.matieres 
        records.insert_one({"libelle": libelle})

        return redirect(url_for('listeMatiere'))

@app.route('/deleteMatiere/<string:id_data>', methods=['GET'])
def deleteMatiere(id_data):
    flash("Matiere Supprimée avec Succes")
    records = mongo.db.matieres
    records.delete_one({"_id": ObjectId(id_data)}) 

    return redirect(url_for('listeMatiere'))

@app.route('/updateMatiere', methods=['POST', 'GET'])
def updateMatiere():
    if request.method == 'POST':
        id_data = request.form['id']
        libelle = request.form['libelle']
        records = mongo.db.matieres
        records.update_one({"_id": ObjectId(id_data)}, {"$set": {"libelle": libelle}})
        flash("Matiere modifiée avec Succes")
        return redirect(url_for('listeMatiere'))

                ######################################################
                #                     PARTIE CLASSES                 #
                ######################################################

@app.route("/listeClasse")
def listeClasse():
    classes = mongo.db.classes.find()
    return render_template("listeClasse.html", classes=classes) 
       
@app.route('/insertClasse', methods=['POST'])
def insertClasse():
    if request.method == "POST":
        flash("Classe ajoutée avec Succes")
        libelle = request.form['libelle']
        records = mongo.db.classes 
        records.insert_one({"libelle": libelle})

        return redirect(url_for('listeClasse'))
    
     
@app.route('/deleteClasse/<string:id_data>', methods=['GET'])
def deleteClasse(id_data):
    flash("Matiere Supprimée avec Succes")
    records = mongo.db.classes
    records.delete_one({"_id": ObjectId(id_data)}) 

    return redirect(url_for('listeClasse'))

@app.route('/updateClasse', methods=['POST', 'GET'])
def updateClasse():
    if request.method == 'POST':
        id_data = request.form['id']
        libelle = request.form['libelle']
        records = mongo.db.classes
        records.update_one({"_id": ObjectId(id_data)}, {"$set": {"libelle": libelle}})
        flash("Classe modifiée avec Succes")
        return redirect(url_for('listeClasse'))


                ######################################################
                #                     PARTIE ETUDIANTS               #
                ######################################################

@app.route("/listeEtudiant")
def listeEtudiant():
    classe_filter = request.args.get('classeFilter') 
    query = {"role": "etudiant"}
    if classe_filter:
        query["classe"] = classe_filter

    page = request.args.get('page', 1, type=int)
    per_page = 5
    etudiants = mongo.db.users.find(query).skip((page - 1) * per_page).limit(per_page)
    total_etudiants = mongo.db.users.count_documents(query)
    num_pages = total_etudiants // per_page + (total_etudiants % per_page > 0)
    return render_template("listeEtudiant.html", etudiants=etudiants, classes=classes, num_pages=num_pages, current_page=page)

@app.route('/insertEtudiant', methods=['POST', 'GET'])
def insertEtudiant():
    if request.method == "POST":
        flash("Data Inserted Successfully")
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        classe_id = request.form['classe']  
        password = request.form['password']
        password_confirm = request.form['password_confirm']

        if password != password_confirm:
            message = 'Passwords do not match'
            return render_template('index.html', classes=classes, message=message)

        classe = mongo.db.classes.find_one({"_id": ObjectId(classe_id)})
        if not classe:
            message = 'Invalid classe selected'
            return render_template('index.html', classes=classes, message=message)

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        records = mongo.db.users
        records.insert_one({
            "name": name,
            "email": email,
            "phone": phone,
            "classe": classe['libelle'],  
            "password": hashed_password,  
            "role": "etudiant"
        })

        return redirect(url_for('listeEtudiant'))
    else:
        classes = mongo.db.classes.find()  
        return render_template('listeEtudiant.html', classes=classes)

    
@app.route('/deleteEtudiant/<string:id_data>', methods=['GET'])
def deleteEtudiant(id_data):
    flash("Record Has Been Deleted Successfully")
    
    records = mongo.db.users
    records.delete_one({"_id": ObjectId(id_data)})  

    return redirect(url_for('listeEtudiant'))

@app.route('/updateEtudiant', methods=['POST', 'GET'])
def updateEtudiant():
    if request.method == 'POST':
        id_data = request.form['id']
        name = request.form['name']
        email = request.form['email']
        phone = request.form['phone']
        records = mongo.db.users
        records.update_one({"_id": ObjectId(id_data)}, {"$set": {"name": name, "email": email, "phone": phone}})
        flash("Data Updated Successfully")
        return redirect(url_for('listeEtudiant'))
    
    
                ######################################################
                #                   PARTIE NOTEE                     #
                ######################################################


@app.route("/listeNote", methods=["GET"])
def listeNote():
    classe_filter = request.args.get('classeFilter')
    type_note_filter = request.args.get('typeNoteFilter')

    query = {}
    if classe_filter:
        classe = mongo.db.classes.find_one({'libelle': classe_filter})
        if classe:
            query["classe_id"] = classe['_id']
    if type_note_filter:
        type_note = mongo.db.type_notes.find_one({'libelle': type_note_filter})
        if type_note:
            query["type_note_id"] = type_note['_id']

    notes = mongo.db.notes.find(query)
    return render_template("listeNote.html", notes=notes, matieres=matieres, etudiants=etudiants, classes=classes, type_notes=type_notes, ObjectId=ObjectId)
   
@app.route('/insertNote', methods=['POST'])
def insertNote():
    if request.method == "POST":
        flash("Note ajoutée avec Succes")
        matiere_id = request.form['matiere'] 
        etudiant_id = request.form['etudiant']
        classe_id = request.form['classe'] 
        note = request.form['note'] 
        type_note_id = request.form['type_note'] 
        records = mongo.db.notes 
        records.insert_one({"matiere_id": matiere_id,"etudiant_id": etudiant_id,"classe_id": classe_id,"note": note, "type_note_id": type_note_id})  
        return redirect(url_for('listeNote'))

@app.route('/deleteNote/<string:id_data>', methods=['GET'])
def deleteNote(id_data):
    flash("Note Supprimée avec Succes")
    records = mongo.db.notes
    records.delete_one({"_id": ObjectId(id_data)}) 

    return redirect(url_for('listeNote'))

@app.route('/updateNote', methods=['POST', 'GET'])
def updateNote():
    if request.method == 'POST':
        id_data = request.form['id']
        libelle = request.form['libelle']
        records = mongo.db.notes
        records.update_one({"_id": ObjectId(id_data)}, {"$set": {"libelle": libelle}})
        flash("Note modifiée avec Succes")
        return redirect(url_for('listeNote'))
    
# mongo.db.role.insert_many([
#     {"libelle": "etudiant"},
#     {"libelle": "professeur"},
#     {"libelle": "admin"} 
# ])

#mongo.db.typeNote.insert_many([
#     {"libelle": "noteDevoir"},
#     {"libelle": "noteExamen"}
# ])

if __name__ == "__main__":
    app.run(debug=True)
    