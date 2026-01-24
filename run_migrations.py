#!/usr/bin/env python
"""
Script para executar migrações SQL antes de iniciar o app.
Isso garante que as colunas existam no banco antes do SQLAlchemy carregar os modelos.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

def get_database_url():
    """Get and format database URL for psycopg"""
    database_url = os.getenv('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL not set, skipping migrations")
        sys.exit(0)

    # Convert postgres:// to postgresql:// for psycopg
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)

    return database_url

def run_migrations():
    """Run SQL migrations directly using psycopg"""
    try:
        import psycopg
    except ImportError:
        print("psycopg not installed, trying psycopg2...")
        try:
            import psycopg2 as psycopg
        except ImportError:
            print("No PostgreSQL driver found, skipping migrations")
            sys.exit(0)

    database_url = get_database_url()
    migrations_dir = os.path.join(os.path.dirname(__file__), 'migrations')
    migration_file = os.path.join(migrations_dir, 'add_onboarding_fields.sql')

    if not os.path.exists(migration_file):
        print(f"Migration file not found: {migration_file}")
        sys.exit(1)

    print(f"Running migration: {migration_file}")

    try:
        with psycopg.connect(database_url) as conn:
            with conn.cursor() as cur:
                with open(migration_file, 'r') as f:
                    sql = f.read()

                # Execute each statement
                statements = sql.split(';')
                for statement in statements:
                    statement = statement.strip()
                    # Skip empty statements and comments
                    if not statement or statement.startswith('--'):
                        continue

                    try:
                        cur.execute(statement)
                        print(f"  OK: {statement[:60]}...")
                    except Exception as e:
                        # Ignore "already exists" errors
                        error_msg = str(e).lower()
                        if 'already exists' in error_msg or 'duplicate' in error_msg:
                            print(f"  SKIP (already exists): {statement[:60]}...")
                        else:
                            print(f"  WARN: {e}")

                conn.commit()
                print("Migration completed successfully!")

    except Exception as e:
        print(f"Migration error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    run_migrations()
