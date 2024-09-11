from app.extensions import db
from helper.auth import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = { 'schema': 'toku' }

    username = db.Column(db.String(12), nullable = False, primary_key = True)
    first_name = db.Column(db.String, nullable = False)
    last_name = db.Column(db.String, nullable = True)
    division = db.Column(db.String, nullable = False)
    role = db.Column(db.Integer, nullable = False, default = 0)
    password = db.Column(db.String, nullable = False)
    email = db.Column(db.String, nullable = False)

    def __repr__(self):
        return f'<User: {self.first_name} {self.last_name} @ {self.username}>'
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != 'password'}
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def is_admin(self):
        return self.role == 1
    
    def is_user(self):
        return self.role != 1