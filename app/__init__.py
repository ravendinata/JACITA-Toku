import json
from datetime import timedelta

from flask import Flask, render_template

from app.extensions import csrf, db
from app.context_processor import inject_session_data

from helper.endpoint import HTTPStatus

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
    db.init_app(app)    # SQLAlchemy Database Connection Object (app.extensions.db)
    csrf.init_app(app)  # CSRF Protection Object (app.extensions.csrf

    # =================
    # Context Processor
    # =================
    app.context_processor(inject_session_data)  # Inject session data to all templates (app.context_processor.inject_session_data)

    # ==============
    # Error Handlers
    # ==============
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('error/standard.html', 
                               title = "Page Not Found", 
                               message = "The page you are looking for does not exist."), HTTPStatus.NOT_FOUND
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('error/standard.html', 
                               title = "Internal Server Error", 
                               message = "An internal server error occurred. Please try again later."), HTTPStatus.INTERNAL_SERVER_ERROR

    # ==========
    # Blueprints
    # ==========
    # Web Blueprint: Contains all web page routes (app.web)
    from app.web import web
    app.register_blueprint(web)

    # API Blueprint: Contains all API routes (app.api)
    from app.api import api
    app.register_blueprint(api, url_prefix = '/api')

    return app