from flask import render_template

from app.web import web
from helper.auth import check_login
from helper.periods import get_current_period

@web.route('/')
@check_login
def index():
    return render_template('index.html', title = "Home", current_period = get_current_period())