from models import *
import uuid 
from flask import render_template, request, redirect, url_for, session
import plotly
import plotly.graph_objs as go
import json

def open_file_json(name_json):
    with open(f'questions/{name_json}.json', 'r',encoding='utf-8') as file:
        data_json = json.load(file)
        return data_json

@app.route('/', methods=['GET', 'POST'])
def formulaire():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        niveau_etude = request.form['niveau_etude']
        centre_interet = request.form['centre_interet']
        choix_categorie = request.form['choix_categorie']

        if not (nom and prenom and email and niveau_etude and centre_interet and choix_categorie):
            return render_template('formulaire.html', message="Veuillez remplir tous les champs.")
        
        # Générer un ID utilisateur unique
        user_id = str(uuid.uuid4())

        #Stockage dans une variable temporaire
        session['user_id'] = user_id

        participant = Participant(id=user_id,
                                  nom=nom, 
                                  prenom=prenom, 
                                  email=email, 
                                  niveau_etude=niveau_etude,
                                  centre_interet=centre_interet, 
                                  choix_categorie=choix_categorie)
        
        db.session.add(participant)
        db.session.commit()

        return redirect(url_for('accueil'))

    return render_template('formulaire.html', message=None)

@app.route('/accueil')
def accueil():
    return render_template('home.html')


@app.route('/categorie/<categorie>', methods=['GET', 'POST'])
def categorie_questions(categorie):
    if categorie == 'droit':
        message = "droit"
        data_json = open_file_json(categorie)

    elif categorie == 'humanitaire':
        message = "humanitaire"
        data_json = open_file_json(categorie)

    elif categorie == 'culturel':
        message = "culturel"
        data_json = open_file_json(categorie)
    
    elif categorie == 'resultats':
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        traitement_reponses(data_json, categorie)
        return redirect(url_for('accueil'))
    
    return render_template('categorie.html', questions=data_json['questions'],message=message)


def traitement_reponses(data_json, categorie):
    participant_id = session.get('user_id')
    answers = request.form
    correct_answers = 0

    # Vérifiez les réponses
    for question in data_json['questions']:
        question_id = question['question']
        if answers.get(question_id) == question['reponse_correcte']:
            correct_answers += 1  # 1 point par bonne réponse

    # Calculez les statistiques
    total_questions = len(data_json['questions'])
    incorrect_answers = total_questions - correct_answers
    success_percentage = round((correct_answers / total_questions) * 100,2)

    # Créez une instance de ReponseParticipant et ajoutez-la à la base de données 
    reponse_participant = ReponseParticipant(participant_id=participant_id,
                                             correct_answers=correct_answers,
                                             incorrect_answers=incorrect_answers,
                                             success_percentage=success_percentage,
                                             categorie=categorie)
    db.session.add(reponse_participant)
    db.session.commit()

@app.route('/dashboard')
def dashboard():
    categories = []
    success_percentages = []

    # Récupérer les données de succès pour chaque catégorie
    categories_data = db.session.query(ReponseParticipant.categorie, db.func.avg(ReponseParticipant.success_percentage))\
                                 .group_by(ReponseParticipant.categorie).all()

    # Palette de couleurs pour les catégories
    colors = ['rgb(31, 119, 180)', 'rgb(255, 127, 14)', 'rgb(44, 160, 44)', 'rgb(214, 39, 40)', 
              'rgb(148, 103, 189)', 'rgb(140, 86, 75)', 'rgb(227, 119, 194)', 'rgb(127, 127, 127)', 
              'rgb(188, 189, 34)', 'rgb(23, 190, 207)']
    
    for _, (category, success_percentage) in enumerate(categories_data):
        categories.append(category)
        success_percentages.append(success_percentage)

    # Créer le graphique à barres avec des couleurs différentes pour chaque catégorie
    bar_chart = go.Bar(
        x=categories,
        y=success_percentages,
        text=success_percentages,
        textposition='auto',
        marker=dict(color=colors[:len(categories)]),
        opacity=0.6
    )

    layout = go.Layout(
        title='Pourcentage de succès par catégorie',
        xaxis=dict(title='Catégorie'),
        yaxis=dict(title='Pourcentage de succès'),
    )

    fig = go.Figure(data=[bar_chart], layout=layout)

    graph_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template('dashboard.html', graph_json=graph_json)



if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
