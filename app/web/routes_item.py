import json

from flask import render_template, session, redirect, request, url_for

from app.web import web
from app.models.items import Items, NonvalItems
from app.models.logs import ItemPriceUpdateLog
from app.models.misc import Category, QuantityUnit
from app.models.user import User
from helper.auth import check_login
from helper.endpoint import inject_allowed_operations, check_page_permission, check_page_permissions

@web.route('/items')
@check_login
@inject_allowed_operations
def page_items_view_all(user_operations):
    return render_template('items/view_all.html', use_datatables = True, title = "Items", operations = user_operations)

@web.route('/items/grouped')
@check_login
@inject_allowed_operations
def page_items_view_grouped(user_operations):
    return render_template('items/view_grouped.html', use_datatables = True, title = "Items", operations = user_operations)
    
@web.route('/items/add')
@check_login
@inject_allowed_operations
@check_page_permissions([ 'item_validated/create', 'item_nonvalidated/create' ])
def page_items_add(user_operations):
    units = QuantityUnit.query.all()
    units = [ unit.to_dict() for unit in units ]

    categories = Category.query.all()
    categories = [ category.to_dict() for category in categories ]
    categories = sorted(categories, key = lambda x: x['id'])

    return render_template('items/add.html', title = "Add Item", 
                            units = units, categories = categories, operations = user_operations)

@web.route('/items/bulk_add')
@check_login
@check_page_permission('item_validated/create')
def page_items_bulk_add():
    units = QuantityUnit.query.all()
    units = [ unit.to_dict() for unit in units ]

    categories = Category.query.all()
    categories = [ category.to_dict() for category in categories ]
    categories = sorted(categories, key = lambda x: x['id'])

    return render_template('items/bulk_add.html', title = "Bulk Add Items", units = units, categories = categories)
    
@web.route('/item/<string:id>/edit')
@check_login
def page_items_edit(id):
    username = session['user']
    
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
    @inject_allowed_operations
    def page(user_operations):
        user = User.query.get(username)
        if item.created_by != username and not user.can_update_items():
            return render_template('error/standard.html', title = "Forbidden", code = 403, message = "You are not the creator of this item."), 403
        else:
            return render_template('items/edit.html', title = "Edit Item", operations = user_operations,
                                    item_type = item_type, units = units, categories = categories, item = item.to_dict())

    return page()

@web.route('/items/bulk_edit')
@check_login
def page_items_bulk_edit():
    item_ids = request.args.get('items')
    item_ids = json.loads(item_ids)

    units = QuantityUnit.query.all()
    units = [ unit.to_dict() for unit in units ]

    categories = Category.query.all()
    categories = [ category.to_dict() for category in categories ]
    categories = sorted(categories, key = lambda x: x['id'])

    items = []
    for item_id in item_ids:
        item = Items.query.get(item_id)
        if item is not None:
            items.append(item.to_dict())

    return render_template('items/bulk_edit.html', title = "Bulk Edit Items", items = items,
                           units = units, categories = categories)

# =============
# PRICE HISTORY
# =============

@web.route('/item/<string:id>/price_history')
@check_login
def page_items_price_history(id):
    price_history = ItemPriceUpdateLog.query.filter_by(item_id = id).all()
    item = Items.query.get(id) or NonvalItems.query.get(id)

    return render_template('items/price_history.html', title = "Price History", use_datatables = True,
                           price_history = [ log.to_dict() for log in price_history ], item = item.to_dict())