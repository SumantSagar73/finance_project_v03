from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, send_from_directory, current_app, abort, send_file
from flask_login import login_required, current_user
from app.models import Transaction, Budget, Receipt
from app.forms import TransactionForm, BudgetForm, ReceiptUploadForm
from app import db
from datetime import datetime, timedelta
from sqlalchemy import func
from collections import defaultdict
import os
from werkzeug.utils import secure_filename
import json
import time
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from io import BytesIO

main = Blueprint('main', __name__)

@main.route('/')
@main.route('/index')
def index():
    if current_user.is_authenticated:
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
                             transactions=transactions,
                             total_income=total_income,
                             total_expenses=total_expenses,
                             balance=balance,
                             transaction_data=transaction_data)
    return render_template('index.html')

@main.route('/dashboard')
@login_required
def dashboard():
    # Get all transactions for the current user
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.date.desc()).all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expenses

    # Get date range for charts
    today = datetime.now()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago = today - timedelta(days=365)

    # Prepare chart data
    chart_data = {
        'incomeExpenses': {
            'week': prepare_income_expenses_data(week_ago),
            'month': prepare_income_expenses_data(month_ago),
            'year': prepare_income_expenses_data(year_ago)
        },
        'expenseCategories': {
            'month': prepare_category_data(month_ago),
            'year': prepare_category_data(year_ago)
        },
        'monthlyTrend': {
            '3months': prepare_monthly_trend_data(3),
            '6months': prepare_monthly_trend_data(6),
            'year': prepare_monthly_trend_data(12)
        }
    }

    # Prepare transaction data for charts
    transaction_data = [{
        'date': t.date.strftime('%Y-%m-%d'),
        'type': t.type,
        'amount': float(t.amount),
        'category': t.category
    } for t in transactions]

    return render_template('dashboard/index.html',
                         transactions=transactions,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=balance,
                         chart_data=chart_data,
                         transaction_data=transaction_data)

def prepare_income_expenses_data(start_date):
    # Get transactions within date range
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date >= start_date
    ).all()

    # Group by date
    daily_data = defaultdict(lambda: {'income': 0, 'expenses': 0})
    for t in transactions:
        date_str = t.date.strftime('%Y-%m-%d')
        if t.type == 'income':
            daily_data[date_str]['income'] += t.amount
        else:
            daily_data[date_str]['expenses'] += t.amount

    # Sort by date
    sorted_dates = sorted(daily_data.keys())
    
    return {
        'labels': sorted_dates,
        'income': [daily_data[date]['income'] for date in sorted_dates],
        'expenses': [daily_data[date]['expenses'] for date in sorted_dates]
    }

def prepare_category_data(start_date_or_transactions):
    # Check if the input is a list of transactions or a start date
    if isinstance(start_date_or_transactions, list):
        # If it's a list, assume it's transactions
        transactions = start_date_or_transactions
    else:
        # If it's not a list, assume it's a start date
        start_date = start_date_or_transactions
        
        # Get expense transactions within date range
        transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.type == 'expense',
            Transaction.date >= start_date
        ).all()

    # Group by category
    category_data = defaultdict(float)
    for t in transactions:
        if t.type == 'expense':  # Only include expenses
            category_data[t.category] += t.amount

    return {
        'labels': list(category_data.keys()),
        'data': list(category_data.values())
    }

def prepare_monthly_trend_data(months_or_transactions):
    # Calculate start date
    today = datetime.now()
    
    # Check if the input is a list of transactions or a number of months
    if isinstance(months_or_transactions, list):
        # If it's a list, assume it's transactions
        transactions = months_or_transactions
        # Use a default of 6 months for the date range
        months = 6
    else:
        # If it's not a list, assume it's a number of months
        months = months_or_transactions
        # Ensure months is an integer
        if isinstance(months, list):
            months = months[0]  # Take the first value if it's a list
        
        # Calculate start date
        start_date = today - timedelta(days=30 * months)
        
        # Get transactions within date range
        transactions = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.date >= start_date
        ).all()

    # Group by month
    monthly_data = defaultdict(lambda: {'income': 0, 'expenses': 0})
    for t in transactions:
        month_key = t.date.strftime('%Y-%m')
        if t.type == 'income':
            monthly_data[month_key]['income'] += t.amount
        else:
            monthly_data[month_key]['expenses'] += t.amount

    # Sort by month
    sorted_months = sorted(monthly_data.keys())
    
    # Calculate balance for each month
    balance = 0
    balance_data = []
    for month in sorted_months:
        balance += monthly_data[month]['income'] - monthly_data[month]['expenses']
        balance_data.append(balance)

    return {
        'labels': sorted_months,
        'income': [monthly_data[month]['income'] for month in sorted_months],
        'expenses': [monthly_data[month]['expenses'] for month in sorted_months],
        'balance': balance_data
    }

@main.route('/add_transaction', methods=['GET', 'POST'])
@login_required
def add_transaction():
    form = TransactionForm()
    if form.validate_on_submit():
        # Check if this is an expense transaction
        if form.type.data == 'expense':
            # Get the corresponding budget
            budget = Budget.query.filter_by(
                user_id=current_user.id,
                category=form.category.data
            ).first()
            
            if budget:
                # Calculate current month's spending
                current_month = datetime.now().replace(day=1)
                monthly_expenses = Transaction.query.filter(
                    Transaction.user_id == current_user.id,
                    Transaction.category == form.category.data,
                    Transaction.type == 'expense',
                    Transaction.date >= current_month
                ).with_entities(func.sum(Transaction.amount)).scalar() or 0
                
                # Add the new transaction amount
                total_spending = monthly_expenses + float(form.amount.data)
                
                # Check if this would exceed the budget
                if total_spending > budget.limit:
                    flash(f'Warning: This transaction would exceed your budget for {budget.category}! Current spending: ₹{monthly_expenses:.2f}, Budget limit: ₹{budget.limit:.2f}', 'warning')
                elif total_spending >= (budget.limit * budget.alert_threshold / 100):
                    flash(f'Alert: You are approaching your budget limit for {budget.category}! Current spending: ₹{monthly_expenses:.2f}, Budget limit: ₹{budget.limit:.2f}', 'warning')
        
        # Create and save the transaction
        transaction = Transaction(
            date=form.date.data,
            description=form.description.data,
            amount=form.amount.data,
            type=form.type.data,
            category=form.category.data,
            user_id=current_user.id
        )
        
        try:
            db.session.add(transaction)
            db.session.commit()
            flash('Transaction added successfully!', 'success')
            return redirect(url_for('main.dashboard'))
        except Exception as e:
            db.session.rollback()
            flash('Error adding transaction. Please try again.', 'error')
            
    return render_template('dashboard/add_transaction.html', form=form)

@main.route('/edit_transaction/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        abort(403)
    
    form = TransactionForm(obj=transaction)
    if form.validate_on_submit():
        transaction.date = form.date.data
        transaction.description = form.description.data
        transaction.amount = form.amount.data
        transaction.type = form.type.data
        transaction.category = form.category.data
        
        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('dashboard/edit_transaction.html', form=form, transaction=transaction)

@main.route('/transaction/delete/<int:id>', methods=['GET', 'POST'])
@login_required
def delete_transaction(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        flash('You do not have permission to delete this transaction.', 'error')
        return redirect(url_for('main.dashboard'))
    
    try:
        db.session.delete(transaction)
        db.session.commit()
        flash('Transaction deleted successfully!', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Error deleting transaction. Please try again.', 'error')
    
    return redirect(url_for('main.dashboard'))

@main.route('/transaction/<int:id>/upload-receipt', methods=['GET', 'POST'])
@login_required
def upload_receipt(id):
    transaction = Transaction.query.get_or_404(id)
    if transaction.user_id != current_user.id:
        flash('You do not have permission to upload receipts for this transaction.', 'error')
        return redirect(url_for('main.dashboard'))
    
    form = ReceiptUploadForm()
    if form.validate_on_submit():
        if form.receipt.data:
            # Generate a unique filename
            filename = secure_filename(f"{current_user.id}_{transaction.id}_{form.receipt.data.filename}")
            # Save the file
            form.receipt.data.save(os.path.join(current_app.config['UPLOAD_FOLDER'], filename))
            # Update transaction with receipt path
            transaction.receipt_path = filename
            db.session.commit()
            flash('Receipt uploaded successfully!', 'success')
            return redirect(url_for('main.dashboard'))
    
    return render_template('dashboard/upload_receipt.html', form=form, transaction=transaction)

@main.route('/view_receipt/<int:receipt_id>')
@login_required
def view_receipt(receipt_id):
    receipt = Receipt.query.get_or_404(receipt_id)
    if receipt.user_id != current_user.id:
        flash('You do not have permission to view this receipt.', 'error')
        return redirect(url_for('main.dashboard'))
    
    return send_from_directory(
        os.path.join('app', 'static', 'uploads', 'receipts'),
        receipt.filename,
        as_attachment=False
    )

@main.route('/receipt/<filename>')
@login_required
def view_transaction_receipt(filename):
    """View an uploaded receipt."""
    try:
        return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
    except FileNotFoundError:
        flash('Receipt not found.', 'error')
        return redirect(url_for('main.dashboard'))

@main.route('/reports')
@login_required
def reports():
    # Get date range from query parameters or default to current month
    start_date = request.args.get('start_date', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Convert string dates to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get transactions for the date range
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date.between(start_date, end_date)
    ).all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expenses
    
    # Prepare monthly statistics
    monthly_stats = {}
    for t in transactions:
        month_key = t.date.strftime('%Y-%m')
        if month_key not in monthly_stats:
            monthly_stats[month_key] = {'income': 0, 'expense': 0}
        if t.type == 'income':
            monthly_stats[month_key]['income'] += float(t.amount)
        else:
            monthly_stats[month_key]['expense'] += float(t.amount)
    
    # Prepare monthly data for charts
    monthly_data = {
        'labels': list(monthly_stats.keys()),
        'income': [monthly_stats[key]['income'] for key in monthly_stats],
        'expenses': [monthly_stats[key]['expense'] for key in monthly_stats]
    }
    
    # Prepare category data for expense chart
    expense_category_totals = defaultdict(float)
    for t in transactions:
        if t.type == 'expense':
            expense_category_totals[t.category] += float(t.amount)
    
    total_expenses = sum(expense_category_totals.values())
    category_data = {
        'labels': list(expense_category_totals.keys()),
        'data': list(expense_category_totals.values()),
        'percentages': [float(amount) / total_expenses * 100 if total_expenses > 0 else 0 
                       for amount in expense_category_totals.values()]
    }
    
    # Prepare income categories data
    income_categories = {}
    for t in transactions:
        if t.type == 'income':
            if t.category not in income_categories:
                income_categories[t.category] = {'amount': 0, 'percentage': 0}
            income_categories[t.category]['amount'] += float(t.amount)
    
    # Calculate percentages for income categories
    if total_income > 0:
        for category in income_categories:
            income_categories[category]['percentage'] = (income_categories[category]['amount'] / total_income) * 100
    
    # Prepare expense categories data
    expense_categories = {}
    for t in transactions:
        if t.type == 'expense':
            if t.category not in expense_categories:
                expense_categories[t.category] = {'amount': 0, 'percentage': 0}
            expense_categories[t.category]['amount'] += float(t.amount)
    
    # Calculate percentages for expense categories
    if total_expenses > 0:
        for category in expense_categories:
            expense_categories[category]['percentage'] = (expense_categories[category]['amount'] / total_expenses) * 100
    
    # Get transactions with receipts
    transactions_with_receipts = [t for t in transactions if hasattr(t, 'receipt_id') and t.receipt_id is not None]
    
    # Get all unique categories for the filter dropdown
    categories = sorted(set(t.category for t in transactions))
    
    return render_template('dashboard/reports.html',
                         transactions=transactions,
                         transactions_with_receipts=transactions_with_receipts,
                         total_income=total_income,
                         total_expenses=total_expenses,
                         balance=balance,
                         monthly_data=monthly_data,
                         category_data=category_data,
                         income_categories=income_categories,
                         expense_categories=expense_categories,
                         categories=categories,
                         start_date=start_date.strftime('%Y-%m-%d'),
                         end_date=end_date.strftime('%Y-%m-%d'))

@main.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    form = BudgetForm()
    if form.validate_on_submit():
        budget = Budget(
            category=form.category.data,
            limit=form.limit.data,
            reset_day=form.reset_day.data,
            alert_threshold=form.alert_threshold.data,
            user_id=current_user.id
        )
        db.session.add(budget)
        db.session.commit()
        flash('Budget created successfully!', 'success')
        return redirect(url_for('main.budget'))
    
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard/budget.html', form=form, budgets=budgets)

@main.route('/budget/<int:id>/delete', methods=['GET', 'POST'])
@login_required
def delete_budget(id):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id:
        abort(403)
    db.session.delete(budget)
    db.session.commit()
    flash('Budget deleted successfully.', 'success')
    return redirect(url_for('main.budget'))

@main.route('/budget/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_budget(id):
    budget = Budget.query.get_or_404(id)
    if budget.user_id != current_user.id:
        abort(403)
    
    form = BudgetForm(obj=budget)
    if form.validate_on_submit():
        budget.category = form.category.data
        budget.limit = form.limit.data
        budget.reset_day = form.reset_day.data
        budget.alert_threshold = form.alert_threshold.data
        db.session.commit()
        flash('Budget updated successfully.', 'success')
        return redirect(url_for('main.budget'))
    
    return render_template('dashboard/edit_budget.html', form=form, budget=budget)

@main.route('/download_report/<format>')
@login_required
def download_report(format):
    # Get date range from query parameters
    start_date = request.args.get('start_date', datetime.now().replace(day=1).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Convert string dates to datetime objects
    start_date = datetime.strptime(start_date, '%Y-%m-%d')
    end_date = datetime.strptime(end_date, '%Y-%m-%d')
    
    # Get transactions for the date range
    transactions = Transaction.query.filter(
        Transaction.user_id == current_user.id,
        Transaction.date.between(start_date, end_date)
    ).all()
    
    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expenses = sum(t.amount for t in transactions if t.type == 'expense')
    balance = total_income - total_expenses
    
    if format == 'excel':
        # Create a DataFrame
        data = []
        for t in transactions:
            data.append({
                'Date': t.date.strftime('%Y-%m-%d'),
                'Description': t.description,
                'Category': t.category,
                'Type': t.type,
                'Amount': float(t.amount)
            })
        
        df = pd.DataFrame(data)
        
        # Create a BytesIO object
        output = BytesIO()
        
        # Create Excel writer
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            # Write transactions
            df.to_excel(writer, sheet_name='Transactions', index=False)
            
            # Write summary
            summary_data = {
                'Metric': ['Total Income', 'Total Expenses', 'Balance'],
                'Amount': [total_income, total_expenses, balance]
            }
            pd.DataFrame(summary_data).to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'financial_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.xlsx'
        )
    
    elif format == 'pdf':
        # Create a BytesIO object
        output = BytesIO()
        
        # Create PDF document
        doc = SimpleDocTemplate(output, pagesize=letter)
        elements = []
        
        # Add summary table
        summary_data = [
            ['Metric', 'Amount'],
            ['Total Income', f'₹{total_income:.2f}'],
            ['Total Expenses', f'₹{total_expenses:.2f}'],
            ['Balance', f'₹{balance:.2f}']
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        
        # Add transactions table
        transactions_data = [['Date', 'Description', 'Category', 'Type', 'Amount']]
        for t in transactions:
            transactions_data.append([
                t.date.strftime('%Y-%m-%d'),
                t.description,
                t.category,
                t.type,
                f'₹{float(t.amount):.2f}'
            ])
        
        transactions_table = Table(transactions_data)
        transactions_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(transactions_table)
        
        # Build PDF
        doc.build(elements)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'financial_report_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.pdf'
        )
    
    return redirect(url_for('main.reports'))

@main.route('/check_budgets')
@login_required
def check_budgets():
    """Check all budgets and return notifications for exceeded or warning budgets."""
    notifications = []
    today = datetime.now()
    
    # Get all budgets for the current user
    budgets = Budget.query.filter_by(user_id=current_user.id).all()
    
    for budget in budgets:
        # Calculate current month's spending
        current_month = today.replace(day=1)
        monthly_expenses = Transaction.query.filter(
            Transaction.user_id == current_user.id,
            Transaction.category == budget.category,
            Transaction.type == 'expense',
            Transaction.date >= current_month
        ).with_entities(func.sum(Transaction.amount)).scalar() or 0
        
        # Check if budget is exceeded
        if monthly_expenses > budget.limit:
            notifications.append({
                'type': 'danger',
                'message': f'Budget exceeded for {budget.category}! Current spending: ₹{monthly_expenses:.2f}, Budget limit: ₹{budget.limit:.2f}'
            })
        # Check if budget is approaching limit
        elif monthly_expenses >= (budget.limit * budget.alert_threshold / 100):
            notifications.append({
                'type': 'warning',
                'message': f'Approaching budget limit for {budget.category}! Current spending: ₹{monthly_expenses:.2f}, Budget limit: ₹{budget.limit:.2f}'
            })
    
    return jsonify({'notifications': notifications})