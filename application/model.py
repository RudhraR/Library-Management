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
    date_issued = db.Column(db.DateTime())
    return_date = db.Column(db.DateTime())
    # price = db.Column(db.Float(), nullable=False)
    section = db.Column(db.Integer(), db.ForeignKey('section.section_name'), nullable=False)
    feedback = db.Column(db.String())
    rating = db.Column(db.Float())
    book_image = db.Column(db.String())
    # user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'))

    def __init__(self,book_name,book_desc,author,content,book_image,section):
        self.book_name = book_name
        self.book_desc = book_desc
        self.author = author
        self.content=content
        self.book_image=book_image
        self.section = section
        

class Section(db.Model):
    __tablename__ = "section"
    section_id = db.Column(db.Integer(), primary_key=True)
    section_name = db.Column(db.String(40), nullable = False)
    section_desc = db.Column(db.String())
    # books = db.relationship('Book', backref = 'section', lazy = True)

class Cart(db.Model):
    cart_id = db.Column(db.Integer(), primary_key=True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'), nullable = False)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.book_id'), nullable = False)

class Order(db.Model):
    order_id = db.Column(db.Integer(), primary_key = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'), nullable = False)
    book_id = db.Column(db.Integer(), db.ForeignKey('book.book_id'), nullable = False)
    price = db.Column(db.Float(), nullable = False)
    ebook_path = db.Column(db.String())

class Posts(db.Model):
    __tablename__="posts"
    post_id = db.Column(db.Integer(), primary_key=True, autoincrement= True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'))
    post_image_path = db.Column(db.String())
    post_desc = db.Column(db.String())
    like = db.Column(db.Integer())

    def __init__(self, user_id, post_image_path, post_desc):
        self.user_id = user_id
        self.post_desc = post_desc
        self.post_image_path = post_image_path

class PostComments(db.Model):
    __tablename__="comments"
    comment_id = db.Column(db.Integer(), primary_key=True, autoincrement = True)
    user_id = db.Column(db.Integer(), db.ForeignKey('user.user_id'))
    post_id = db.Column(db.Integer(), db.ForeignKey('posts.post_id'))
    comment = db.Column(db.String())
