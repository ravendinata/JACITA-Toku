import json
import os
from datetime import datetime

with open('config.json') as config_file:
    config = json.load(config_file)

OUTPUT_DIR = config['log_output_dir']
os.makedirs(OUTPUT_DIR, exist_ok = True)

def log_creation(object, user):
    """
    Log a create transaction to a local log JSON file

    :param object: The object that the transaction is about.
    :param action: The action that was performed on the object.
    :param user: The user that performed the action.
    """
    date_today = datetime.now().strftime("%Y%m%d")
    timestamp = str(datetime.now().isoformat())

    if hasattr(object, 'id'):
        id = object.id
    elif hasattr(object, 'username'):
        id = object.username

    data = {
        'timestamp': timestamp,
        'user': user,
        'type': object.__class__.__name__,
        'object_id': id
    }

    with open(f"{OUTPUT_DIR}/{date_today}_creations.tokulog", 'a') as f:
        f.write(json.dumps(data))
        f.write("\n")

def log_update(object_post, object_pre, user):
    """
    Log an update transaction to a local log JSON file

    :param object_post: The object after the update.
    :param object_pre: The object before the update.
    :param user: The user that performed the action.
    """
    date_today = datetime.now().strftime("%Y%m%d")
    
    object_post_dict = object_post.to_dict()
    object_post_dict['type'] = object_post.__class__.__name__

    for key in object_post_dict:
        if type(object_post_dict[key]) is not str:
            object_post_dict[key] = str(object_post_dict[key])

    object_pre_dict = object_pre.to_dict()
    object_pre_dict['type'] = object_pre.__class__.__name__

    for key in object_pre_dict:
        if type(object_pre_dict[key]) is not str:
            object_pre_dict[key] = str(object_pre_dict[key])

    timestamp = str(datetime.now().isoformat())

    changed_fields = {}
    for key in object_post_dict:
        if key in object_pre_dict and object_post_dict[key] != object_pre_dict[key] and key != 'modification_date' and key != 'modification_by':
            changed_fields[key] = { 'before': object_pre_dict[key], 'after': object_post_dict[key] }

    if len(changed_fields) == 0:
        return

    data = {
        'timestamp': timestamp,
        'user': user,
        'object_id': object_post.id,
        'type': object_post.__class__.__name__,
        'changed_fields': changed_fields
    }
    
    with open(f"{OUTPUT_DIR}/{date_today}_updates.tokulog", 'a') as f:
        f.write(json.dumps(data))
        f.write("\n")

def log_deletion(object, user):
    """
    Log a delete transaction to a local log JSON file

    :param object: The object that the transaction is about.
    :param action: The action that was performed on the object.
    :param user: The user that performed the action.
    """
    date_today = datetime.now().strftime("%Y%m%d")
    
    object_dict = object.to_dict()
    object_dict['type'] = object.__class__.__name__

    for key in object_dict:
        if type(object_dict[key]) is not str:
            object_dict[key] = str(object_dict[key])

    timestamp = str(datetime.now().isoformat())

    data = {
        'timestamp': timestamp,
        'user': user,
        'object': object_dict
    }

    with open(f"{OUTPUT_DIR}/{date_today}_deletions.tokulog", 'a') as f:
        f.write(json.dumps(data))
        f.write("\n")

def log_login(user, ip_address):
    """
    Log a login to a local log JSON file

    :param user: The user that logged in.
    """
    date_today = datetime.now().strftime("%Y%m%d")
    timestamp = str(datetime.now().isoformat())

    with open(f"{OUTPUT_DIR}/{date_today}_logins.tokulog", 'a') as f:
        f.write(json.dumps({
            'timestamp': timestamp,
            'user': user,
            'operation': 'login',
            'ip_address': ip_address
        }))

def log_logout(user):
    """
    Log a logout to a local log JSON file

    :param user: The user that logged out.
    """
    date_today = datetime.now().strftime("%Y%m%d")
    timestamp = str(datetime.now().isoformat())

    with open(f"{OUTPUT_DIR}/{date_today}_logins.tokulog", 'a') as f:
        f.write(json.dumps({
            'timestamp': timestamp,
            'user': user,
            'operation': 'logout'
        }))

def log_system_event(module, event):
    """
    Log a system event to a local log JSON file

    :param event: The event that occurred.
    :param module: The module that the event occurred in.
    """
    date_today = datetime.now().strftime("%Y%m%d")
    timestamp = str(datetime.now().isoformat())

    with open(f"{OUTPUT_DIR}/{date_today}_system_events.tokulog", 'a') as f:
        f.write(json.dumps({
            'timestamp': timestamp,
            'module': module,
            'event': event
        }))