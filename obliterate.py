from app import app, db, User

def remove_user(username_to_delete):
    with app.app_context():

        user = User.query.filter_by(username=username_to_delete).first()

        if user:

            db.session.delete(user)
            db.session.commit()
            print(f"User {username_to_delete} has been fucking obliterated from existence ^^.")
        else:
            print("User was not found, nothing was deleted")

target = input("Which asshole you wanna delete? Place it here: ")
remove_user(target)
