from app import db, create_app
from app.models import Budget

def migrate_database():
    app = create_app()
    with app.app_context():
        # Check if columns exist
        inspector = db.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('budget')]
        
        # Add reset_day column if it doesn't exist
        if 'reset_day' not in columns:
            print("Adding reset_day column to budget table...")
            db.engine.execute('ALTER TABLE budget ADD COLUMN reset_day INTEGER NOT NULL DEFAULT 1')
        
        # Add alert_threshold column if it doesn't exist
        if 'alert_threshold' not in columns:
            print("Adding alert_threshold column to budget table...")
            db.engine.execute('ALTER TABLE budget ADD COLUMN alert_threshold FLOAT NOT NULL DEFAULT 80.0')
        
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate_database() 