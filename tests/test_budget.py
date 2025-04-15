import pytest
from datetime import datetime, timedelta
from app import create_app, db
from app.models import User, Transaction, Budget
from config import TestConfig

@pytest.fixture
def app():
    app = create_app(TestConfig)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def _db(app):
    with app.app_context():
        db.create_all()
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture
def session(_db):
    connection = _db.engine.connect()
    transaction = connection.begin()
    
    session = _db.create_scoped_session(
        options={"bind": connection, "binds": {}}
    )
    _db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture
def user(session):
    user = User(username='testuser', email='test@example.com')
    user.set_password('password')
    session.add(user)
    session.commit()
    return user

@pytest.fixture
def budget(session, user):
    budget = Budget(
        category='food',
        limit=1000.0,
        user_id=user.id,
        reset_day=1,
        alert_threshold=80.0
    )
    session.add(budget)
    session.commit()
    return budget

def test_budget_creation(session, user):
    budget = Budget(
        category='food',
        limit=1000.0,
        user_id=user.id,
        reset_day=1,
        alert_threshold=80.0
    )
    session.add(budget)
    session.commit()
    
    assert budget.category == 'food'
    assert budget.limit == 1000.0
    assert budget.user_id == user.id
    assert budget.reset_day == 1
    assert budget.alert_threshold == 80.0

def test_budget_spent_calculation(session, user, budget):
    # Add transactions for the current month
    today = datetime.now()
    transaction1 = Transaction(
        date=today,
        description='Groceries',
        amount=500.0,
        type='expense',
        category='food',
        user_id=user.id
    )
    transaction2 = Transaction(
        date=today,
        description='Restaurant',
        amount=300.0,
        type='expense',
        category='food',
        user_id=user.id
    )
    session.add(transaction1)
    session.add(transaction2)
    session.commit()
    
    assert budget.spent == 800.0
    assert budget.remaining == 200.0
    assert budget.percentage == 80.0
    assert budget.status == 'warning'

def test_budget_exceeded(session, user, budget):
    # Add transaction that exceeds the budget
    transaction = Transaction(
        date=datetime.now(),
        description='Groceries',
        amount=1200.0,
        type='expense',
        category='food',
        user_id=user.id
    )
    session.add(transaction)
    session.commit()
    
    assert budget.spent == 1200.0
    assert budget.remaining == -200.0
    assert budget.percentage == 120.0
    assert budget.status == 'exceeded'

def test_budget_reset_day(session, user):
    # Create budget with reset day on the 15th
    budget = Budget(
        category='food',
        limit=1000.0,
        user_id=user.id,
        reset_day=15,
        alert_threshold=80.0
    )
    session.add(budget)
    session.commit()
    
    assert budget.reset_day == 15

def test_budget_alert_threshold(session, user):
    # Create budget with custom alert threshold
    budget = Budget(
        category='food',
        limit=1000.0,
        user_id=user.id,
        reset_day=1,
        alert_threshold=90.0
    )
    session.add(budget)
    session.commit()
    
    assert budget.alert_threshold == 90.0 