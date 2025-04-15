from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FloatField, SelectField, TextAreaField, SubmitField, DateTimeField, DateField, FileField, DecimalField
from wtforms.validators import DataRequired, Email, EqualTo, Length, NumberRange, Optional
from datetime import datetime
from flask_wtf.file import FileField, FileRequired, FileAllowed
from flask_login import current_user
from app.models import Budget

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

class TransactionForm(FlaskForm):
    date = DateField('Date', validators=[DataRequired()], default=datetime.now)
    description = StringField('Description', validators=[DataRequired()])
    amount = DecimalField('Amount', validators=[DataRequired()])
    type = SelectField('Type', choices=[('income', 'Income'), ('expense', 'Expense')], validators=[DataRequired()])
    category = SelectField('Category', validators=[DataRequired()])
    receipt = FileField('Receipt', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only image and PDF files are allowed!')
    ])
    submit = SubmitField('Save Transaction')

    def __init__(self, *args, **kwargs):
        super(TransactionForm, self).__init__(*args, **kwargs)
        # Default categories for both income and expenses
        self.default_categories = {
            'income': [
                ('salary', 'Salary'),
                ('freelance', 'Freelance'),
                ('investments', 'Investments'),
                ('rental', 'Rental Income'),
                ('other_income', 'Other Income')
            ],
            'expense': [
                ('food', 'Food & Dining'),
                ('transportation', 'Transportation'),
                ('housing', 'Housing'),
                ('utilities', 'Utilities'),
                ('healthcare', 'Healthcare'),
                ('insurance', 'Insurance'),
                ('shopping', 'Shopping'),
                ('entertainment', 'Entertainment'),
                ('education', 'Education'),
                ('travel', 'Travel'),
                ('personal_care', 'Personal Care'),
                ('gifts', 'Gifts & Donations'),
                ('taxes', 'Taxes'),
                ('other_expense', 'Other Expenses')
            ]
        }
        
        # Get budget categories if user is authenticated
        if current_user.is_authenticated:
            budgets = Budget.query.filter_by(user_id=current_user.id).all()
            budget_categories = [(b.category, b.category) for b in budgets]
            
            # Combine budget categories with default categories
            if self.type.data == 'income':
                self.category.choices = self.default_categories['income']
            else:
                self.category.choices = budget_categories + self.default_categories['expense']
        else:
            # If not authenticated, use default categories
            if self.type.data == 'income':
                self.category.choices = self.default_categories['income']
            else:
                self.category.choices = self.default_categories['expense']

class BudgetForm(FlaskForm):
    category = SelectField('Category', validators=[DataRequired()])
    limit = FloatField('Monthly Limit (₹)', validators=[
        DataRequired(),
        NumberRange(min=0, message='Limit must be a positive number')
    ])
    reset_day = SelectField('Reset Day', choices=[(str(i), str(i)) for i in range(1, 32)], validators=[DataRequired()])
    alert_threshold = FloatField('Alert Threshold (%)', validators=[
        DataRequired(),
        NumberRange(min=0, max=100, message='Threshold must be between 0 and 100')
    ])
    submit = SubmitField('Create Budget')

    def __init__(self, *args, **kwargs):
        super(BudgetForm, self).__init__(*args, **kwargs)
        self.category.choices = [
            ('food', 'Food & Dining'),
            ('transportation', 'Transportation'),
            ('housing', 'Housing'),
            ('utilities', 'Utilities'),
            ('healthcare', 'Healthcare'),
            ('insurance', 'Insurance'),
            ('shopping', 'Shopping'),
            ('entertainment', 'Entertainment'),
            ('education', 'Education'),
            ('travel', 'Travel'),
            ('personal_care', 'Personal Care'),
            ('gifts', 'Gifts & Donations'),
            ('taxes', 'Taxes'),
            ('other_expense', 'Other Expenses')
        ]

class ReceiptUploadForm(FlaskForm):
    file = FileField('Receipt', validators=[
        DataRequired(),
        FileAllowed(['jpg', 'jpeg', 'png', 'pdf'], 'Only image and PDF files are allowed!')
    ])
    submit = SubmitField('Upload Receipt') 