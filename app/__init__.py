import json
from datetime import timedelta

from flask import Flask

from app.extensions import db

def create_app():
    with open('config.json') as config_file:
        config = json.load(config_file)

    app = Flask(__name__)
    app.secret_key = config['app_secret_key']
    app.config['SQLALCHEMY_DATABASE_URI'] = f'postgresql://{config["db_user"]}:{config["db_pass"]}@{config["db_host"]}:{config["db_port"]}/{config["db_name"]}?sslmode=require'
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours = 8)

    # ==========
    # Extensions
    # ==========
    db.init_app(app)

    # ==========
    # Blueprints
    # ==========
    from app.web import web
    app.register_blueprint(web)

    from app.api import api
    app.register_blueprint(api, url_prefix = '/api')

    return app