#!/usr/bin/env python3
"""
Database setup script for Googol project.
This script initializes or updates the SQLite database with the correct schema.
"""

import sqlite3
import os
import sys
from pathlib import Path

# Colors for terminal output
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'  # No Color

DB_PATH = Path(__file__).parent / "annotations.db"
SCHEMA_PATH = Path(__file__).parent / "db_schema.sql"
BACKUP_PATH = Path(__file__).parent / "annotations.db.backup"


def print_success(msg):
    print(f"{GREEN}✓ {msg}{NC}")


def print_warning(msg):
    print(f"{YELLOW}⚠ {msg}{NC}")


def print_error(msg):
    print(f"{RED}❌ {msg}{NC}")


def check_sqlite_available():
    """Check if SQLite3 is available."""
    try:
        conn = sqlite3.connect(":memory:")
        conn.close()
        return True
    except Exception:
        return False


def get_existing_tables(conn):
    """Get list of existing tables in the database."""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    return [row[0] for row in cursor.fetchall()]


def has_annotation_request_table(conn):
    """Check if annotation_request table exists."""
    tables = get_existing_tables(conn)
    return "annotation_request" in tables


def create_database(force=False):
    """Create or update the database with the schema."""
    print("================================")
    print("Googol Database Setup")
    print("================================")
    print()

    # Check if SQLite is available
    if not check_sqlite_available():
        print_error("SQLite3 is not available")
        print("\nPlease ensure SQLite3 is installed and Python sqlite3 module is available.")
        return False

    print_success("SQLite3 is available")

    # Check if schema file exists
    if not SCHEMA_PATH.exists():
        print_error(f"Schema file not found: {SCHEMA_PATH}")
        return False

    print_success("Schema file found")

    # Check if database exists
    db_exists = DB_PATH.exists()
    needs_backup = False

    if db_exists:
        print()
        print_warning(f"Database already exists at: {DB_PATH}")

        # Check current schema
        conn = sqlite3.connect(str(DB_PATH))
        tables = get_existing_tables(conn)
        conn.close()

        if has_annotation_request_table(sqlite3.connect(str(DB_PATH))):
            print_success("Database appears to have the correct schema")
            print()
            print("Current tables:")
            for table in tables:
                print(f"  ✓ {table}")
            print()

            if not force:
                response = input("Do you want to recreate the database? This will DELETE all existing data! (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print("Keeping existing database.")
                    return True
        else:
            print_warning("Database exists but is missing annotation_request table (old schema)")
            print()

            if not force:
                response = input("Do you want to backup and recreate the database? (yes/no): ")
                if response.lower() not in ['yes', 'y']:
                    print("Keeping existing database.")
                    return True

        # Backup existing database
        print()
        print_warning("Creating backup...")
        import shutil
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print_success(f"Backup created: {BACKUP_PATH}")
        needs_backup = True

        # Remove old database
        DB_PATH.unlink()
        print_success("Old database removed")

    # Create new database with schema
    print()
    print_warning("Creating new database with schema...")

    try:
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        # Read and execute schema
        with open(SCHEMA_PATH, 'r') as f:
            schema_sql = f.read()

        # Execute schema (split by semicolons for better error handling)
        cursor.executescript(schema_sql)
        conn.commit()
        conn.close()

        print_success("Database created successfully")

    except Exception as e:
        print_error(f"Failed to create database: {e}")
        if needs_backup:
            print_warning(f"Restoring from backup...")
            import shutil
            shutil.copy2(BACKUP_PATH, DB_PATH)
        return False

    # Verify the setup
    print()
    print_warning("Verifying database setup...")
    print()

    conn = sqlite3.connect(str(DB_PATH))
    tables = get_existing_tables(conn)

    # Check tables
    print("Tables created:")
    for table in tables:
        print(f"  ✓ {table}")

    # Check for required tables
    required_tables = ["label", "patient", "annotation_request", "annotation"]
    missing_tables = [t for t in required_tables if t not in tables]

    if missing_tables:
        print()
        print_error(f"Missing required tables: {', '.join(missing_tables)}")
        conn.close()
        return False

    # Check indexes
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'")
    indexes = [row[0] for row in cursor.fetchall()]

    print()
    print("Indexes created:")
    for index in indexes:
        print(f"  ✓ {index}")

    # Verify foreign keys are enabled
    cursor.execute("PRAGMA foreign_keys")
    fk_enabled = cursor.fetchone()[0]
    conn.close()

    if fk_enabled:
        print()
        print_success("Foreign keys are enabled")
    else:
        print()
        print_warning("Warning: Foreign keys are not enabled")

    print()
    print("================================")
    print_success("Database setup complete!")
    print("================================")
    print()
    print(f"Database location: {DB_PATH}")
    print()
    print("You can now use the database with:")
    print("  - DB/repository.py (AnnotationRepo)")
    print("  - DB/agentic_repository.py (AgenticAnnotationRepo)")
    print()

    return True


if __name__ == "__main__":
    force = "--force" in sys.argv or "-f" in sys.argv
    success = create_database(force=force)
    sys.exit(0 if success else 1)


