from app import create_app, db
from app.models import User, Transaction, Budget

app = create_app()

with app.app_context():
    # Find the user with username 'sumant'
    user = User.query.filter_by(username='sumant').first()
    
    if user:
        print(f"Found user: {user.username} ({user.email})")
        
        # Delete user's transactions
        print("Deleting user's transactions...")
        transactions = Transaction.query.filter_by(user_id=user.id).all()
        for transaction in transactions:
            db.session.delete(transaction)
        db.session.commit()
        print(f"Deleted {len(transactions)} transactions.")
        
        # Delete user's budgets
        print("Deleting user's budgets...")
        budgets = Budget.query.filter_by(user_id=user.id).all()
        for budget in budgets:
            db.session.delete(budget)
        db.session.commit()
        print(f"Deleted {len(budgets)} budgets.")
        
        # Delete the user
        print("Deleting user...")
        db.session.delete(user)
        db.session.commit()
        print("User deleted successfully.")
    else:
        print("User with username 'sumant' not found.")
    
    # List all users
    print("\nCurrent users in database:")
    users = User.query.all()
    for user in users:
        print(f"  - {user.username} ({user.email})") 