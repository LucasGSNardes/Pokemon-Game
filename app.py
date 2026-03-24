from flask import Flask, render_template, request, redirect
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
#Tells Flask where to save the database file
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///users.db"
db = SQLAlchemy(app)

#Database structure and columns.
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

#Creates the db file automatically... I hope.
with app.app_context():
    db.create_all()

#Register routes (Don't ask me how it works.)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == "POST":
        uname = request.form["username"]
        pword = request.form['password']

        #Hashing time, also saves to db btw.
        hashed_pword = generate_password_hash(pword)
        new_user = User(username=uname, password=hashed_pword)

        db.session.add(new_user)
        db.session.commit()
        return "Registration Successful! Go to /login"
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
            return f"Hello {uname}, you are officially logged in, don't let it go to your head though."
        else:
            return "Invalid, get somethin' else. Probs username or password"
        
    return '''<form method="post">
    Username: <input name= "username"><br>
    Password: <input type="password" name="password"><br>
    <input type ="submit" value="Login">
    </form>'''

if __name__ == '__main__':
    app.run(debug=True)






































def rockpaperscizzorsfancy():
    user = input("Write an option (rock, paper, scizzors): ").lower()
    computer = random.choice(["rock", "paper", "scizzors"])
    print(f"\nComputer chose {computer}.")

    if user == computer:
        print("A tie losers.")
    elif rules[user] == computer:
        print(f"{user.title()} fuckin' smashed the computer bro.")
    else:
        print(f"{computer.title()} fuckin' covered your shit bro.") 

