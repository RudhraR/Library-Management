from flask import redirect, render_template, request, flash, session
from flask import current_app as app, url_for
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
# from sqlalchemy import func, DateTime
from datetime import datetime, timedelta
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
            books= Book.query.all()
            return render_template("librarian_home.html", books=books)
        else:
            return ("You are not allowed to access librarian page")
        
@app.route("/add_books", methods=["GET","POST"])
@login_required
def add_books():
    if request.method == "GET":
        return render_template('add_books.html')
    if request.method == "POST":
        book_name = request.form['book_name']
        book_desc = request.form['book_desc']
        author = request.form['author']
        content=request.files['content']
        book_image=request.files['book_image']
        section = request.form['section']
        book_image.save("static/IMG/book_images/" + book_image.filename)
        content.save("static/books/" + content.filename)
        new_book = Book(book_name=book_name, book_desc=book_desc, author=author, 
                        content="../static/books/" + content.filename,
                        book_image="../static/IMG/book_images/" + book_image.filename, section=section)
        db.session.add(new_book)
        db.session.commit()
        # flash ("Book added successfully")
        msg = "Book added successfully"
        return render_template("add_books.html", msg=msg)

@app.route("/read_book/<int:book_id>", methods = ["GET", "POST"])
@login_required
def read_book(book_id):
    book = Book.query.filter_by(book_id=book_id).first()
    return render_template("read_book.html", book=book)


@app.route("/edit_book/<int:book_id>", methods=["GET","POST"])
@login_required
def edit_book(book_id):
    book = Book.query.filter_by(book_id=book_id).first()
    if book == None:
        flash("Book doesn't exist")
        return redirect("/librarian_home")
    if request.method == "GET":
        book = Book.query.filter_by(book_id=book_id).first()
        return render_template("edit_book.html", book=book)
    if request.method == "POST":
        book.book_desc = request.form['book_desc']
        book.author = request.form['author']    
        section = request.form['section']
        if section !="Choose...":
            book.section = section
        content=request.files['content']
        if content:
            content.save("static/books/" + content.filename)
            book.content="../static/books/" + content.filename
        db.session.commit()
        msg = "Book details updated successfully"
        return render_template("edit_book.html", book=book,  msg=msg)
     
@app.route("/delete_book/<int:book_id>")
@login_required
def delete_book(book_id):
    book = Book.query.filter_by(book_id=book_id).first()
    db.session.delete(book)
    db.session.commit()
    return redirect("/librarian_home")

@app.route("/user_book_request/<int:book_id>")
@login_required
def user_book_request(book_id):
    user_logined_id = current_user.user_id
    new_access_request = Book_access(book_id=book_id, user_id=user_logined_id, admin_approval="Pending")
    db.session.add(new_access_request)
    db.session.commit()
    return redirect("/book_details/"+str(book_id))

@app.route("/user_access_revoke/<int:book_id>/<int:user_id>")
@login_required
def user_access_revoke(book_id,user_id):
    access_request = Book_access.query.filter_by(user_id=user_id, book_id=book_id).first()
    db.session.delete(access_request)
    db.session.commit()
    return redirect("/librarian_home")

@app.route("/pending_approvals", methods=["GET","POST"])
@login_required
def pending_approvals():
    pending_requests = Book_access.query.join(
        Book, Book_access.book_id == Book.book_id).join(
        User, Book_access.user_id == User.user_id).filter(
            Book_access.admin_approval == "Pending").add_columns(
                User.user_name, User.user_mail, 
                Book.book_id, Book.book_name, Book_access.access_id).all() 
    return render_template("pending_approvals.html", pending_requests = pending_requests)
    
@app.route("/admin_approval/<int:access_id>", methods=["POST"])
def admin_approval(access_id):    
    if request.method == "POST":
        access_request = Book_access.query.filter_by(access_id=access_id).first()
        approved_status = request.form["approved_status"]
        if(approved_status == "Approve"):
            access_request.admin_approval = "Approved"
            access_request.request_date = datetime.now()
            access_request.return_date = datetime.now() + timedelta(days=1)
        elif(approved_status == "Reject"):
            db.session.delete(access_request)
        db.session.commit()
        return redirect("/pending_approvals")
