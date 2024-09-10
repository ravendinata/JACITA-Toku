import json

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func

from app.extensions import db

def create_app():
    with open('config.json') as config_file:
        config = json.load(config_file)

    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{config["db_user"]}:{config["db_pass"]}@{config["db_host"]}:{config["db_port"]}/{config["db_name"]}?sslmode=require'

    # ==========
    # Extensions
    # ==========
    db.init_app(app)

    # ==========
    # Blueprints
    # ==========
    from app.api import api
    app.register_blueprint(api, url_prefix = '/api')

    return app