from flask import render_template, session, redirect, url_for

from app.web import web
from helper.auth import check_login

@web.route('/')
@check_login
def index():
    return render_template('index.html', title = "Home")