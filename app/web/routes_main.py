from flask import render_template, session, redirect, url_for

from app.web import web
from helper.auth import is_authenticated

@web.route('/')
def index():
    if not is_authenticated(session):
        return redirect(url_for('web.page_login'))
    else:
        return render_template('index.html', title = "Home")