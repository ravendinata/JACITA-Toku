from flask import render_template, session, redirect, url_for

from app.web import web
from app.models.items import Items, NonvalItems
from app.models.misc import Category, QuantityUnit
from app.models.user import User
from helper.auth import check_login
from helper.endpoint import inject_allowed_operations, check_page_permission, check_page_permissions

@web.route('/items')
@check_login
@inject_allowed_operations
def page_items_view_all(user_operations):
    data = { 'username': session['user'] }
    return render_template('items/view_all.html', use_datatables = True, title = "Items", data = data, operations = user_operations)
    
@web.route('/items/add')
@check_login
@inject_allowed_operations
@check_page_permissions([ 'item_validated/create', 'item_nonvalidated/create' ])
def page_items_add(user_operations):
    data = { 'username': session['user'] }
    
    units = QuantityUnit.query.all()
    units = [ unit.to_dict() for unit in units ]

    categories = Category.query.all()
    categories = [ category.to_dict() for category in categories ]
    categories = sorted(categories, key = lambda x: x['id'])

    return render_template('items/add.html', title = "Add Item", 
                            data = data, units = units, categories = categories, operations = user_operations)
    
@web.route('/item/<string:id>/edit')
@check_login
def page_items_edit(id):
    username = session['user']

    data = { 'username': username }
    
    units = QuantityUnit.query.all()
    units = [ unit.to_dict() for unit in units ]

    categories = Category.query.all()
    categories = [ category.to_dict() for category in categories ]
    categories = sorted(categories, key = lambda x: x['id'])

    item = Items.query.get(id) or NonvalItems.query.get(id)
    if item is None:
        return redirect(url_for('web.page_items_view_all'))

    item_type = 'validated' if isinstance(item, Items) else 'nonvalidated'

    @check_page_permission(f"item_{item_type}/update")
    def page():
        user = User.query.get(username)
        if item.created_by != username and not user.can_update_items():
            return render_template('error/standard.html', title = "Forbidden", code = 403, message = "You are not the creator of this item.", data = data), 403
        else:
            data['item_type'] = item_type
            return render_template('items/edit.html', title = "Edit Item", 
                                    data = data, units = units, categories = categories, item = item.to_dict())

    return page()