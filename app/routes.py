from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms.budget_form import BudgetForm
from app.models.budget import Budget
from app.extensions import db
import json

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    form = BudgetForm()
    if form.validate_on_submit():
        budget = Budget(
            user_id=current_user.id,
            category=form.category.data,
            limit=form.limit.data,
            reset_day=request.form.get('reset_day', 1, type=int),
            alert_threshold=request.form.get('alert_threshold', 80.0, type=float)
        )
        db.session.add(budget)
        db.session.commit()
        flash('Budget created successfully!', 'success')
        return redirect(url_for('budget'))
    
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    
    # Calculate summary statistics
    total_budget = sum(budget.limit for budget in budgets)
    total_spent = sum(budget.spent for budget in budgets)
    total_remaining = total_budget - total_spent
    
    return render_template('dashboard/budget.html', 
                         form=form, 
                         budgets=budgets,
                         total_budget=total_budget,
                         total_spent=total_spent,
                         total_remaining=total_remaining)

@app.route('/budget/<int:id>/delete')
@login_required
def delete_budget(id):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id:
        flash('You do not have permission to delete this budget.', 'error')
        return redirect(url_for('budget'))
    
    db.session.delete(budget)
    db.session.commit()
    flash('Budget deleted successfully!', 'success')
    return redirect(url_for('budget'))

@app.route('/budget/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_budget(id):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id:
        flash('You do not have permission to edit this budget.', 'error')
        return redirect(url_for('budget'))
    
    form = BudgetForm(obj=budget)
    if form.validate_on_submit():
        budget.category = form.category.data
        budget.limit = form.limit.data
        budget.reset_day = request.form.get('reset_day', budget.reset_day, type=int)
        budget.alert_threshold = request.form.get('alert_threshold', budget.alert_threshold, type=float)
        db.session.commit()
        flash('Budget updated successfully!', 'success')
        return redirect(url_for('budget'))
    
    return render_template('dashboard/edit_budget.html', form=form, budget=budget)

@main.route('/')
@login_required
def index():
    # Get all transactions for the current user
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expenses
    
    # Prepare transaction data for charts
    transaction_data = [{
        'date': t.date.strftime('%Y-%m-%d'),
        'type': t.type,
        'amount': float(t.amount),
        'category': t.category
    } for t in transactions]
    
    return render_template('dashboard/index.html',
                         transactions=transactions[:10],  # Show only last 10 transactions
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=balance,
                         transaction_data=json.dumps(transaction_data))  # Pass data for charts 