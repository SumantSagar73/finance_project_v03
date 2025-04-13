from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.models import Transaction
from app.forms import TransactionForm
from app import db
from datetime import datetime, timedelta
from collections import defaultdict
import calendar

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    # Get all transactions for the current user
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expenses

    # Prepare chart data
    today = datetime.now()
    
    # Income vs Expenses Chart Data
    def get_weekly_data():
        week_data = defaultdict(lambda: {'income': 0, 'expenses': 0})
        for t in transactions:
            if t.date >= today - timedelta(days=7):
                day = t.date.strftime('%a')
                if t.type == 'income':
                    week_data[day]['income'] += t.amount
                else:
                    week_data[day]['expenses'] += t.amount
        return week_data

    def get_monthly_data():
        month_data = defaultdict(lambda: {'income': 0, 'expenses': 0})
        for t in transactions:
            if t.date >= today - timedelta(days=30):
                week = (t.date.day - 1) // 7 + 1
                if t.type == 'income':
                    month_data[f'Week {week}']['income'] += t.amount
                else:
                    month_data[f'Week {week}']['expenses'] += t.amount
        return month_data

    def get_yearly_data():
        year_data = defaultdict(lambda: {'income': 0, 'expenses': 0})
        for t in transactions:
            if t.date >= today - timedelta(days=365):
                month = t.date.strftime('%b')
                if t.type == 'income':
                    year_data[month]['income'] += t.amount
                else:
                    year_data[month]['expenses'] += t.amount
        return year_data

    # Expense Categories Chart Data
    def get_category_data(period='month'):
        category_data = defaultdict(float)
        if period == 'month':
            start_date = today - timedelta(days=30)
        else:  # year
            start_date = today - timedelta(days=365)
        
        for t in transactions:
            if t.date >= start_date and t.type == 'expense':
                category_data[t.category] += t.amount
        return category_data

    # Monthly Trend Chart Data
    def get_trend_data(months=6):
        trend_data = defaultdict(lambda: {'income': 0, 'expenses': 0, 'balance': 0})
        start_date = today - timedelta(days=30*months)
        
        for t in transactions:
            if t.date >= start_date:
                month = t.date.strftime('%b')
                if t.type == 'income':
                    trend_data[month]['income'] += t.amount
                else:
                    trend_data[month]['expenses'] += t.amount
        
        # Calculate balance for each month
        running_balance = 0
        for month in trend_data:
            running_balance += trend_data[month]['income'] - trend_data[month]['expenses']
            trend_data[month]['balance'] = running_balance
        
        return trend_data

    # Prepare chart data
    chart_data = {
        'incomeExpenses': {
            'week': get_weekly_data(),
            'month': get_monthly_data(),
            'year': get_yearly_data()
        },
        'expenseCategories': {
            'month': get_category_data('month'),
            'year': get_category_data('year')
        },
        'monthlyTrend': {
            '3months': get_trend_data(3),
            '6months': get_trend_data(6),
            'year': get_trend_data(12)
        }
    }

    return render_template('dashboard/index.html',
                         transactions=transactions,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=balance,
                         chart_data=chart_data)

@bp.route('/transaction/add', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            category=form.category.data,
            type=form.type.data,
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()
        flash('Transaction added successfully!')
        return redirect(url_for('main.dashboard'))
    return render_template('dashboard/add_transaction.html', form=form)

@bp.route('/transaction/delete/<int:id>')
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        flash('You cannot delete this transaction.')
        return redirect(url_for('main.dashboard'))
    db.session.delete(transaction)
    db.session.commit()
    flash('Transaction deleted successfully!')
    return redirect(url_for('main.dashboard')) 