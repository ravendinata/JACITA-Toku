from flask import render_template, session, redirect, url_for

from app.web import web
from app.models.user import User, Division
from helper.auth import is_authenticated, check_login
from helper.endpoint import check_page_permission
from helper.role import Role

@web.route('/login')
def page_login():
    if is_authenticated(session):
        return redirect(url_for('web.index'))
    else:
        return render_template('user/login.html', title = "Login", next_url = session.get('next'))
    
@web.route('/user/profile')
@check_login
def page_profile():
    username = session.get('user')
    user = User.query.get(username)
    return render_template('user/profile.html', title = "Profile", user = user.to_dict())

@web.route('/user/<string:username>')
@check_login
@check_page_permission('user/administer')
def page_user(username):
    user = User.query.get(username)
    return render_template('user/profile.html', title = "User", user = user.to_dict(), admin = True)

@web.route('/users')
@check_login
@check_page_permission('user/administer')
def page_users():
    division = Division.query.all()
    roles = Role.get_roles()
    return render_template('user/view_all.html', use_datatables = True, title = "Users", roles = roles, divisions = division)