import sqlite3
import os

# Set environment variables for local development
os.environ["INPUT_DIR"] = os.path.join(os.getcwd(), "input")
os.environ["OUTPUT_DIR"] = os.path.join(os.getcwd(), "output")

# Now import settings after environment variables are set
from refiner.config import settings

# Connect to the database
db_path = os.path.join(settings.OUTPUT_DIR, 'db.libsql')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# List all tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in the database:")
for table in tables:
    print(f"- {table[0]}")

# For each table, show its structure and some data
for table in tables:
    table_name = table[0]
    print(f"\nTable structure {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for column in columns:
        print(f"  {column[1]} ({column[2]})")

    print(f"\nSample data from {table_name}:")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")

conn.close()