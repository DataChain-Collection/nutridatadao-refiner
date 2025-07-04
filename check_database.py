import sqlite3
import os

# Set environment variables for local development
os.environ["INPUT_DIR"] = os.path.join(os.getcwd(), "input")
os.environ["OUTPUT_DIR"] = os.path.join(os.getcwd(), "output")

# Now import settings after environment variables are set
from refiner.config import settings

# Conectar a la base de datos
db_path = os.path.join(settings.OUTPUT_DIR, 'db.libsql')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Listar todas las tablas
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tablas en la base de datos:")
for table in tables:
    print(f"- {table[0]}")

# Para cada tabla, mostrar su estructura y algunos datos
for table in tables:
    table_name = table[0]
    print(f"\nEstructura de la tabla {table_name}:")
    cursor.execute(f"PRAGMA table_info({table_name});")
    columns = cursor.fetchall()
    for column in columns:
        print(f"  {column[1]} ({column[2]})")

    print(f"\nDatos de muestra de {table_name}:")
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 5;")
    rows = cursor.fetchall()
    for row in rows:
        print(f"  {row}")

conn.close()