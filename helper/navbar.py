from helper.role import Role

navbar_items = {
    Role.ADMINISTRATOR: [ 'items', 'my_orders', 'order_administration', 'profile', 'users' ],
    Role.DIVISION_LEADER: [ 'items', 'my_orders', 'order_administration', 'profile' ],
    Role.DIVISION_USER: [ 'items', 'my_orders', 'profile' ],
    Role.FINANCE_MANAGER: [ 'items', 'order_administration', 'profile' ],
    Role.PROCUREMENT_MANAGER: [ 'items', 'order_administration', 'profile' ],
    Role.SYSTEM: [ 'items', 'order_administration', 'profile', 'users' ]
}

def get_navbar_items(role: Role|int):
    """
    Get the navbar items for the role.
    
    :param role: The role to get the navbar items for. Refer to the Role enum in helper/role.py.
    :returns: The list of navbar items for the role.
    """
    return navbar_items.get(role, [])