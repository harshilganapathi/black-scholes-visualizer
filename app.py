import os
import numpy as np
import plotly.graph_objs as go
from flask import Flask, render_template, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from scipy.stats import norm
from flask_socketio import SocketIO, emit

# Initialize Flask app and database
app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transactions.db'  # SQLite database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
socketio = SocketIO(app)

# Database model for transaction history
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

# Black-Scholes formula implementation
def black_scholes(S, K, T, r, sigma, option_type="call"):
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)
    
    if option_type == "call":
        price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == "put":
        price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("Option type must be 'call' or 'put'")
    
    return price

@socketio.on('calculate')
def handle_calculate(data):
    try:
        S = float(data.get('S', 100))
        K = float(data.get('K', 100))
        T = float(data.get('T', 1))
        r = float(data.get('r', 0.05))
        sigma = float(data.get('sigma', 0.2))
        option_type = data.get('option_type', 'call')

        # Simple validation checks
        if S <= 0 or K <= 0 or T <= 0 or sigma <= 0:
            raise ValueError("All inputs must be positive numbers.")
        if option_type not in ['call', 'put']:
            raise ValueError("Option type must be 'call' or 'put'.")

        # Calculate the option price
        option_price = black_scholes(S, K, T, r, sigma, option_type)

        # Save the transaction to the database
        transaction = Transaction(
            spot_price=S,
            strike_price=K,
            time_to_expiration=T,
            risk_free_rate=r,
            volatility=sigma,
            option_type=option_type,
            option_price=option_price
        )
        db.session.add(transaction)
        db.session.commit()

        # Update the graph
        S_values = np.linspace(0.5 * S, 1.5 * S, 100)
        prices = [black_scholes(s, K, T, r, sigma, option_type) for s in S_values]

        trace = go.Scatter(x=S_values, y=prices, mode='lines', name=f'{option_type.capitalize()} Option Price')
        layout = go.Layout(title=f'Black-Scholes {option_type.capitalize()} Option Price',
                           xaxis=dict(title='Underlying Asset Price'),
                           yaxis=dict(title='Option Price'))
        fig = go.Figure(data=[trace], layout=layout)

        graphJSON = fig.to_json()
        emit('update_graph', {'graph': graphJSON})

    except ValueError as e:
        emit('error', {'error': str(e)})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/history')
def history():
    transactions = Transaction.query.order_by(Transaction.timestamp.desc()).all()
    return render_template('history.html', transactions=transactions)

if __name__ == '__main__':
    socketio.run(app, debug=True)
