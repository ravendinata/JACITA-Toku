from flask import session
from sqlalchemy import desc

from app.models.orders import Orders
from app.models.user import User
from helper.navbar import get_navbar_items

def inject_session_data():
    session_data_keys = [ 'user', 'active_order' ]
    data = {}
    navbar = []

    if 'user' in session:
        active_order = Orders.query.filter(~Orders.status.in_([10, 99]), Orders.created_by == session['user']).order_by(desc(Orders.created_date)).first()
        if active_order:
            session['active_order'] = active_order.id
        else:
            session.pop('active_order', None)

        role = User.query.get(session['user']).role
        navbar = get_navbar_items(role) if 'user' in session else []
    
    for key in session_data_keys:
        data[key] = session.get(key, None)

    return { 'data': data, 'navbar': navbar}