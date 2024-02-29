from flask import redirect, render_template, request, flash, session
from flask import current_app as app, url_for
from flask_login import login_user, LoginManager, login_required, logout_user, current_user
from datetime import datetime, timedelta
from .model import *
from functools import wraps
import os

# Initializing login manager

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(id):
    return User.query.get(id)

def librarian_only(func):
    @wraps(func)
    def inner(*args, **kwargs):
        if current_user.is_authenticated:
            if current_user.role != "librarian":
                flash('You are not allowed to access Librarian related pages')
                return redirect('/')
        return func(*args, **kwargs)
    return inner
            
@app.route("/librarian_login", methods=["GET","POST"])
def librarian_login():
    if request.method == "GET":
        return render_template("librarian/librarian_login.html", user=current_user, page="librarian_login")
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user =  User.query.filter_by(user_mail = email).first()
        if (user.role == "librarian"):
            if password == "adminpwd":
                login_user(user)
                return redirect('/')
            else:
                flash('Wrong password. Try login again!')
                return redirect('/librarian_login')
        else:
            flash('You are not allowed to access librarian page')
            return redirect('/login')
        
@app.route("/add_books", methods=["GET","POST"])
@login_required
@librarian_only
def add_books():
    if request.method == "GET":
        sections = Section.query.all()
        return render_template('librarian/add_books.html', sections=sections, user=current_user)
    if request.method == "POST":
        book_name = request.form['book_name']
        book_desc = request.form['book_desc']
        author = request.form['author']
        content=request.files['content']
        book_image=request.files['book_image']
        section_id = request.form['section_id']
        price = request.form['price']
        no_of_pages = request.form['no_of_pages']
        book_image.save("static/IMG/book_images/" + book_image.filename)
        content.save("static/books/" + content.filename)
        new_book = Book(book_name=book_name, book_desc=book_desc, author=author, 
                        content="../static/books/" + content.filename,
                        book_image="../static/IMG/book_images/" + book_image.filename, section_id=section_id,
                        price=price, no_of_pages=no_of_pages)
        db.session.add(new_book)
        db.session.commit()
        flash ("Book added successfully", 'success')
        
        return redirect("/add_books")

@app.route("/edit_book/<int:book_id>", methods=["GET","POST"])
@login_required
@librarian_only
def edit_book(book_id):
    book = Book.query.filter_by(book_id=book_id).first()
    sections= Section.query.all()
    section = Section.query.filter_by(section_id = book.section_id).first()
    if book == None:
        flash("Book doesn't exist")
        return redirect("/")
    if request.method == "GET":
        return render_template("librarian/edit_book.html", book=book, sections=sections, current_section_name=section.section_name, user=current_user)
    if request.method == "POST":
        book.book_desc = request.form['book_desc']
        book.author = request.form['author']    
        section_id = request.form['section']
        if section_id !="Choose...":
            book.section_id = section_id
        content=request.files['content']
        if content:
            content.save("static/books/" + content.filename)
            book.content="../static/books/" + content.filename
        book.price = request.form['price']
        book.no_of_pages = request.form['no_of_pages']
        db.session.commit()
        msg = "Book details updated successfully"
        section = Section.query.filter_by(section_id = book.section_id).first()
        return render_template("librarian/edit_book.html", book=book,  msg=msg, sections=sections, current_section_name=section.section_name, user=current_user)
     
@app.route("/delete_book/<int:book_id>")
@login_required
@librarian_only
def delete_book(book_id):
    book = Book.query.filter_by(book_id=book_id).first()
    if book:
        if book.content != "../static/books/default_book.pdf":
            os.remove(book.content[3:])
            os.remove(book.book_image[3:])
        db.session.delete(book)
        db.session.commit()
    else:
        flash("Book doesn't exist")
    return redirect("/")

@app.route("/user_book_request/<int:book_id>")
@login_required
def user_book_request(book_id):
    user_logined_id = current_user.user_id
    request_date = datetime.now()
    new_access_request = Book_access(book_id=book_id, user_id=user_logined_id, admin_approval="Pending", request_date=request_date)
    db.session.add(new_access_request)
    db.session.commit()
    return redirect("/book_details/"+str(book_id))

@app.route("/user_access_revoke/<int:book_id>/<int:user_id>")
@login_required
@librarian_only
def user_access_revoke(book_id,user_id):
    access_request = Book_access.query.filter_by(user_id=user_id, book_id=book_id).first()
    db.session.delete(access_request)
    db.session.commit()
    return redirect("/user_management")

@app.route("/user_management", methods=["GET","POST"])
@login_required
@librarian_only
def user_management():
    pending_requests = Book_access.query.join(
        Book, Book_access.book_id == Book.book_id).join(
        User, Book_access.user_id == User.user_id).filter(
            Book_access.admin_approval == "Pending").add_columns(
                User.user_name, User.user_mail, Book.book_name, Book.book_id, Book_access.request_date,
                 Book_access.access_id).all() 

    status = Book_access.query.join(
        Book, Book_access.book_id == Book.book_id).join(
        User, Book_access.user_id == User.user_id).filter(
            Book_access.admin_approval == "Approved").add_columns(
                User.user_name, Book.book_name, Book.book_id,
                Book_access.admin_approved_date, Book_access.return_date, User.user_id).all()
    return render_template("librarian/user_management.html", pending_requests = pending_requests, 
                           status=status, sections=Section.query.all(), user=current_user)
    
@app.route("/admin_approval/<int:access_id>", methods=["POST"])
@login_required
@librarian_only
def admin_approval(access_id):    
    if request.method == "POST":
        access_request = Book_access.query.filter_by(access_id=access_id).first()
        approved_status = request.form["approved_status"]
        if(approved_status == "Approve"):
            access_request.admin_approval = "Approved"
            access_request.admin_approved_date = datetime.now()
            access_request.return_date = datetime.now() + timedelta(days=1)
        elif(approved_status == "Reject"):
            db.session.delete(access_request)
        db.session.commit()
        return redirect("/user_management")
    
@app.route("/section_management")
@login_required
@librarian_only
def section_management():
    sections = Section.query.all()
    return render_template("librarian/section_management.html", sections=sections, user=current_user)

@app.route("/add_section", methods=["POST"])
@librarian_only
def add_section():
        if request.method=="POST":
            section_name = request.form['section_name']
            section_desc = request.form['section_desc']
            date_created = datetime.now()
            
            if section_name!="":
                new_section = Section(section_name=section_name, section_desc=section_desc, date_created=date_created)
                db.session.add(new_section)
                db.session.commit()
                flash('Section added successfully!', 'success')
            return redirect("/section_management")

@app.route("/add_sectionwise_book/<int:section_id>")
@librarian_only
def add_sectionwise_book(section_id):
            sectionwise = Section.query.filter_by(section_id=section_id).first()
            return render_template("librarian/add_books.html", sectionwise=sectionwise, sections=Section.query.all(), user=current_user)
            
@app.route("/section_action/<int:section_id>", methods=["POST"])
@login_required
@librarian_only
def section_action(section_id):
    if request.method=="POST":
        section_action = request.form["section_action"]
        section = Section.query.filter_by(section_id=section_id).first()
        if section_action == "Edit":
            msg="Edit modal"
            return render_template("librarian/section_management.html", msg=msg, sections=Section.query.all(), current_section=section, user=current_user)
        if section_action == "Delete": 
            no_of_books = Book.query.filter_by(section_id = section_id).count()
            if no_of_books == 0:
                db.session.delete(section)
                db.session.commit()
            else:
                msg="Delete modal"
                return render_template("librarian/section_management.html", msg=msg, sections=Section.query.all(), current_section=section, user=current_user)    
            flash('Section deleted successfully!', 'error')
        if section_action == "Show": 
            return redirect(url_for('sectionwise_books',section_id=section_id))
        return redirect("/section_management")
     
@app.route("/edit_section/<int:section_id>", methods=["POST"])
@login_required
@librarian_only
def edit_section(section_id):
    if request.method=="POST":
        new_section_name = request.form["new_section_name"]
        new_section_desc = request.form["new_section_desc"]
        section = Section.query.filter_by(section_id=section_id).first()
        if new_section_name != "":
            section.section_name = new_section_name
            section.section_desc = new_section_desc
            db.session.commit()
            flash('Section name updated successfully!', 'success')
        return redirect("/section_management")

@app.route("/delete_section/<int:section_id>", methods=["GET","POST"])
@login_required
@librarian_only
def delete_section(section_id):
    current_section = Section.query.filter_by(section_id=section_id).first()
    if request.method=="POST":
        new_section = request.form["new_section_name"]       
        reassigned_section = Section.query.filter_by(section_id=new_section).first()
        reassigned_section.books += current_section.books
        db.session.delete(current_section)
        db.session.commit()
        flash('Section deleted successfully and the books are reassigned!', 'error') 
        return redirect("/section_management")
    
    books = Book.query.filter_by(section_id = section_id).all()
    for book in books:
        db.session.delete(book)
    db.session.delete(current_section)
    db.session.commit()
    flash('Section and the books in it are deleted successfully!', 'error') 
    return redirect("/section_management")

       
@app.route("/sectionwise_books/<int:section_id>", methods=["GET","POST"])
@login_required
@librarian_only
def sectionwise_books(section_id):
    section = Section.query.filter_by(section_id=section_id).first()
    section_books = section.books
    if request.method=="GET":
        return render_template("librarian/sectionwise_books.html", section=section, section_books=section_books, sections=Section.query.all(), user=current_user) 
    if request.method=="POST":
        pass
        return redirect("/section_management")
    
@app.route("/dashboard")
@login_required
def dashboard():

#librarian dashboard: issued books
    issued_books = db.session.query(Book.book_id, Book.book_name, 
                                    db.func.count(Book_access.admin_approval).label('book_count')).join(
                                        Book_access, Book.book_id == Book_access.book_id).filter(
                                            Book_access.admin_approval == "Approved").group_by(
                                                Book.book_id, Book.book_name).all()
                                 
    issued_books_list = []
    issued_books_count = []
    for book in issued_books:
        issued_books_list.append(book.book_name)
        issued_books_count.append(book.book_count)

#librarian and user dashboard: Section distribution  
    allsections = Section.query.all()  
    section_names = []
    section_book_count = []
    for section in allsections:
        section_names.append(section.section_name)
        section_book_count.append(len(section.books))

#User Dashboard: Various books status like purchased_books, books_to_read, book_requests
    book_type_names = ["Purchased books", "Books available to read", "Book requests", "Returned/Completed books"]
    purchased_count = Books_purchased.query.filter_by(user_id = current_user.user_id).count()
    books_to_read = Book_access.query.filter_by(user_id = current_user.user_id, 
                                                admin_approval="Approved").count()
    book_requests = Book_access.query.filter_by(user_id = current_user.user_id, 
                                                admin_approval="Pending").count()
    returned_books = Book_access.query.filter_by(user_id = current_user.user_id, 
                                                admin_approval="Returned").count()
    book_type_count = [purchased_count, books_to_read, book_requests, returned_books]
    
    
    return render_template("dashboard.html", user=current_user,
                           issued_books_list=issued_books_list, issued_books_count=issued_books_count,
                           section_names=section_names,section_book_count=section_book_count,
                           book_type_names = book_type_names, book_type_count=book_type_count) 