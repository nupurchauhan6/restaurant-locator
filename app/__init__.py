from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

db = SQLAlchemy()
DB_NAME = "restaurant_database.db"

def create_app():

    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'ds@123'
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_NAME}'

    db.init_app(app)

    from .models import Restaurant
    create_database(app)
    return app


def create_database(app):
    if not path.exists('app/' + DB_NAME):
        with app.app_context():
            # create database and tables
            db.create_all()

            # insert data
            from .data import insert
            db.session.add_all(insert)
            db.session.commit()