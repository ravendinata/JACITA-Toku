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
        'w': '9', 'x': '9', 'y': '9', 'z': '9'
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
    
def generate_item_id(brand, name, variant):
    """
    Generate an item ID from the brand, name, and variant.

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

    t9_brand = zero_pad(convert_t9(brand), 5) if brand else 99
    t9_name = zero_pad(convert_t9(name), 8)
    t9_variant = zero_pad(convert_t9(variant), 7) if variant else 0

    # If any of the fields end with a dot, replace it with a zero
    if is_a_number(t9_brand):
        if t9_brand[-1] == '.':
            t9_brand = t9_brand[:-1] + '0'

    if t9_name[-1] == '.':
        t9_name = t9_name[:-1] + '0'

    if is_a_number(t9_variant):
        if t9_variant[-1] == '.':
            t9_variant = t9_variant[:-1] + '0'

    return f"{t9_brand}-{t9_name}-{t9_variant}"