from . import db

class Restaurant(db.Model):
    id = db.Column('id', db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    address = db.Column(db.String(200))
    pincode = db.Column(db.String(50))
    number = db.Column(db.String(50))

    def __init__(self, name, address, pincode, number):
        self.name = name
        self.address = address
        self.pincode = pincode
        self.number = number
