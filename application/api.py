from flask import request, jsonify
from flask_restful import Resource, reqparse, abort, fields, marshal_with
from datetime import datetime
from application.model import *
import werkzeug
import json
from flask import current_app as api


#UserAPI
user_parser = reqparse.RequestParser()
user_parser.add_argument('user_mail', type=str)
user_parser.add_argument('user_name', type=str)
user_parser.add_argument('password', type=str)

user_fields = {
    'user_id': fields.Integer,
    'user_mail': fields.String,
    'password': fields.String,
    'user_name':fields.String
}


# (AllUserAPI endpoint: '/api/user')
class AllUserAPI(Resource):
    def get(resource):
        users = User.query.all()
        user_list = []
        for user in users:
            user_list.append({'user_id': user.user_id,'user_mail': user.user_mail,'user_name':user.user_name})
        return user_list

    def post(resource):
        args = user_parser.parse_args()
        user = User.query.filter_by(user_mail = args["user_mail"]).first()
        if user:
            abort(409,message="user mail already registered")
        new_user = User(email= args["user_mail"], password=args["password"], name=args["user_name"], role="User")
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'status':'success', 'message':'user added'})
    
# (UserAPI Endpoint: '/api/user/<int:user_id>')
class UserAPI(Resource):
    @marshal_with(user_fields)
    def get(self, user_id):
        user = User.query.filter_by(user_id=user_id).first()
        return user, 200

    @marshal_with(user_fields)
    def put(self, user_id):
        args = user_parser.parse_args()
        user = User.query.filter_by(user_id = user_id).first()
        if not user:
            abort(404, message="this user is not in database")
        if args["user_mail"]:
            user.user_mail = args["user_mail"]
        if args["user_name"]:
            user.user_name = args["user_name"]
        if args["password"]:
            user.password = args["password"]
        db.session.commit()
        return user

    def delete(self, user_id):
        user = User.query.filter_by(user_id=user_id).first()
        db.session.delete(user)
        db.session.commit()
        return jsonify({'status': 'Deleted', 'message':"User is deleted"})
    
    
#BookAPI

book_parser = reqparse.RequestParser()
book_parser.add_argument('book_name', type=str)
book_parser.add_argument('book_desc', type=str)
book_parser.add_argument('author', type=str)
# book_parser.add_argument ('content', type=werkzeug.datastructures.FileStorage, location='files')
book_parser.add_argument('price', type=float)
book_parser.add_argument('section_id', type=int, required=True, help="Section_id cannot be blank!")
book_parser.add_argument('rating', type=str)
# book_parser.add_argument('book_image', type=werkzeug.datastructures.FileStorage, location='files')
book_parser.add_argument('no_of_pages', type=int)

book_fields = {
    'book_id': fields.Integer,
    'book_name': fields.String,
    'book_desc': fields.String,
    'author': fields.String,
    'price':fields.Float,
    'section_id':fields.Integer,
    'rating':fields.String,
    'no_of_pages':fields.Integer
}

# (AllBookAPI endpoint: '/api/book')
class AllBookAPI(Resource):
    def get(resource):
        books = Book.query.all()
        book_list = []
        for book in books:
            section=Section.query.filter_by(section_id=book.section_id).first()
            book_list.append({'book_id': book.book_id,'book_name': book.book_name,'description':book.book_desc,
                              'author':book.author, 'no_of_pages':book.no_of_pages, 'price':book.price,
                              'rating':book.rating,'section_name':section.section_name})
        return book_list

    def post(resource): 
        args = book_parser.parse_args()
        new_book = Book(book_name= args["book_name"], book_desc=args["book_desc"], author=args["author"], 
                        section_id= args["section_id"], price= args["price"],
                        no_of_pages= args["no_of_pages"], content="../static/books/default_book.pdf", 
                        book_image="../static/IMG/default_book_image.jpg"
                        )
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'status':'success', 'message':'Book added successfully'})
        
#(BookAPI endpoint: '/api/book/<int:book_id>')
class BookAPI(Resource):
    @marshal_with(book_fields)
    def get(self, book_id):   
        book = Book.query.filter_by(book_id=book_id).first()
        if not book:
            abort(404, message="This book is not in the database")
        return book, 200
 
    @marshal_with(book_fields)
    def put(self, book_id):
        args = book_parser.parse_args()
        book = Book.query.filter_by(book_id = book_id).first()
        if not book:
            abort(404, message="This book is not in the database")
        if args["author"]:
            book.author = args["author"]
        if args["price"]:
            book.price = args["price"]
        if args["no_of_pages"]:
            book.no_of_pages = args["no_of_pages"]
        if args["section_id"]:
            book.section_id = args["section_id"]
        db.session.commit()
        return book
    
    def delete(self, book_id):
        book = Book.query.filter_by(book_id=book_id).first()
        if not book:
            abort(404, message="This book is not in the database")
        db.session.delete(book)
        db.session.commit()
        return jsonify({'status': 'Deleted', 'message':"Book is deleted"})

#SectionAPI
section_parser = reqparse.RequestParser()
section_parser.add_argument('section_name', type=str)
section_parser.add_argument('section_desc', type=str)

section_fields = {
    'section_id': fields.Integer,
    'section_name': fields.String,
    'section_desc': fields.String,
    'date_created': fields.DateTime(dt_format='iso8601')
}
   
# (AllSectionAPI endpoint: '/api/section')
class AllSectionAPI(Resource):
    def get(resource):
        sections = Section.query.all()
        section_list = []
        for section in sections:
            section_list.append({'section_id': section.section_id,'section_name': section.section_name,
                                 'description':section.section_desc,
                                 'books': [book.book_name for book in section.books]
                              })
        return section_list
    
    def post(resource):
        args = section_parser.parse_args()
        section = Section.query.filter_by(section_name = args["section_name"]).first()
        if section:
            abort(409,message="Section already exists.")
        new_section = Section(section_name= args["section_name"], 
                              section_desc=args["section_desc"], 
                              date_created=datetime.now())
        db.session.add(new_section)
        db.session.commit()
        return jsonify({'status':'success', 'message':'Section created'})

# (SectionAPI endpoint: '/api/section/<int:section_id>')    
class SectionAPI(Resource):
    @marshal_with(section_fields)
    def get(self, section_id):
        section = Section.query.filter_by(section_id=section_id).first()
        return section, 200

    @marshal_with(section_fields)
    def put(self, section_id):
        args = section_parser.parse_args()
        section = Section.query.filter_by(section_id = section_id).first()
        if not section:
            abort(404, message="This section is not in database")
        if args["section_name"]:
            section.section_name = args["section_name"]
        if args["section_desc"]:
            section.section_desc = args["section_desc"]
        db.session.commit()
        return section

    def delete(self, section_id):
        section = Section.query.filter_by(section_id=section_id).first()
        if section.books:
            for book in section.books:
                db.session.delete(book)
        db.session.delete(section)
        db.session.commit()
        return jsonify({'status': 'Deleted', 'message':"Section is deleted"})


section_book_parser = reqparse.RequestParser()
section_book_parser.add_argument('book_id', type=int)

section_book_fields = {
    'section_id': fields.Integer,
    'section_name': fields.String,
    'section_desc': fields.String,
    'date_created': fields.DateTime(dt_format='iso8601'),
    'books': fields.List(fields.Nested(book_fields))
}

# (Section_BooksAPI endpoint: '/api/section_books/<int:section_id>')
class Section_BooksAPI(Resource):
    @marshal_with(section_book_fields)
    def get(self, section_id):
        section = Section.query.filter_by(section_id=section_id).first() 
        if not section:
            abort(404, message="This section doesn't exist.")       
        return section, 200

    @marshal_with(section_book_fields)
    def put(self, section_id):
        args = section_book_parser.parse_args()
        section = Section.query.filter_by(section_id = section_id).first()
        book = Book.query.filter_by(book_id=args["book_id"]).first()
        if not section:
            abort(404, message="This section doesn't exist.")  
        if not book:
            abort(404, message="This book is not in database")
        book.section_id=section_id
        db.session.commit()
        return section
    
    def post(self, section_id):
        section = Section.query.filter_by(section_id = section_id).first()
        if not section:
            abort(404, message="This section doesn't exist.")  
        args = book_parser.parse_args()
        new_book = Book(book_name= args["book_name"], book_desc=args["book_desc"], author=args["author"], 
                        section_id= section_id, price= args["price"],
                        no_of_pages= args["no_of_pages"], content="../static/books/default_book.pdf", 
                        book_image="../static/IMG/default_book_image.jpg"
                        )
        db.session.add(new_book)
        db.session.commit()
        return jsonify({'status':'success', 'message':'Book added successfully to the section'})
    
    def delete(self, section_id):
        args = section_book_parser.parse_args()
        section = Section.query.filter_by(section_id=section_id).first()
        if not section:
            abort(404, message="This section doesn't exist.")  
        book = Book.query.filter_by(book_id=args["book_id"]).first()
        if book in section.books:
            db.session.delete(book)
        else:
            abort(404, message="This book doesn't exist in this section.")  
        db.session.commit()
        return jsonify({'status': 'Deleted', 'message':"Book is deleted from the section"})