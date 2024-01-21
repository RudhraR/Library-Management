from flask import redirect, render_template, request, flash, session
from flask import current_app as app
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from .model import *

# Initializing login manager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

@app.route("/librarian_login", methods=["GET","POST"])
def librarian_login():
    if request.method == "GET":
        return render_template("librarian_login.html")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user =  User.query.filter_by(user_mail = email).first()
        if (email == "librarian@gmail.com" and password=="adminpwd" and user.role=="librarian"):
            # session['email'] = email
            login_user(user)
            return redirect('/librarian_home')
        else:
            flash('You are not allowed to access librarian page')
            return redirect('/login')


# for logout user
@app.route("/librarian_logout")
@login_required
def librarian_logout():
    # session.pop('email',None)
    logout_user()
    return redirect('/login')

@app.route("/librarian_home", methods= ["GET"])
@login_required
def librarian_home():
    if request.method == "GET":
        if current_user.role == "librarian":
             return render_template('librarian_home.html')
        else:
            return ("You are not allowed to access librarian page")