import random
import re
import uuid

from app.models.items import Items, NonvalItems
from app.models.user import Division

# ===============
# GENERIC METHODS
# ===============

def is_a_number(value):
    """
    Check if a value is a number.

    Parameters:
    value : any
        The value to check.

    Returns:
    bool
        True if the value is a number, False otherwise.
    """
    try:
        float(value)
        return True
    except ValueError:
        return False

def convert_t9(string):
    """
    Convert a string to T9 format.

    Parameters:
    string : str
        The string to convert.

    Returns:
    str
        The string in T9 format.
    """
    t9 = {
        'a': '2', 'b': '2', 'c': '2',
        'd': '3', 'e': '3', 'f': '3',
        'g': '4', 'h': '4', 'i': '4',
        'j': '5', 'k': '5', 'l': '5',
        'm': '6', 'n': '6', 'o': '6',
        'p': '7', 'q': '7', 'r': '7', 's': '7',
        't': '8', 'u': '8', 'v': '8',
        'w': '9', 'x': '9', 'y': '9', 'z': '9',
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4',
        '5': '5', '6': '6', '7': '7', '8': '8', '9': '9'
    }

    return ''.join([ t9.get(char, ".") for char in string.lower() ])

def zero_pad(string, length, direction = 'right'):
    """
    Zero-pad a T9 string to a specified length. Trims the string if it exceeds the length.

    Parameters:
    string : str
        The string to zero-pad.

    length : int
        The length to zero-pad the string to.

    direction : str
        The direction to zero-pad the string to. Default is 'right'.

    Returns:
    str
        The zero-padded string.
    """

    if len(string) > length:
        return string[:length]

    if direction == 'left':
        return string.zfill(length)
    else:
        return string.ljust(length, '0')
    
def replace_start_end_dot(string: str):
    """
    Replace the starting and ending dot of a string with a zero.

    Parameters:
    string : str
        The string to replace the starting and ending dot.

    Returns:
    str
        The string with the starting and ending dot replaced.
    """

    if string[0] == '.':
        string = '0' + string[1:]
    if string[-1] == '.':
        string = string[:-1] + '0'

    return string

def jumble_string(string):
    """
    Jumble a string.

    Parameters:
    string : str
        The string to jumble.

    Returns:
    str
        The jumbled string.
    """

    return ''.join(random.sample(string, len(string)))

# ======================
# ORDER SPECIFIC METHODS
# ======================

def generate_order_id(period, division_id):
    """
    Generate an order ID from the period and division.

    Parameters:
    period : str
        The period of the order.

    division : str
        The division of the order.

    Returns:
    str
        The generated order ID.
    """

    period_formatted = period.replace("/", ".")
    division_abbreviation = Division.query.get(division_id).abbreviation
    random_id = str(uuid.uuid4().int)[:6].upper()

    return f"{period_formatted}-{division_abbreviation}-{random_id}"

# =====================
# ITEM SPECIFIC METHODS
# =====================
    
def generate_item_id(brand, name, variant):
    """
    Generate an item ID from the brand, name, and variant.
    The generated ID is in the format of T9-converted brand, name, and variant.
    It will check if the generated ID already exists in the database and jumble the variant if it does.

    Parameters:
    brand : str
        The brand of the item.

    name : str
        The name of the item.

    variant : str
        The variant of the item.

    Returns:
    str
        The generated item ID.
    """

    t9_brand = zero_pad(convert_t9(brand), 5) if brand else "99"
    t9_name = zero_pad(convert_t9(name), 8)
    t9_variant = zero_pad(convert_t9(variant), 7) if variant else "0"

    # If any of the fields end or start with a dot, replace it with a zero
    t9_brand = replace_start_end_dot(t9_brand)
    t9_name = replace_start_end_dot(t9_name)
    t9_variant = replace_start_end_dot(t9_variant)

    result = f"{t9_brand}-{t9_name}-{t9_variant}"

    check_item = Items.query.get(result) or NonvalItems.query.get(result)
    if check_item:
        print(f"Item ID {result} already exists but item is different, jumbling the variant to generate a new ID.")
        result = generate_item_id(brand, name, jumble_string(variant))

    # Secondary check - If still exists, use a random ID for the variant
    check_item = Items.query.get(result) or NonvalItems.query.get(result)
    if check_item:
        print(f"Item ID {result} already exists, jumbling the name to generate a new ID.")
        random_id = str(uuid.uuid4().int)[:7].upper()
        result = generate_item_id(brand, name, random_id)

    # If there is a consecutive dot, replace it with a zero
    result = re.sub(r'\.{2,}', '.0', result)

    return result