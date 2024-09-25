from flask import session

def inject_session_data():
    session_data_keys = [ 'user', 'active_order' ]
    data = {}
    
    for key in session_data_keys:
        data[key] = session.get(key, None)

    print(f"Context Processor: {data}")

    return { 'data': data }