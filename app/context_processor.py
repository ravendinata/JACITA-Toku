from flask import session
from sqlalchemy import desc

from app.models.orders import Orders

def inject_session_data():
    session_data_keys = [ 'user', 'active_order' ]
    data = {}

    if 'user' in session:
        active_order = Orders.query.filter(~Orders.status.in_([10, 99]), Orders.created_by == session['user']).order_by(desc(Orders.created_date)).first()
        if active_order:
            session['active_order'] = active_order.id
        else:
            session.pop('active_order', None)
    
    for key in session_data_keys:
        data[key] = session.get(key, None)

    return { 'data': data }