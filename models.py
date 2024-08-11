from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())
    spot_price = db.Column(db.Float, nullable=False)
    strike_price = db.Column(db.Float, nullable=False)
    time_to_expiration = db.Column(db.Float, nullable=False)
    risk_free_rate = db.Column(db.Float, nullable=False)
    volatility = db.Column(db.Float, nullable=False)
    option_type = db.Column(db.String(4), nullable=False)
    option_price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Transaction {self.id}: {self.option_type} Option, Price: {self.option_price}>'
