from app.extensions import db
from helper.auth import generate_password_hash, check_password_hash
from helper.navbar import get_navbar_items
from helper.role import Role, check_permission, get_allowed_operations, get_role_text

class Division(db.Model):
    __tablename__ = 'division'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.Integer, nullable = False, primary_key = True)
    abbreviation = db.Column(db.String(3), nullable = False)
    full_name = db.Column(db.String, nullable = False)
    
    def __repr__(self):
        return f'<Division: {self.full_name} [{self.id}]>'
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class User(db.Model):
    __tablename__ = 'user'
    __table_args__ = { 'schema': 'toku' }

    username = db.Column(db.String(12), nullable = False, primary_key = True)
    first_name = db.Column(db.String, nullable = False)
    last_name = db.Column(db.String, nullable = True)
    division_id = db.Column(db.Integer, db.ForeignKey(Division.id), nullable = False, default = 0)
    role = db.Column(db.Integer, nullable = False, default = 0)
    password = db.Column(db.String, nullable = False)
    email = db.Column(db.String, nullable = False)

    def __repr__(self):
        return f'<User: {self.first_name} {self.last_name} @ {self.username}>'
    
    def to_dict(self):
        user_data = {c.name: getattr(self, c.name) for c in self.__table__.columns if c.name != 'password' and c.name != 'role' and c.name != 'division_id'}
        user_data['division'] = Division.query.get(self.division_id).to_dict()
        user_data['role'] = { 'id': self.role, 'text': get_role_text(self.role) }
        return user_data
    
    @property
    def full_name(self):
        string = self.first_name
        if self.last_name:
            string += ' ' + self.last_name
        return string
    
    @property
    def division(self):
        return Division.query.get(self.division_id)
    
    @property
    def navbar_items(self):
        return get_navbar_items(self.role)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def is_admin(self):
        return self.role == Role.ADMINISTRATOR
    
    def is_user(self):
        return self.role != Role.ADMINISTRATOR and self.role != Role.SYSTEM
    
    def can_update_items(self):
        return self.role == Role.ADMINISTRATOR or self.role == Role.PROCUREMENT_MANAGER or self.role == Role.SYSTEM
    
    def can_do(self, action):
        return check_permission(self, action)
    
    def allowed_operations(self):
        return get_allowed_operations(self)