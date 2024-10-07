from datetime import datetime

from flask import render_template

from app.web import web
from helper.auth import check_login

@web.route('/')
@check_login
def index():
    curr_period_short = datetime.now().strftime('%Y/%m')
    curr_period_long = datetime.now().strftime('%B %Y')
    current_period = { 'short': curr_period_short, 'long': curr_period_long }
    return render_template('index.html', title = "Home", current_period = current_period)