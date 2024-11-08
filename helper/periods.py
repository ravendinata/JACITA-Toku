from datetime import datetime
from dateutil.relativedelta import relativedelta

def get_current_month():
    now = datetime.now()
    return f"{now.year}/{now.month:02d}"

def get_next_month():
    now = datetime.now()
    next_month = now + relativedelta(months = 1)
    return f"{next_month.year}/{next_month.month:02d}"

def get_current_period():
    return get_available_periods()[0]

def get_available_periods(length = 3):
    today = datetime.now()
    
    if today.day <= 25:
        first_period = today + relativedelta(months = 1)
    else:
        first_period = today + relativedelta(months = 2)
    
    periods = []
    
    # Generate the next 3 periods
    for i in range(length):
        target_month = first_period + relativedelta(months = i)
        order_start = (target_month + relativedelta(months = -2, day = 25))
        order_end = (target_month + relativedelta(months = -1, day = 25))
        
        period = {
            'short': target_month.strftime('%Y/%m'),
            'long': target_month.strftime('%B %Y'),
            'window': f"{order_start.strftime('%d %B')} - {order_end.strftime('%d %B, %Y')}",
            'start_date': order_start,
            'end_date': order_end
        }
        periods.append(period)
    
    return periods