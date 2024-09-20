from flask import render_template, session, redirect, url_for

from app.web import web
from app.models.items import Items, NonvalItems
from app.models.misc import Category, QuantityUnit
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
        
        units = QuantityUnit.query.all()
        units = [ unit.to_dict() for unit in units ]

        categories = Category.query.all()
        categories = [ category.to_dict() for category in categories ]
        categories = sorted(categories, key = lambda x: x['id'])

        return render_template('items/add.html', title = "Add Item", 
                               data = data, units = units, categories = categories)
    
@web.route('/item/<string:id>/edit')
def page_items_edit(id):
    if not is_authenticated(session):
        return redirect(url_for('web.page_login'))
    else:
        data = { 'username': session['user'] }
        
        units = QuantityUnit.query.all()
        units = [ unit.to_dict() for unit in units ]

        categories = Category.query.all()
        categories = [ category.to_dict() for category in categories ]
        categories = sorted(categories, key = lambda x: x['id'])

        item = Items.query.get(id)
        if item is None:
            item = NonvalItems.query.get(id)
            if item is None:
                return redirect(url_for('web.page_items_view_all'))
            else:
                item_type = 'nonvalidated'
        else:
            item_type = 'validated'

        item = item.to_dict()
        data['item_type'] = item_type

        return render_template('items/edit.html', title = "Edit Item", 
                               data = data, units = units, categories = categories, item = item)