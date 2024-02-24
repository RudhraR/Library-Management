from flask import redirect, render_template, request, flash
from flask import current_app as app
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime, timedelta
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
        return render_template("user/register.html", user=current_user, page="register")
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
        return render_template("user/login.html",user=current_user, page="user_login")
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
                    flash("Wrong Password, Please try login again")
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
        sections= Section.query.all()
        return render_template("home.html", sections=sections, user=current_user)

@app.route("/user_profile", methods= ["GET"])
@login_required
def user_profile():
    if request.method == "GET":
        user_logined_id = current_user.user_id
        user = User.query.filter_by(user_id=user_logined_id).first()
        posts= Posts.query.filter_by(user_id = user_logined_id).all()
        return render_template("other/profile.html", user=current_user,  posts=posts)

@app.route("/edit_profile", methods=["GET", "POST"])
@login_required
def edit_profile():
    if request.method == "GET":
        user_logined_id = current_user.user_id
        user = User.query.filter_by(user_id = user_logined_id).first()
        return render_template("other/edit_profile.html", user=user)
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


@app.route("/book_details/<int:book_id>", methods = ["GET"])
@login_required
def book_details(book_id):
    if request.method == "GET":
        book = Book.query.filter_by(book_id=book_id).first()  
        user_logined_id = current_user.user_id
        # user = User.query.filter_by(user_id=user_logined_id).first()
        if current_user.role!='librarian':
            access_request = Book_access.query.filter_by(user_id=user_logined_id, book_id=book_id).first()
            current_time = datetime.now()
            request_btn, requested_btn, read_return_btns, edit_delete_btn, max_request_reached= True, False, False, False, False
            no_of_requests = Book_access.query.filter_by(user_id=user_logined_id).count()
            if no_of_requests >= 3:
                max_request_reached = True
            if access_request != None:
                access_status = access_request.admin_approval
                if access_status == "Pending":
                    requested_btn = True
                    request_btn = False
                    read_return_btns = False
                elif access_status == "Approved":
                    if current_time > access_request.return_date:
                        db.session.delete(access_request)
                        db.session.commit()
                    else:
                        read_return_btns = True
                        request_btn = False
                        requested_btn = False
                else:
                    read_return_btns = False
                    request_btn = True
                    requested_btn = False
            else:
                if max_request_reached:
                    read_return_btns = False
                    request_btn = False
                    requested_btn = False        
            return render_template("user/book_details.html", book=book, request_btn = request_btn, 
                               requested_btn = requested_btn, read_return_btns = read_return_btns, 
                               edit_delete_btn=edit_delete_btn, max_request_reached=max_request_reached,user=current_user)
        else:
            edit_delete_btn = True
            return render_template("user/book_details.html", book=book, edit_delete_btn=edit_delete_btn,user=current_user)

@app.route("/read_book/<int:book_id>", methods = ["GET", "POST"])
@login_required
def read_book(book_id):
    book = Book.query.filter_by(book_id=book_id).first()
    return render_template("user/read_book.html", book=book,user=current_user)

@app.route("/user_book_return/<int:book_id>")
@login_required
def user_book_return(book_id):
    user_logined_id = current_user.user_id
    access_request = Book_access.query.filter_by(user_id=user_logined_id, book_id=book_id).first()
    db.session.delete(access_request)
    db.session.commit()
    return redirect("/book_details/"+str(book_id))
