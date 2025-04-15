from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager
from sqlalchemy.sql import func
import os

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    transactions = db.relationship('Transaction', backref='user', lazy='dynamic')
    budgets = db.relationship('Budget', backref='user', lazy='dynamic')
    receipts = db.relationship('Receipt', backref='user', lazy='dynamic')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Receipt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Receipt {self.original_filename}>'
    
    @property
    def file_url(self):
        return f'/receipts/{self.filename}'
    
    @property
    def formatted_size(self):
        """Return file size in a human-readable format"""
        size = float(self.file_size)  # Create a copy of the file size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    category = db.Column(db.String(50), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f'<Transaction {self.description}>'

class Budget(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(50), nullable=False)
    limit = db.Column(db.Float, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    reset_day = db.Column(db.Integer, nullable=False, default=1)  # Day of month to reset budget
    alert_threshold = db.Column(db.Float, nullable=False, default=80.0)  # Percentage to trigger alert

    @property
    def spent(self):
        return sum(t.amount for t in self.user.transactions 
                  if t.category == self.category and t.type == 'expense' 
                  and t.date.year == datetime.utcnow().year 
                  and t.date.month == datetime.utcnow().month)

    @property
    def remaining(self):
        return self.limit - self.spent

    @property
    def percentage(self):
        return (self.spent / self.limit * 100) if self.limit > 0 else 0

    @property
    def status(self):
        if self.percentage >= 100:
            return 'exceeded'
        elif self.percentage >= self.alert_threshold:
            return 'warning'
        return 'good'

    @classmethod
    def get_smart_suggestion(cls, user_id, category):
        # Get average spending for this category over last 3 months
        three_months_ago = datetime.utcnow() - timedelta(days=90)
        avg_spent = db.session.query(
            func.avg(Transaction.amount)
        ).filter(
            Transaction.user_id == user_id,
            Transaction.category == category,
            Transaction.type == 'expense',
            Transaction.date >= three_months_ago
        ).scalar() or 0

        # Add 10% buffer to the average
        suggested_limit = avg_spent * 1.1
        return round(suggested_limit, 2)

    def __repr__(self):
        return f'<Budget {self.category}>'

@login_manager.user_loader
def load_user(id):
    return User.query.get(int(id)) 