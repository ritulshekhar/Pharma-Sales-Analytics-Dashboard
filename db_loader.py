"""
PostgreSQL Database Loader
Reads the generated CSV file and inserts the data into PostgreSQL.
Automatically creates the target database if it does not exist,
applies the database schema (tables, constraints, indexes),
and inserts the 50,000 records using SQLAlchemy.
"""

import os
import sys
from dotenv import load_dotenv
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Load environment variables from .env file if it exists
load_dotenv()

# Database Connection Settings
# Users can modify these in their environment or .env file
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")
DB_NAME = os.getenv("DB_NAME", "pharma_sales_db")
CSV_PATH = "pharma_sales_data.csv"
SCHEMA_PATH = "schema.sql"

def get_connection_url(database=None):
    """Generates the SQLAlchemy URL connection string."""
    query_params = {}
    if DB_HOST and DB_HOST != "localhost" and DB_HOST != "127.0.0.1":
        query_params["sslmode"] = "require"
        
    return URL.create(
        drivername="postgresql+psycopg2",
        username=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        database=database,
        query=query_params
    )

def create_database_if_not_exists():
    """
    Connects to the default 'postgres' database and creates the target database
    if it does not already exist.
    """
    print(f"Connecting to PostgreSQL server at {DB_HOST}:{DB_PORT} as user '{DB_USER}'...")
    try:
        # Connect to default system DB 'postgres' to check/create target DB
        engine = create_engine(get_connection_url(database="postgres"), isolation_level="AUTOCOMMIT")
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{DB_NAME}'"))
            exists = result.scalar()
            
            if not exists:
                print(f"Database '{DB_NAME}' not found. Creating database...")
                conn.execute(text(f"CREATE DATABASE {DB_NAME}"))
                print(f"Database '{DB_NAME}' created successfully.")
            else:
                print(f"Database '{DB_NAME}' already exists.")
        engine.dispose()
    except Exception as e:
        print(f"\n[ERROR] Failed to connect to PostgreSQL or create database.")
        print(f"Details: {e}")
        print("\nPlease ensure:")
        print("1. PostgreSQL is installed and running.")
        print("2. Your username and password are correct.")
        print("3. You have set up environment variables or a .env file if using non-default credentials.")
        sys.exit(1)

def execute_schema_script(engine):
    """Reads schema.sql and runs it against the target database."""
    if not os.path.exists(SCHEMA_PATH):
        print(f"[ERROR] Schema file '{SCHEMA_PATH}' not found in the current directory.")
        sys.exit(1)
        
    print(f"Reading schema script '{SCHEMA_PATH}'...")
    with open(SCHEMA_PATH, "r") as f:
        schema_sql = f.read()
        
    print("Creating database schema and indexes...")
    try:
        with engine.connect() as conn:
            # PostgreSQL requires auto-commit off (default in connection transaction) to run multiple DDL blocks
            # We split the SQL commands by semicolon, but clean up query comments/empty lines first
            statements = schema_sql.split(";")
            with conn.begin():  # Run within a transaction
                for statement in statements:
                    statement_stripped = statement.strip()
                    if statement_stripped:
                        conn.execute(text(statement_stripped))
        print("Database schema and indexes created successfully.")
    except Exception as e:
        print(f"[ERROR] Failed to apply database schema. Details: {e}")
        sys.exit(1)

def load_data_to_db(engine):
    """Reads the CSV file and loads it into the database using psycopg2 COPY."""
    if not os.path.exists(CSV_PATH):
        print(f"[ERROR] Dataset file '{CSV_PATH}' not found. Please run 'data_generator.py' first.")
        sys.exit(1)
        
    print(f"Opening synthetic dataset '{CSV_PATH}'...")
    
    # We will get total line count to know the record size
    with open(CSV_PATH, "r") as f:
        record_count = sum(1 for line in f) - 1 # Subtract 1 for header row
        
    print(f"Prepared {record_count:,} records from CSV. Connecting via psycopg2...")
    
    try:
        print("Loading data into PostgreSQL via COPY (extremely fast)...")
        
        # Build connection arguments
        conn_args = {
            "host": DB_HOST,
            "port": DB_PORT,
            "user": DB_USER,
            "password": DB_PASSWORD,
            "database": DB_NAME
        }
        # If remote database, require SSL
        if DB_HOST and DB_HOST != "localhost" and DB_HOST != "127.0.0.1":
            conn_args["sslmode"] = "require"
            
        conn = psycopg2.connect(**conn_args)
        cursor = conn.cursor()
        
        # Execute PostgreSQL COPY command
        with open(CSV_PATH, "r") as f:
            cursor.copy_expert("COPY pharma_sales FROM STDIN WITH CSV HEADER", f)
            
        conn.commit()
        cursor.close()
        conn.close()
        print("Data load complete!")
        
        # Verify row count in target DB using SQLAlchemy engine
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) FROM pharma_sales"))
            db_count = result.scalar()
            print(f"Verification: Found {db_count:,} records inside the 'pharma_sales' table.")
            
            if db_count == record_count:
                print("SUCCESS: Row count matches perfectly!")
            else:
                print(f"WARNING: Row count mismatch. CSV has {record_count:,}, DB has {db_count:,}.")
                
    except Exception as e:
        print(f"[ERROR] Failed to write data to database. Details: {e}")
        sys.exit(1)

def main():
    print("=" * 60)
    print("PHARMA SALES DATABASE INITIALIZATION & LOADER")
    print("=" * 60)
    
    # Step 1: Create target database if it doesn't exist
    create_database_if_not_exists()
    
    # Step 2: Establish connection to target database
    target_engine = create_engine(get_connection_url(database=DB_NAME))
    
    # Step 3: Run schema.sql DDL script
    execute_schema_script(target_engine)
    
    # Step 4: Load generated CSV data into PostgreSQL
    load_data_to_db(target_engine)
    
    # Clean up
    target_engine.dispose()
    print("=" * 60)
    print("Database setup complete! You can now run the Streamlit dashboard.")
    print("=" * 60)

if __name__ == "__main__":
    main()
