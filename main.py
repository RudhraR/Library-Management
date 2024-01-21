from flask import Flask, request, render_template
from application.database import db
from application.model import *
import os
from application.config import LocalDevelopmentConfig

app = None

def create_app():
    app = Flask(__name__, template_folder="Templates")
    if os.getenv('ENV', "development") == "production":
      raise Exception("Currently no production config is setup.")
    else:
      print("Starting Local Development")
      app.config.from_object(LocalDevelopmentConfig)
    db.init_app(app)
    app.app_context().push()  
    return app 

app = create_app()
app.secret_key="123456789"

from application.controllers import *
from application.librarian_controllers import *

def addlibrarian():
  if User.query.filter_by(role='librarian').first() is None:
    user = User(name = "librarian", email = "librarian@gmail.com", password = "adminpwd", role ="librarian")
    db.session.add(user)
    db.session.commit()

with app.app_context():
    db.create_all()
    addlibrarian()

if __name__ == "__main__":
    app.run(host='0.0.0.0',port=8000, debug=True)