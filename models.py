from trtlme import db

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String(99), nullable=False)
    payment_id = db.Column(db.String(64), nullable=False)
    url = db.Column(db.String(64), nullable=False)
    message = db.Column(db.String(512), nullable=False)
    turtlehash = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    def __repr__(self):
        return '<User %u with Address %s and turtle %i>' % (self.url,self.address,self.turtlehash)

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.String(32), nullable=False)
    paid = db.Column(db.Boolean, default=False, nullable=False)
    def __repr__(self):
        return '<%p Status: %i>' % (self.payment_id,self.paid)
