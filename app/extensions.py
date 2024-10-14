from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect

db = SQLAlchemy(engine_options = { 'pool_recycle': 3600, 'pool_pre_ping': True })

csrf = CSRFProtect()