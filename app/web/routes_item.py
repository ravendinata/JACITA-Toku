from flask import render_template, session, redirect, url_for

from app.web import web
from helper.auth import is_authenticated

@web.route('/items')
def page_items_view_all():
    if not is_authenticated(session):
        return redirect(url_for('web.page_login'))
    else:
        data = { 'username': session['user'] }
        return render_template('items/view_all.html', title = "Items", data = data, use_datatables = True)
    
@web.route('/items/add')
def page_items_add():
    if not is_authenticated(session):
        return redirect(url_for('web.page_login'))
    else:
        data = { 'username': session['user'] }
        return render_template('items/add.html', title = "Add Item", data = data)