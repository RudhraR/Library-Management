from flask import redirect, render_template, request, flash
from flask import current_app as app
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt

from .model import *

#-------initialize login manager--------------
bcrypt = Bcrypt(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)


@app.route("/register", methods = ["GET","POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    if request.method == "POST":
        email = request.form["email"]
        existing_email =  User.query.filter_by(user_mail = email).first()
        if existing_email:
            flash("email already registered")
            return redirect("/login")
        else:
            password = request.form["password"]
            name = request.form["user_name"]
            hashed_password = bcrypt.generate_password_hash(password)
            new_user = User(name=name, email = email, password= hashed_password, role= "User")
            db.session.add(new_user)
            db.session.commit()
            flash("You are now registered, Please Login")
            return redirect('/login')

@app.route("/login", methods =["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        email = request.form["email"]
        password =  request.form["password"]
        user =  User.query.filter_by(user_mail = email).first()
        if user:
            if user.role != "librarian":
                if bcrypt.check_password_hash(user.password, password):
                    login_user(user)
                    return redirect('/')
                else:
                    flash("Wrong Password, Please Login")
                    return redirect("/login")
            else:
                flash("You are not authorized to login as librarian.")
                return redirect("/login")
        else:
            flash("You are not registered, Please register")
            return redirect("/register")


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route('/',methods = ["GET"])
@login_required
def home():
    if request.method == "GET":
        books= Book.query.all()
        return render_template("home.html", books=books)

@app.route("/user_profile", methods= ["GET"])
@login_required
def user_profile():
    if request.method == "GET":
        user_logined_id = current_user.user_id
        user = User.query.filter_by(user_id=user_logined_id).first()
        posts= Posts.query.filter_by(user_id = user_logined_id).all()
        return render_template("profile.html", user = user, posts=posts)

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "GET":
        user_logined_id = current_user.user_id
        user = User.query.filter_by(user_id = user_logined_id).first()
        return render_template("edit_profile.html", user=user)
    if request.method == "POST":
        user_name = request.form["user_name"]
        user_bio = request.form["user_bio"]
        profile_pic = request.files["profile_pic"]
        profile_pic.save("static/images/" + profile_pic.filename)

        user_logined_id = current_user.user_id
        user = User.query.filter_by(user_id = user_logined_id).first()
        user.user_name = user_name
        user.user_bio = user_bio
        user.profile_img_path = "../static/images/" + profile_pic.filename
        db.session.commit()
        return redirect('/user_profile')


@app.route("/add_post", methods=["GET","POST"])
@login_required
def add_post():
    if request.method == "GET":
        return render_template('add_post.html')
    if request.method == "POST":
        post_img = request.files['post_img']
        post_desc = request.form['post_desc']
        user_logined_id = current_user.user_id
        post_img.save("static/images/post_images/" + post_img.filename)
        new_post = Posts(user_id=user_logined_id, post_image_path="../static/images/post_images/" + post_img.filename, post_desc=post_desc)
        db.session.add(new_post)
        db.session.commit()
        return redirect('/user_profile')

@app.route("/user_post/<int:post_id>", methods = ["GET", "POST"])
@login_required
def user_post(post_id):
    post = Posts.query.filter_by(post_id=post_id).first()
    return render_template("user_post.html", post=post)










