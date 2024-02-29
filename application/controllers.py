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
            flash("Your email is already registered! Kindly proceed with login.", "error")
            return redirect("/login")
        else:
            password = request.form["password"]
            name = request.form["user_name"]
            hashed_password = bcrypt.generate_password_hash(password)
            new_user = User(name=name, email = email, password= hashed_password, role= "User")
            db.session.add(new_user)
            db.session.commit()
            flash("You are now registered, Please Login", "success")
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
                    flash("Wrong Password! Please try again..", "error")
                    return redirect("/login")
            else:
                flash("You are not authorized to login as librarian.", "error")
                return redirect("/login")
        else:
            flash("You are not registered. Please register.", "error")
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
        purchased = Books_purchased.query.filter_by(user_id = current_user.user_id).all()
        return render_template("home.html", sections=sections, user=current_user, purchased=purchased)

@app.route("/book_details/<int:book_id>", methods = ["GET"])
@login_required
def book_details(book_id):
    if request.method == "GET":
        book = Book.query.filter_by(book_id=book_id).first()  
        user_logined_id = current_user.user_id
        feedback_list = User_Feedback.query.join(
                User, User_Feedback.user_id == User.user_id).filter(
                User_Feedback.book_id == book_id).add_columns(
                User.user_name, User_Feedback.rating, User_Feedback.user_feedback).all() 
        
        if current_user.role!='librarian':
            
            access_request = Book_access.query.filter_by(user_id=user_logined_id, book_id=book_id).first()
            user_feedback = User_Feedback.query.filter_by(user_id=user_logined_id, book_id=book_id).first()
            current_time = datetime.now()
            request_btn, requested_btn, read_return_btns, edit_delete_btn = True, False, False, False
            max_request_reached, feedback_given=False, False
            
            purchased = Books_purchased.query.filter_by(user_id = user_logined_id, book_id=book_id).first()
            
            if user_feedback:
                feedback_given=True
            no_of_requests = Book_access.query.filter_by(user_id=user_logined_id).count()
            if no_of_requests >= 5:
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
            return render_template("user/book_details.html", book=book, request_btn = request_btn, purchased=purchased,
                               requested_btn = requested_btn, read_return_btns = read_return_btns, 
                               edit_delete_btn=edit_delete_btn, max_request_reached=max_request_reached,
                               feedback_given=feedback_given,user=current_user, feedback_list=feedback_list)
        else:
            edit_delete_btn = True
            return render_template("user/book_details.html", book=book, edit_delete_btn=edit_delete_btn,
                                   user=current_user, feedback_list=feedback_list)

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
    access_request.admin_approval = "Returned"
    access_request.return_date = datetime.now()
    flash("This book is returned by you, successfully! ", "success")
    db.session.commit()
    return redirect("/book_details/"+str(book_id))

@app.route("/user_books", methods=["GET"])
@login_required
def user_books():
    pending_requests = Book_access.query.join(
        Book, Book_access.book_id == Book.book_id).filter(
            Book_access.admin_approval == "Pending", Book_access.user_id == current_user.user_id).add_columns(
                Book.book_name, Book.book_id).all() 
    
    books_to_read = Book_access.query.join(
        Book, Book_access.book_id == Book.book_id).filter(
            Book_access.user_id == current_user.user_id, Book_access.admin_approval == "Approved").add_columns(
                Book.book_name, Book.book_id,
                Book_access.admin_approved_date, Book_access.return_date).all()
    
    books_returned = Book_access.query.join(
        Book, Book_access.book_id == Book.book_id).filter(
            Book_access.admin_approval == "Returned", Book_access.user_id == current_user.user_id).add_columns(
                Book.book_name, Book.book_id, Book_access.return_date).all() 
        
    if request.method == "GET":
        return render_template("user/user_books.html", pending_requests=pending_requests, 
                               books_to_read= books_to_read, books_returned=books_returned, user=current_user)
    
@app.route("/user_feedback/<int:book_id>", methods=["POST"])
@login_required
def user_feedback(book_id):
    if request.method == "POST":
        rating=request.form["rating"]
        user_feedback=request.form["user_feedback"]
        new_feedback=User_Feedback(user_id=current_user.user_id, book_id=book_id, rating=rating, user_feedback=user_feedback)
        db.session.add(new_feedback)
        
        book = Book.query.filter_by(book_id=book_id).first()
        current_rating = book.rating
        if current_rating is None:
            book.rating = rating
        else:
            new_rating = (float(current_rating)+float(rating)) / 2
            book.rating = new_rating
        db.session.commit()
        flash("Your feedback is submitted successfully", "success")
    return redirect("/book_details/"+str(book_id))

@app.route("/search", methods=["POST"])
@login_required
def search():
    if request.method == "POST":
        search_by = request.form["search_by"]
        search_input = "%" + request.form["search_input"] + "%"
        search_param = ""
        if request.form["search_input"] == "":
            return redirect("/")
        search_results = None
        # search_by values are: book_name, book_section, author, search_section
        if search_by == "book_section" or search_by == "search_section":
            search_results = Section.query.filter(Section.section_name.like(search_input)).all()
            search_param = "section"
        if search_by == "book_name":
            search_results = Book.query.filter(Book.book_name.like(search_input)).all()
            search_param = "book"
        if search_by == "author":
            search_results = Book.query.filter(Book.author.like(search_input)).all()
            search_param = "book"
        return render_template('search.html', search_results=search_results, 
                               search_param=search_param, user=current_user)

   
@app.route("/add_to_cart/<int:book_id>")
@login_required
def add_to_cart(book_id):
    book = Book.query.filter_by(book_id=book_id).first()
    new_item = Cart(user_id=current_user.user_id, book_id=book_id, price=book.price)
    db.session.add(new_item)
    db.session.commit()
    flash("Book added successfully to the cart.", "success")
    return redirect('/cart')

@app.route("/delete_from_cart/<int:cart_id>")
@login_required
def delete_from_cart(cart_id):
    item = Cart.query.filter_by(cart_id=cart_id).first()
    db.session.delete(item)
    db.session.commit()
    flash("Book deleted from the cart.", "error")
    return redirect('/cart')

@app.route("/cart", methods=["GET","POST"])
@login_required
def cart():
    if request.method=="GET":
        cart_items = Cart.query.join(
                Book, Cart.book_id == Book.book_id).filter(
                Cart.user_id == current_user.user_id).add_columns(
                Book.book_name, Book.author, Book.price, Cart.cart_id).all() 
        if cart_items:
            total_price= sum([item.price for item in cart_items])
            return render_template('user/cart.html',user=current_user, cart_items=cart_items, total_price=total_price)    
    return render_template('user/cart.html',user=current_user)

@app.route("/purchase", methods=["POST"])
@login_required
def purchase():
    if request.method == "POST":
        cvv = request.form["cvv"]
        if cvv == "123":
            purchase = Cart.query.filter_by(user_id = current_user.user_id).all()
            for item in purchase:     
                new_item = Books_purchased(user_id=current_user.user_id, book_id=item.book_id)
                db.session.add(new_item)
                db.session.delete(item)
            db.session.commit()
            flash("Your payment is complete. You can now download your purchased e-books.", "success")
            return redirect('/purchased_books')
        else:
            flash("Your CVV is incorrect. Try your payment again.", "error")
            return redirect('/cart')

@app.route("/purchased_books", methods=["GET"])
@login_required
def purchased_books():
    if request.method == "GET":
        purchased_books = Books_purchased.query.join(
        Book, Books_purchased.book_id == Book.book_id).filter(
            Books_purchased.user_id == current_user.user_id).add_columns(
                Book.book_name, Book.author, Book.content, Book.book_id).all()
        return render_template("user/purchased_books.html", purchased_books=purchased_books, user=current_user)