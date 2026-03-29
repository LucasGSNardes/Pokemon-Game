from flask import Flask, render_template, request, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import requests
import random 
import jwt
import datetime

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
    return '<h1>Welcome!</h1><p>Go to <a href="/register">Register</a> or <a href="/login">Login</a></p>'

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
            payload = {
                'user_id': user.id, 'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24) #valid for one day, or 24 hours if you're annoying
            }
            #Sign in with the secret key
            token = jwt.encode(payload, app.config["SECRET_KEY"], algorithm="HS256")
            return f'''
                        <h1>Login Success!</h1>
                        <p>Your token is: <code>{token}</code></p>
                        <script>
                            // This saves the token in the browser's "Pocket"
                            localStorage.setItem("token", "{token}");
                            // Then moves to the battle page after 2 seconds
                            setTimeout(() => {{ 
                                window.location.href = "/battle?token={token}"; 
                            }}, 2000);
                        </script>
                    '''
        else:
            return "Invalid, get somethin' else. Probs username or password. <a href='/login>Try again</a>"
        
    return '''<form method="post">
    Username: <input name= "username"><br>
    Password: <input type="password" name="password"><br>
    <input type ="submit" value="Login">
    </form>'''

rules = {"paper": "rock", "scissors": "paper", "rock": "scissors"}

@app.route('/battle')
def battle():
    token = request.args.get('token') #Pass it in the url for now
    
    if not token:
        return "Missing Token dumbass!", 401
    try:
        #unseal the token
        data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        current_user_id = data["user_id"]
        user = db.session.get(User, current_user_id)
        trainer_name = user.username
        #if working, continue the battle logic
    except jwt.ExpiredSignatureError:
        return "Token expired. Login again", 401
    except jwt.InvalidTokenError:
        return "Fake Token! Nice try team rocket... gosh that's so corny.", 401
    

    poke_id = random.randint(1,1010)
    api_url = f'https://pokeapi.co/api/v2/pokemon/{poke_id}'

    response = requests.get(api_url)

    if response.status_code == 200:
        data = response.json()

        pokemon_name = data["name"].capitalize()
        pokemon_sprite = data["sprites"]["front_default"]

        return render_template('battle.html', 
                       trainer_name=trainer_name, 
                       pokemon_name=pokemon_name, 
                       pokemon_sprite=pokemon_sprite, 
                       token=token)
    
    return "The tall grass is empty... (API Error)", 500

@app.route('/resolve-battle', methods=['POST'])
def resolve():
    user_choice = request.form.get("user_choice")
    boss_name = request.form.get("pokemon_name")
    token_from_form = request.form.get('token')

    if not token_from_form:
        return "Missing token! Your victory doesn't count.", 401
    
    try:
        data = jwt.decode(token_from_form, app.config["SECRET_KEY"], algorithms=["HS256"])
        current_user_id = data["user_id"]
        user = db.session.get(User, current_user_id)
        

    except Exception:
        return "Invalid Token, prob", 401
    
    #Fight logic finally

    options = ["rock", "paper", "scissors"]
    boss_choice = random.choice(options)
    if user_choice == boss_choice:
        status = "Tie"
        result= "It's a tie, both struggled."

    elif rules[user_choice] == boss_choice:
        status = "Win"
        result= f"You win! Your {user_choice} defeated {boss_name}'s {boss_choice}."
        user.score += 1
        db.session.commit()

    else:
        status = "Loss"
        result = f"You lost! {boss_name} defeated your {user_choice} using their {boss_choice}'s."

    #Store result data in the session 'notebook'
    session['last_battle'] = {
        'status': status,
        'result': result,
        'boss_choice': boss_choice,
        'user_choice': user_choice,
        'score': user.score,
        'pokemon_name': boss_name
    }

    #Redirect to a dedicated result page
    #Pass the token in the url so the play again button works
    return redirect(url_for('battle_result', token=token_from_form))
    
@app.route('/battle_result')
def battle_result():
    token = request.args.get('token')

    #pull the data from the 'notebook'
    battle_data = session.get('last_battle')

    if not battle_data:
        return redirect(url_for('battle', token=token))
    
    return render_template("result.html",
                           status=battle_data['status'],
                           result=battle_data['result'],
                           pokemon_name=battle_data['pokemon_name'],
                           user_choice=battle_data['user_choice'],
                           boss_choice=battle_data['boss_choice'],
                           score=battle_data['score'],
                           token=token
                           )

if __name__ == '__main__':
    app.run(debug=True)

