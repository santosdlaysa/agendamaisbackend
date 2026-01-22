from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import os

db = SQLAlchemy()

def run_migrations():
    """Run SQL migration files"""
    migrations_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'migrations')
    migration_files = [
        'add_service_payments.sql',
    ]

    for migration_file in migration_files:
        migration_path = os.path.join(migrations_dir, migration_file)
        if os.path.exists(migration_path):
            try:
                with open(migration_path, 'r') as f:
                    sql = f.read()

                # Execute each statement separately
                statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
                for statement in statements:
                    if statement:
                        try:
                            db.session.execute(text(statement))
                        except Exception as e:
                            # Ignore errors for IF NOT EXISTS / IF EXISTS statements
                            if 'already exists' not in str(e).lower() and 'does not exist' not in str(e).lower():
                                print(f"Migration statement warning: {e}")

                db.session.commit()
                print(f"Migration {migration_file} executed successfully")
            except Exception as e:
                db.session.rollback()
                print(f"Migration {migration_file} error: {e}")

def init_db():
    """Initialize database tables"""
    db.create_all()
    run_migrations()