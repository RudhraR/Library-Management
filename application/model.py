from .database import db
from flask_login import UserMixin

class User(db.Model,UserMixin):
    __tablename__=  "user"
    user_id = db.Column(db.Integer(), primary_key = True, autoincrement = True)
    user_mail =  db.Column(db.String(30), nullable = False, unique = True)
    user_name = db.Column(db.String())
    password = db.Column(db.String(80), nullable = False)
    role = db.Column(db.String(20), nullable = False)

    def __init__(self,name,email,password,role):
        self.user_name = name
        self.user_mail = email
        self.password = password
        self.role = role
        
    def get_id(self):
        return self.user_id

class Book(db.Model):
    __tablename__="book"
    book_id = db.Column(db.Integer(), primary_key=True, autoincrement= True)   
    book_name =  db.Column(db.String(80), nullable = False)
    book_desc = db.Column(db.String())
    author = db.Column(db.String(80), nullable = False)
    content = db.Column(db.String())
    price = db.Column(db.Float(), nullable=False)
    section_id = db.Column(db.Integer(), db.ForeignKey('section.section_id'), nullable=False)
    rating = db.Column(db.String())
    book_image = db.Column(db.String())
    no_of_pages = db.Column(db.Integer())  
    
    book_access = db.relationship("Book_access", cascade="all, delete")
    feedback = db.relationship("User_Feedback", cascade="all, delete")
    cart = db.relationship("Cart", cascade="all, delete")
    books_purchased = db.relationship("Books_purchased", cascade="all, delete")
    
        
class Section(db.Model):
    __tablename__ = "section"
    section_id = db.Column(db.Integer(), primary_key=True)
    section_name = db.Column(db.String(40), nullable = False)
    section_desc = db.Column(db.String())
    date_created = db.Column(db.Date())
    books = db.relationship('Book', backref = 'section', lazy = True)

class Book_access(db.Model):
    __tablename__ = "book_access"
    access_id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'), nullable = False)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.book_id'), nullable = False)
    admin_approval = db.Column(db.String(), nullable=False)
    request_date = db.Column(db.DateTime())
    admin_approved_date = db.Column(db.DateTime())
    return_date = db.Column(db.DateTime())

class User_Feedback(db.Model):
    __tablename__="user_feedback"
    feedback_id = db.Column(db.Integer(), primary_key=True, autoincrement = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'))
    book_id = db.Column(db.Integer(), db.ForeignKey('book.book_id'))
    rating = db.Column(db.Integer())
    user_feedback = db.Column(db.String())

class Cart(db.Model):
    __tablename__="cart"
    cart_id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'), nullable = False)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.book_id'), nullable = False)
    price = db.Column(db.Float(), nullable = False)

class Books_purchased(db.Model):
    __tablename__="books_purchased"
    order_id = db.Column(db.Integer(), primary_key = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'), nullable = False)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.book_id'), nullable = False)