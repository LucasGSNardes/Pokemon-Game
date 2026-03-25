from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import random 


app = Flask(__name__)
app.secret_key = "my_super_not_obvious_key"
#Tells Flask where to save the database file
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
db = SQLAlchemy(app)

#Database structure and columns.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    score = db.Column(db.Integer, default=0)


#Creates the db file automatically... I hope.
with app.app_context():
    db.create_all()

#Register routes (Don't ask me how it works.)

@app.route('/')
def home():
    return '<h1>Welcome!</h1><p>Go to <a href="/register">Register</a> or <a href="/login">Login</a></p> or <a href="/battle">Battle</a>'

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        uname = request.form["username"]
        pword = request.form['password']

        #Hashing time, also saves to db btw.
        hashed_pword = generate_password_hash(pword)
        new_user = User(username=uname, password=hashed_pword)

        try:
            db.session.add(new_user)
            db.session.commit()
            return redirect(url_for("login"))
        except IntegrityError:
            db.session.rollback()
            return "<h3>That username is already taken.</h3><a href='/register'>Try a different name</a>"

    return '''<form method="post">
    Username: <input name= "username"><br>
    Password: <input type="password" name="password"><br>
    <input type ="submit" value="Register">
    </form>'''

#Login route apparently
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == "POST":
        uname = request.form["username"]
        pword = request.form["password"]

        user = User.query.filter_by(username=uname).first()

        if user and check_password_hash(user.password, pword):
            session["user_id"] = user.id #Stores the id ig
            return redirect(url_for('battle'))
        else:
            return "Invalid, get somethin' else. Probs username or password. <a href='/login>Try agai</a>"
        
    return '''<form method="post">
    Username: <input name= "username"><br>
    Password: <input type="password" name="password"><br>
    <input type ="submit" value="Login">
    </form>'''

rules = {"rock": "paper", "paper": "scissors", "scissors": "rock"}

@app.route('/battle')
def battle():
    if "user_id" not in session:
        return "<h3>You must be logged in to fight your pokemon.</h3><a href='/login'>Login here</a>"

    poke_id = random.randint(1,1010)
    api_url = f'https://pokeapi.co/api/v2/pokemon/{poke_id}'

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()

        pokemon_name = data["name"].capitalize()
        pokemon_sprite = data["sprites"]["front_default"]

        return f'''
            <div style="text-align: center; font-family: sans-serif;">
                <h1>You encountered a wild {pokemon_name}!</h1>
                <img src="{pokemon_sprite}" width:"600"; height="400">
                <form action="/resolve-battle" method="POST">
                <input type="hidden" name="pokemon_name" value="{pokemon_name}">
                <button name="user_choice" value="rock">ROCK</button>
                <button name="user_choice" value="paper">PAPER</button>
                <button name="user_choice" value="scissors">SCISSORS</button>
            </form>
            </div>
        '''
    return "The tall grass is empty... (API Error)", 500

@app.route('/resolve-battle', methods=['POST'])
def resolve():
    user_choice = request.form.get("user_choice")
    boss_name = request.form.get("pokemon_name")

    options = ["rock", "paper", "scissors"]
    boss_choice = random.choice(options)
    if user_choice == boss_choice:
        result= "It's a tie, both struggled."
    elif rules[boss_choice] == user_choice:
        result= f"You win! Your {user_choice} defeated {boss_name}'s {boss_choice}."
        if "user_id" in session:
                current_user = User.query.get(session["user_id"])
                current_user.score += 10
                db.session.commit()
    else:
        result = f"You lost! {boss_name} defeated your {user_choice} using their {boss_choice}'s."

    return f'''<div style="text-align: center;">
                <h1>Battle Results</h1>
                <p>You chose: <b>{user_choice.upper()}</b></p>
                <p>{boss_name} chose: <b>{boss_choice.upper()}</b></p>
                <h2>{result}</h2>
                <a href="/battle"><button>Fight Another Boss</button></a>
                </div>
                ''' 
    


if __name__ == '__main__':
    app.run(debug=True)