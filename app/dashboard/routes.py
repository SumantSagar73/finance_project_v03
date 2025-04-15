from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.dashboard import bp
from app.models import Transaction, Budget
from app.forms import TransactionForm, BudgetForm
from datetime import datetime

@bp.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    form = BudgetForm()
    if form.validate_on_submit():
        budget = Budget(
            category=form.category.data,
            limit=form.limit.data,
            user_id=current_user.id
        )
        db.session.add(budget)
        db.session.commit()
        flash('Budget added successfully!', 'success')
        return redirect(url_for('dashboard.budget'))
    
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    # Calculate spent amount for each budget
    for budget in budgets:
        spent = db.session.query(db.func.sum(Transaction.amount)).filter(
            Transaction.user_id == current_user.id,
            Transaction.category == budget.category,
            Transaction.type == 'expense',
            db.func.date_trunc('month', Transaction.date) == db.func.date_trunc('month', db.func.current_date())
        ).scalar() or 0
        budget.spent = spent
    
    return render_template('dashboard/budget.html', form=form, budgets=budgets)

@bp.route('/budget/<int:budget_id>', methods=['DELETE'])
@login_required
def delete_budget(budget_id):
    budget = Budget.query.get_or_404(budget_id)
    if budget.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 403
    
    db.session.delete(budget)
    db.session.commit()
    return jsonify({'success': True}) 