from flask import render_template, session, redirect, url_for

from app.web import web
from app.models.user import User
from helper.auth import is_authenticated

@web.route('/login')
def page_login():
    if is_authenticated(session):
        return redirect(url_for('web.index'))
    else:
        return render_template('user/login.html', title = "Login")
    
@web.route('/user/profile')
def page_profile():
    if is_authenticated(session):
        username = session.get('user')
        user = User.query.get(username)
        data = { 'username': username }

        return render_template('user/profile.html', title = "Profile", user = user.to_dict(), data = data)
    else:
        return redirect(url_for('web.login'))