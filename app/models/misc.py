from app.extensions import db

class Category(db.Model):
    __tablename__ = 'category'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.Integer, primary_key = True)
    name = db.Column(db.String, nullable = False)
    description = db.Column(db.String, nullable = True)

    def __repr__(self):
        return f'<Category: {self.name} [{self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }
    
class QuantityUnit(db.Model):
    __tablename__ = 'quantity_unit'
    __table_args__ = { 'schema': 'toku' }

    id = db.Column(db.Integer, primary_key = True)
    unit = db.Column(db.String, nullable = False)
    long_name = db.Column(db.String, nullable = False)

    def __repr__(self):
        return f'<QuantityUnit: {self.name} [{self.id}]>'
    
    def to_dict(self):
        return { c.name: getattr(self, c.name) for c in self.__table__.columns }