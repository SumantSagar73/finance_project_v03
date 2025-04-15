from app import create_app, db
from app.models import User
from sqlalchemy import text
import sqlite3

app = create_app()

with app.app_context():
    # Check for duplicate usernames
    print("Checking for duplicate usernames...")
    result = db.session.execute(text("SELECT username, COUNT(*) as count FROM user GROUP BY username HAVING count > 1"))
    duplicates = result.fetchall()
    
    if duplicates:
        print(f"Found {len(duplicates)} usernames with duplicates:")
        for username, count in duplicates:
            print(f"  - {username}: {count} occurrences")
        
        # Delete duplicates, keeping only the first occurrence
        for username, _ in duplicates:
            users = User.query.filter_by(username=username).order_by(User.id).all()
            # Keep the first user, delete the rest
            for user in users[1:]:
                print(f"  - Deleting duplicate user: {user.username} (ID: {user.id})")
                db.session.delete(user)
        
        db.session.commit()
        print("Duplicates removed successfully.")
    else:
        print("No duplicate usernames found.")
    
    # Check for duplicate emails
    print("\nChecking for duplicate emails...")
    result = db.session.execute(text("SELECT email, COUNT(*) as count FROM user GROUP BY email HAVING count > 1"))
    duplicates = result.fetchall()
    
    if duplicates:
        print(f"Found {len(duplicates)} emails with duplicates:")
        for email, count in duplicates:
            print(f"  - {email}: {count} occurrences")
        
        # Delete duplicates, keeping only the first occurrence
        for email, _ in duplicates:
            users = User.query.filter_by(email=email).order_by(User.id).all()
            # Keep the first user, delete the rest
            for user in users[1:]:
                print(f"  - Deleting duplicate user: {user.email} (ID: {user.id})")
                db.session.delete(user)
        
        db.session.commit()
        print("Duplicates removed successfully.")
    else:
        print("No duplicate emails found.")
    
    # List all users
    print("\nCurrent users in database:")
    users = User.query.all()
    for user in users:
        print(f"  - {user.username} ({user.email})")

def update_schema():
    # Connect to the database
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    try:
        # Drop the new table if it exists
        cursor.execute('DROP TABLE IF EXISTS transaction_new')

        # Create a new table with the desired schema
        cursor.execute('''
            CREATE TABLE transaction_new (
                id INTEGER NOT NULL PRIMARY KEY,
                amount FLOAT NOT NULL,
                description VARCHAR(200),
                category VARCHAR(50),
                type VARCHAR(20),
                date DATETIME NOT NULL,
                user_id INTEGER NOT NULL,
                created_at DATETIME,
                receipt_id INTEGER,
                FOREIGN KEY(user_id) REFERENCES user(id),
                FOREIGN KEY(receipt_id) REFERENCES receipt(id)
            )
        ''')

        # Copy data from the old table to the new table
        cursor.execute('''
            INSERT INTO transaction_new (id, amount, description, category, type, date, user_id, created_at)
            SELECT id, amount, description, category, type, date, user_id, created_at
            FROM "transaction"
        ''')

        # Drop the old table
        cursor.execute('DROP TABLE "transaction"')

        # Rename the new table to the original name
        cursor.execute('ALTER TABLE transaction_new RENAME TO "transaction"')

        # Commit the changes
        conn.commit()
        print("Database schema updated successfully!")

    except Exception as e:
        print(f"An error occurred: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    update_schema() 