from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(engine_options = { 'pool_recycle': 3600, 'pool_pre_ping': True })